import os
import time
from contextlib import asynccontextmanager
from typing import List, Optional

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
from cortx_backend.common.tokens import EnvTokenProvider
from cortx_backend.common.tracing import setup_tracing
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = setup_logging("compliance-svc")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("compliance-svc startup complete")
    try:
        yield
    finally:
        try:
            client._client.close()  # type: ignore[attr-defined]
        except Exception:
            pass
        logger.info("compliance-svc shutdown complete")


app = FastAPI(title="PropVerify Compliance Service", version="0.1.0", lifespan=lifespan)
setup_tracing("compliance-svc", app)

# Initialize CORTX infrastructure singletons
cfg = CORTXConfig.from_env()
client = CORTXClient(cfg, EnvTokenProvider())
# Compliance service doesn't need to call itself - use optional cortex_client
cortex_client = None
if cfg.compliance_url:
    try:
        cortex_client = CortexClient(cfg.compliance_url)
    except Exception as e:
        logger.warning(f"Could not initialize CortexClient: {e}. Running in standalone mode.")

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
            "name": "PropVerify Compliance Service",
            "version": app.version,
            "message": "Compliance logging, reporting, and regulatory event tracking",
        }
    )


class ComplianceEventRequest(BaseModel):
    """Request model for logging compliance events."""

    event_type: str = Field(..., description="Type of compliance event")
    description: str = Field(..., description="Event description")
    data: dict = Field(default_factory=dict, description="Event data")
    user_id: Optional[str] = Field(default=None, description="User ID associated with event")
    severity: Optional[str] = Field(default="info", description="Event severity level")


class ComplianceEventResponse(BaseModel):
    """Response model for compliance events."""

    event_id: str = Field(..., description="Unique event ID")
    status: str = Field(..., description="Status of event logging")
    correlation_id: str = Field(..., description="Correlation ID for tracing")


# In-memory store for compliance events (production would use persistent storage)
compliance_events: List[dict] = []


@app.post("/compliance/events", tags=["compliance"], response_model=ComplianceEventResponse)
async def log_compliance_event(
    request: Request,
    event_req: ComplianceEventRequest,
    _claims: Optional[dict] = Depends(auth_dependency),
) -> JSONResponse:
    """Log a compliance event for audit and regulatory tracking.

    All compliance events are logged with cryptographic hashing and
    correlation IDs for audit trail purposes.
    """
    corr_id = request.state.correlation_id
    traceparent = request.headers.get("traceparent")
    user_id = event_req.user_id or get_user_id_from_request(request)

    # Generate event ID
    import uuid

    event_id = str(uuid.uuid4())

    # Hash event data for integrity
    input_hash = sha256_hex(event_req.dict())

    # Map severity to compliance level
    severity_map = {
        "critical": ComplianceLevel.CRITICAL,
        "high": ComplianceLevel.HIGH,
        "medium": ComplianceLevel.MEDIUM,
        "low": ComplianceLevel.LOW,
        "info": ComplianceLevel.LOW,
    }
    compliance_level = severity_map.get(event_req.severity.lower(), ComplianceLevel.MEDIUM)

    # Map event type string to EventType enum
    event_type_map = {
        "audit": EventType.SCHEMA_CHANGE,
        "regulatory": EventType.APPROVAL_REQUIRED,
        "violation": EventType.SYSTEM_ERROR,
        "access": EventType.AUTH_SUCCESS,
        "workflow": EventType.WORKFLOW_START,
        "rulepack": EventType.RULEPACK_EXECUTE,
    }
    event_type = event_type_map.get(event_req.event_type.lower(), EventType.SYSTEM_ERROR)

    try:
        # Create compliance event
        event = ComplianceEvent(
            event_type=event_type,
            compliance_level=compliance_level,
            action=f"compliance_event_{event_req.event_type}",
            resource=f"compliance_event:{event_id}",
            user_id=user_id,
            correlation_id=corr_id,
            details={
                "event_id": event_id,
                "description": event_req.description,
                "data_hash": input_hash,
                "severity": event_req.severity,
                **event_req.data,
            },
        )

        # Log to CORTX Compliance service via CortexClient (if available)
        if cortex_client:
            cortex_client.log_compliance_event(event)

        # Store locally for retrieval (production would use persistent DB)
        event_data = {
            "event_id": event_id,
            "event_type": event_req.event_type,
            "description": event_req.description,
            "data": event_req.data,
            "user_id": user_id,
            "severity": event_req.severity,
            "correlation_id": corr_id,
            "timestamp": int(time.time()),
            "data_hash": input_hash,
        }
        compliance_events.append(event_data)

        response = ComplianceEventResponse(
            event_id=event_id, status="logged", correlation_id=corr_id
        )

        logger.info(f"Compliance event logged: {event_id} type={event_req.event_type}")
        return JSONResponse(response.dict(), status_code=201)

    except Exception as e:
        logger.error(f"Failed to log compliance event: {e}")
        raise HTTPException(status_code=500, detail="Failed to log compliance event")


@app.get("/compliance/events", tags=["compliance"])
async def get_compliance_events(
    request: Request,
    type: Optional[str] = None,
    limit: int = 100,
    _claims: Optional[dict] = Depends(auth_dependency),
) -> JSONResponse:
    """Retrieve compliance events with optional filtering.

    Returns most recent events, optionally filtered by event type.
    """
    corr_id = request.state.correlation_id

    # Filter events by type if specified
    filtered_events = compliance_events
    if type:
        filtered_events = [e for e in compliance_events if e.get("event_type") == type]

    # Sort by timestamp descending and limit
    sorted_events = sorted(filtered_events, key=lambda e: e.get("timestamp", 0), reverse=True)
    limited_events = sorted_events[:limit]

    logger.info(f"Retrieved {len(limited_events)} compliance events (type={type}, limit={limit})")
    return JSONResponse(
        {
            "events": limited_events,
            "count": len(limited_events),
            "total": len(filtered_events),
            "correlation_id": corr_id,
        }
    )


@app.get("/compliance/report", tags=["compliance"])
async def generate_compliance_report(
    request: Request,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    _claims: dict = Depends(admin_role_dependency),
) -> JSONResponse:
    """Generate compliance report for specified time range.

    Requires admin role. Returns aggregated compliance metrics and events.
    """
    corr_id = request.state.correlation_id
    current_time = int(time.time())

    # Default to last 24 hours if not specified
    start_time = start_time or (current_time - 86400)
    end_time = end_time or current_time

    # Filter events by time range
    filtered_events = [
        e for e in compliance_events if start_time <= e.get("timestamp", 0) <= end_time
    ]

    # Aggregate by event type
    event_counts = {}
    severity_counts = {}
    for event in filtered_events:
        event_type = event.get("event_type", "unknown")
        severity = event.get("severity", "unknown")
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    report = {
        "report_generated_at": current_time,
        "time_range": {"start": start_time, "end": end_time},
        "total_events": len(filtered_events),
        "event_type_breakdown": event_counts,
        "severity_breakdown": severity_counts,
        "compliance_status": (
            "compliant" if severity_counts.get("critical", 0) == 0 else "needs_review"
        ),
        "correlation_id": corr_id,
    }

    logger.info(
        f"Generated compliance report: {len(filtered_events)} events from {start_time} to {end_time}"
    )
    return JSONResponse(report)
