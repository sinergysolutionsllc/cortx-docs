import json
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from cortx_backend.common.audit import sha256_hex
from cortx_backend.common.auth import (
    decode_token_optional,
    get_user_id_from_request,
    require_auth,
    require_roles,
)
from cortx_backend.common.config import CORTXConfig
from cortx_backend.common.cortex_client import CortexClient
from cortx_backend.common.http_client import CORTXClient
from cortx_backend.common.logging import setup_logging
from cortx_backend.common.metrics import instrument_metrics
from cortx_backend.common.middleware import add_common_middleware
from cortx_backend.common.models import ComplianceEvent, ComplianceLevel, EventType
from cortx_backend.common.redaction import redact_text
from cortx_backend.common.tokens import EnvTokenProvider
from cortx_backend.common.tracing import setup_tracing
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = setup_logging("validation-svc")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("validation-svc startup complete")
    try:
        yield
    finally:
        try:
            client._client.close()  # type: ignore[attr-defined]
        except Exception:
            pass
        logger.info("validation-svc shutdown complete")


app = FastAPI(title="PropVerify Validation Service", version="0.1.0", lifespan=lifespan)
setup_tracing("validation-svc", app)

# Initialize CORTX infrastructure singletons
cfg = CORTXConfig.from_env()
client = CORTXClient(cfg, EnvTokenProvider())
cortex_client = CortexClient(cfg.compliance_url)

# Apply common middleware and metrics
add_common_middleware(app)
instrument_metrics(app)


def auth_dependency(request: Request) -> Optional[dict]:
    if os.getenv("REQUIRE_AUTH", "false").lower() in {"1", "true", "yes"}:
        return require_auth(request)
    else:
        return decode_token_optional(request)


def write_role_dependency(request: Request) -> dict:
    if os.getenv("REQUIRE_AUTH", "false").lower() in {"1", "true", "yes"}:
        return require_roles("propverify:write")(request)
    else:
        return decode_token_optional(request) or {}


def admin_role_dependency(request: Request) -> dict:
    if os.getenv("REQUIRE_AUTH", "false").lower() in {"1", "true", "yes"}:
        return require_roles("propverify:admin")(request)
    else:
        return decode_token_optional(request) or {}


@app.get("/healthz", tags=["health"])  # liveness
async def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/readyz", tags=["health"])  # readiness
async def readyz() -> JSONResponse:
    return JSONResponse({"status": "ready"})


@app.get("/livez", tags=["health"])  # alias
async def livez() -> JSONResponse:
    return JSONResponse({"status": "alive"})


@app.get("/", tags=["meta"])  # minimal index
async def index(_claims: Optional[dict] = Depends(auth_dependency)) -> JSONResponse:
    return JSONResponse(
        {
            "name": "PropVerify Validation Service",
            "version": app.version,
            "message": "Integrates with CORTX Validation/Compliance. No business logic here.",
        }
    )


@app.get("/schemas", tags=["integration"])
async def get_schemas(
    request: Request,
    _claims: Optional[dict] = Depends(auth_dependency),
) -> JSONResponse:
    """Sample call to CORTX Schemas service via Gateway."""
    try:
        corr_id = request.state.correlation_id
        traceparent = request.headers.get("traceparent")

        # TODO: Replace with actual schemas endpoint path
        resp = client.get_json(
            "/schemas",
            correlation_id=corr_id,
            traceparent=traceparent,
        )

        return JSONResponse({"schemas": resp})
    except Exception as e:
        logger.error(f"Schemas service call failed: {e}")
        return JSONResponse({"error": "Schemas service unreachable"}, status_code=503)


class ValidationRequest(BaseModel):
    """Request model for validation."""

    rule_pack_id: str = Field(..., description="RulePack ID from Packs Registry")
    payload: dict = Field(..., description="Data to validate")
    validation_type: Optional[str] = Field(default="standard", description="Type of validation")
    strict_mode: bool = Field(default=True, description="Whether to fail on warnings")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class ValidationResult(BaseModel):
    """Validation result model."""

    valid: bool = Field(..., description="Whether validation passed")
    errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of validation errors"
    )
    warnings: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of validation warnings"
    )
    rule_results: Dict[str, Any] = Field(
        default_factory=dict, description="Individual rule execution results"
    )
    metadata: Optional[dict] = Field(default=None, description="Additional result metadata")


class ValidationResponse(BaseModel):
    """Response model for validation."""

    result: ValidationResult = Field(..., description="Validation result")
    correlation_id: str = Field(..., description="Correlation ID for tracing")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    rule_pack_version: Optional[str] = Field(default=None, description="Version of RulePack used")


def normalize_validation_output(raw_result: dict, redact_pii: bool = True) -> ValidationResult:
    """Normalize and sanitize validation results.

    This function ensures no PII leakage and consistent output format.
    Must have 100% test coverage as a validator function.
    """
    # Extract basic validation status
    valid = raw_result.get("valid", False)

    # Process errors with PII redaction
    errors = []
    for error in raw_result.get("errors", []):
        error_obj = {
            "code": error.get("code", "UNKNOWN"),
            "message": error.get("message", "Validation error"),
            "field": error.get("field"),
            "severity": error.get("severity", "error"),
        }
        if redact_pii and error_obj["message"]:
            error_obj["message"] = redact_text(error_obj["message"])
        errors.append(error_obj)

    # Process warnings
    warnings = []
    for warning in raw_result.get("warnings", []):
        warning_obj = {
            "code": warning.get("code", "UNKNOWN"),
            "message": warning.get("message", "Validation warning"),
            "field": warning.get("field"),
            "severity": "warning",
        }
        if redact_pii and warning_obj["message"]:
            warning_obj["message"] = redact_text(warning_obj["message"])
        warnings.append(warning_obj)

    # Process individual rule results
    rule_results = {}
    for rule_name, rule_result in raw_result.get("rule_results", {}).items():
        rule_results[rule_name] = {
            "passed": rule_result.get("passed", False),
            "message": (
                redact_text(str(rule_result.get("message", "")))
                if redact_pii
                else rule_result.get("message")
            ),
            "metadata": rule_result.get("metadata", {}),
        }

    return ValidationResult(
        valid=valid,
        errors=errors,
        warnings=warnings,
        rule_results=rule_results,
        metadata=raw_result.get("metadata", {}),
    )


def apply_validation_rules(payload: dict, rule_pack: dict, strict_mode: bool = True) -> dict:
    """Apply RulePack validation rules to payload.

    This is a core validator function requiring 100% test coverage.
    """
    results = {"valid": True, "errors": [], "warnings": [], "rule_results": {}}

    # Extract rules from pack
    rules = rule_pack.get("rules", [])

    for rule in rules:
        rule_name = rule.get("name", "unknown_rule")
        rule_type = rule.get("type", "validation")

        try:
            # Apply different rule types
            if rule_type == "required_field":
                field_name = rule.get("field")
                if field_name and field_name not in payload:
                    results["errors"].append(
                        {
                            "code": "MISSING_REQUIRED_FIELD",
                            "message": f"Required field '{field_name}' is missing",
                            "field": field_name,
                            "severity": "error",
                        }
                    )
                    results["valid"] = False
                    results["rule_results"][rule_name] = {
                        "passed": False,
                        "message": "Field missing",
                    }
                else:
                    results["rule_results"][rule_name] = {
                        "passed": True,
                        "message": "Field present",
                    }

            elif rule_type == "format_validation":
                field_name = rule.get("field")
                format_pattern = rule.get("pattern")
                if field_name in payload:
                    import re

                    value = str(payload[field_name])
                    if format_pattern and not re.match(format_pattern, value):
                        severity = "error" if rule.get("required", True) else "warning"
                        msg = {
                            "code": "FORMAT_VALIDATION_FAILED",
                            "message": f"Field '{field_name}' does not match required format",
                            "field": field_name,
                            "severity": severity,
                        }
                        if severity == "error":
                            results["errors"].append(msg)
                            results["valid"] = False
                        else:
                            results["warnings"].append(msg)
                            if strict_mode:
                                results["valid"] = False
                        results["rule_results"][rule_name] = {
                            "passed": False,
                            "message": "Format mismatch",
                        }
                    else:
                        results["rule_results"][rule_name] = {
                            "passed": True,
                            "message": "Format valid",
                        }

            elif rule_type == "range_check":
                field_name = rule.get("field")
                min_val = rule.get("min")
                max_val = rule.get("max")
                if field_name in payload:
                    value = payload[field_name]
                    if isinstance(value, (int, float)):
                        if (min_val is not None and value < min_val) or (
                            max_val is not None and value > max_val
                        ):
                            results["warnings"].append(
                                {
                                    "code": "RANGE_CHECK_FAILED",
                                    "message": f"Field '{field_name}' value {value} is outside range [{min_val}, {max_val}]",
                                    "field": field_name,
                                    "severity": "warning",
                                }
                            )
                            if strict_mode:
                                results["valid"] = False
                            results["rule_results"][rule_name] = {
                                "passed": False,
                                "message": "Out of range",
                            }
                        else:
                            results["rule_results"][rule_name] = {
                                "passed": True,
                                "message": "In range",
                            }

            elif rule_type == "custom":
                # Custom rule execution (would call external validator in production)
                results["rule_results"][rule_name] = {
                    "passed": True,
                    "message": "Custom rule executed",
                    "metadata": {"rule_type": "custom"},
                }

        except Exception as e:
            logger.error(f"Error executing rule {rule_name}: {e}")
            results["errors"].append(
                {
                    "code": "RULE_EXECUTION_ERROR",
                    "message": f"Failed to execute rule '{rule_name}': {str(e)}",
                    "field": None,
                    "severity": "error",
                }
            )
            results["valid"] = False
            results["rule_results"][rule_name] = {
                "passed": False,
                "message": f"Execution error: {str(e)}",
            }

    return results


@app.post("/validate", tags=["validation"], response_model=ValidationResponse)
async def validate_data(
    request: Request,
    validation_req: ValidationRequest,
    _claims: Optional[dict] = Depends(auth_dependency),
) -> JSONResponse:
    """Validate payload using RulePack from CORTX Validation service.

    Accepts a payload and invokes the CORTX Validation service (RulePack execution) via Gateway.
    Returns normalized validation results with no PII leakage.
    This endpoint requires 100% test coverage for all validator functions.
    """
    corr_id = request.state.correlation_id
    traceparent = request.headers.get("traceparent")
    user_id = get_user_id_from_request(request)
    start_time = time.time()

    # Hash input for audit
    input_hash = sha256_hex(validation_req.dict())

    # Redact PII from payload before processing
    redacted_payload = json.loads(
        redact_text(json.dumps(validation_req.payload), client=client, correlation_id=corr_id)
    )

    try:
        # Step 1: Fetch RulePack from CORTX Packs Registry via Gateway
        try:
            rule_pack_response = client.get_json(
                f"/packs/rules/{validation_req.rule_pack_id}",
                correlation_id=corr_id,
                traceparent=traceparent,
            )
            rule_pack = rule_pack_response.get("pack", {})
            rule_pack_version = rule_pack_response.get("version")
        except Exception as e:
            logger.warning(f"Failed to fetch RulePack from Gateway: {e}. Using default rules.")
            # Fallback to basic validation rules for MVP
            rule_pack = {
                "rules": [
                    {"name": "basic_structure", "type": "required_field", "field": "id"},
                    {"name": "data_present", "type": "required_field", "field": "data"},
                ]
            }
            rule_pack_version = "fallback-1.0"

        # Step 2: Call CORTX Validation service via Gateway
        try:
            validation_response = client.post_json(
                "/validation/execute",
                correlation_id=corr_id,
                traceparent=traceparent,
                json={
                    "rule_pack_id": validation_req.rule_pack_id,
                    "payload": redacted_payload,
                    "validation_type": validation_req.validation_type,
                    "strict_mode": validation_req.strict_mode,
                    "metadata": validation_req.metadata or {},
                },
            )
            raw_result = validation_response.get("result", {})
        except Exception as e:
            logger.warning(f"CORTX Validation service unavailable: {e}. Using local validation.")
            # Fallback to local validation
            raw_result = apply_validation_rules(
                redacted_payload, rule_pack, validation_req.strict_mode
            )

        # Step 3: Normalize and sanitize results
        validation_result = normalize_validation_output(raw_result, redact_pii=True)

        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Build response
        response = ValidationResponse(
            result=validation_result,
            correlation_id=corr_id,
            execution_time_ms=execution_time_ms,
            rule_pack_version=rule_pack_version,
        )

        # Log to audit system
        output_hash = sha256_hex(response.dict())
        event = ComplianceEvent(
            event_type=EventType.RULEPACK_EXECUTE,
            compliance_level=ComplianceLevel.HIGH,
            action="rulepack_validation_success",
            resource=f"rulepack:{validation_req.rule_pack_id}",
            user_id=user_id,
            correlation_id=corr_id,
            details={
                "input_hash": input_hash,
                "output_hash": output_hash,
                "valid": validation_result.valid,
                "error_count": len(validation_result.errors),
                "warning_count": len(validation_result.warnings),
            },
        )
        cortex_client.log_compliance_event(event)

        return JSONResponse(response.dict())

    except Exception as e:
        logger.error(f"Validation processing error: {e}")
        # Return error response
        error_result = ValidationResult(
            valid=False,
            errors=[
                {
                    "code": "VALIDATION_SERVICE_ERROR",
                    "message": "Internal validation service error",
                    "field": None,
                    "severity": "error",
                }
            ],
            warnings=[],
            rule_results={},
        )

        response = ValidationResponse(
            result=error_result,
            correlation_id=corr_id,
            execution_time_ms=int((time.time() - start_time) * 1000),
            rule_pack_version=None,
        )

        # Log error to audit
        output_hash = sha256_hex(response.dict())
        event = ComplianceEvent(
            event_type=EventType.SYSTEM_ERROR,
            compliance_level=ComplianceLevel.CRITICAL,
            action="rulepack_validation_exception",
            resource=f"rulepack:{validation_req.rule_pack_id}",
            user_id=user_id,
            correlation_id=corr_id,
            details={"error": str(e), "input_hash": input_hash, "output_hash": output_hash},
        )
        cortex_client.log_compliance_event(event)

        return JSONResponse(response.dict(), status_code=500)
