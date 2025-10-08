import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

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
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = setup_logging("workflow-svc")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("workflow-svc startup complete")
    try:
        yield
    finally:
        try:
            client._client.close()  # type: ignore[attr-defined]
        except Exception:
            pass
        logger.info("workflow-svc shutdown complete")


app = FastAPI(title="PropVerify Workflow Service", version="0.1.0", lifespan=lifespan)
setup_tracing("workflow-svc", app)

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
            "name": "PropVerify Workflow Service",
            "version": app.version,
            "message": "Integrates with CORTX Workflow/Compliance. No business logic here.",
        }
    )


@app.get("/workflow-status", tags=["integration"])
async def workflow_status(
    request: Request,
    _claims: Optional[dict] = Depends(auth_dependency),
) -> JSONResponse:
    """Sample call to CORTX Workflow service via Gateway."""
    try:
        corr_id = request.state.correlation_id
        traceparent = request.headers.get("traceparent")

        # TODO: Replace with actual workflow endpoint path
        resp = client.get_json(
            "/workflow/status",
            correlation_id=corr_id,
            traceparent=traceparent,
        )

        return JSONResponse({"workflow": resp})
    except Exception as e:
        logger.error(f"Workflow service call failed: {e}")
        return JSONResponse({"error": "Workflow service unreachable"}, status_code=503)


class WorkflowExecutionRequest(BaseModel):
    """Request model for workflow execution."""

    workflow_pack_id: str = Field(..., description="Workflow Pack ID from Packs Registry")
    workflow_type: str = Field(
        ..., description="Type of workflow (e.g., legal, financial, operational)"
    )
    payload: dict = Field(..., description="Workflow-specific payload data")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class WorkflowExecutionResponse(BaseModel):
    """Response model for workflow execution."""

    status: str = Field(..., description="Status: executed, pending_approval, failed")
    workflow_id: str = Field(..., description="Unique workflow execution ID")
    approval_task_id: Optional[str] = Field(
        default=None, description="HIL approval task ID if required"
    )
    requires_human_approval: bool = Field(..., description="Whether HIL approval is required")
    correlation_id: str = Field(..., description="Correlation ID for tracing")
    message: Optional[str] = Field(default=None, description="Status message")


# In-memory store for approval tasks (production would use persistent storage)
approval_tasks: dict = {}


def requires_hil_approval(workflow_type: str, payload: dict) -> bool:
    """Determine if workflow requires Human-in-the-Loop approval.

    Per GOVERNANCE.md and CLAUDE.md:
    - Any action affecting title/legal/financial data requires HIL approval
    """
    # Check workflow type
    if workflow_type.lower() in ["legal", "financial", "title", "ownership", "lien"]:
        return True

    # Check payload for sensitive data indicators
    sensitive_keys = {
        "legal_description",
        "ownership_chain",
        "lien_data",
        "judgment",
        "title_commitment",
        "deed",
        "mortgage",
        "encumbrance",
    }
    payload_keys = set(str(k).lower() for k in payload.keys())

    if payload_keys.intersection(sensitive_keys):
        return True

    # Check for financial amounts above threshold
    for key, value in payload.items():
        if "amount" in str(key).lower() and isinstance(value, (int, float)):
            if value > 10000:  # Configurable threshold
                return True

    return False


@app.post("/execute-workflow", tags=["workflow"], response_model=WorkflowExecutionResponse)
async def execute_workflow(
    request: Request,
    workflow_req: WorkflowExecutionRequest,
    _claims: Optional[dict] = Depends(auth_dependency),
) -> JSONResponse:
    """Execute a workflow with HIL (Human-in-the-Loop) approval when required.

    Integrates with CORTX Workflow service via Gateway.
    Legal/financial workflows require approval before execution.
    """
    corr_id = request.state.correlation_id
    traceparent = request.headers.get("traceparent")
    user_id = get_user_id_from_request(request)
    workflow_id = str(uuid.uuid4())

    # Hash input for audit
    input_hash = sha256_hex(json.dumps(workflow_req.model_dump(), sort_keys=True))

    # Redact any PII from payload before processing
    redacted_payload = json.loads(
        redact_text(json.dumps(workflow_req.payload), client=client, correlation_id=corr_id)
    )

    try:
        # Check if HIL approval is required
        needs_hil = requires_hil_approval(workflow_req.workflow_type, workflow_req.payload)

        if needs_hil:
            # Create approval task via CORTX Workflow service
            approval_task_id = str(uuid.uuid4())

            approval_request = {
                "task_type": "hil_approval",
                "workflow_id": workflow_id,
                "workflow_pack_id": workflow_req.workflow_pack_id,
                "workflow_type": workflow_req.workflow_type,
                "requester": user_id,
                "created_at": int(time.time()),
                "payload_hash": sha256_hex(redacted_payload),
                "metadata": workflow_req.metadata or {},
            }

            # Call CORTX Workflow service to create approval task
            try:
                task_response = client.post_json(
                    "/workflow/tasks/create",
                    correlation_id=corr_id,
                    traceparent=traceparent,
                    json=approval_request,
                )
                approval_task_id = task_response.get("task_id", approval_task_id)
            except Exception as e:
                logger.warning(
                    f"Failed to create approval task via Gateway: {e}. Using local task."
                )

            # Store approval task for later processing
            approval_tasks[approval_task_id] = {
                "workflow_id": workflow_id,
                "workflow_request": workflow_req.model_dump(),
                "status": "pending_approval",
                "created_at": time.time(),
                "correlation_id": corr_id,
            }

            result = WorkflowExecutionResponse(
                status="pending_approval",
                workflow_id=workflow_id,
                approval_task_id=approval_task_id,
                requires_human_approval=True,
                correlation_id=corr_id,
                message="Workflow requires human approval before execution",
            )
        else:
            # Execute workflow immediately via CORTX Workflow service
            workflow_payload = {
                "workflow_pack_id": workflow_req.workflow_pack_id,
                "workflow_type": workflow_req.workflow_type,
                "payload": redacted_payload,
                "metadata": workflow_req.metadata or {},
                "workflow_id": workflow_id,
            }

            try:
                _ = client.post_json(
                    "/workflow/execute",
                    correlation_id=corr_id,
                    traceparent=traceparent,
                    json=workflow_payload,
                )

                result = WorkflowExecutionResponse(
                    status="executed",
                    workflow_id=workflow_id,
                    approval_task_id=None,
                    requires_human_approval=False,
                    correlation_id=corr_id,
                    message="Workflow executed successfully",
                )
            except Exception as e:
                logger.error(f"Workflow execution failed: {e}")
                result = WorkflowExecutionResponse(
                    status="failed",
                    workflow_id=workflow_id,
                    approval_task_id=None,
                    requires_human_approval=False,
                    correlation_id=corr_id,
                    message=f"Workflow execution failed: {str(e)}",
                )

        # Log to audit system
        output_hash = sha256_hex(json.dumps(result.model_dump(), sort_keys=True))

        # Determine event type from status
        if result.status == "pending_approval":
            event_type = EventType.APPROVAL_REQUIRED
        elif result.status == "executed":
            event_type = EventType.WORKFLOW_START
        else:
            event_type = EventType.WORKFLOW_FAIL

        event = ComplianceEvent(
            event_type=event_type,
            compliance_level=ComplianceLevel.HIGH,
            action=f"workflow_execution_{result.status}",
            resource=f"workflow_pack:{workflow_req.workflow_pack_id}",
            user_id=user_id,
            correlation_id=corr_id,
            details={
                "workflow_id": workflow_id,
                "input_hash": input_hash,
                "output_hash": output_hash,
                "requires_hil": needs_hil,
            },
        )
        cortex_client.log_compliance_event(event)

        return JSONResponse(result.model_dump())

    except Exception as e:
        logger.error(f"Workflow processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal workflow processing error")


@app.post("/workflow/approve/{approval_task_id}", tags=["workflow"])
async def approve_workflow(
    request: Request,
    approval_task_id: str,
    approval_data: dict,
    _claims: dict = Depends(write_role_dependency),
) -> JSONResponse:
    """Approve a pending workflow and continue execution.

    This endpoint handles HIL approval and resumes workflow execution.
    Must be idempotent - multiple approvals of same task should be safe.
    """
    corr_id = request.state.correlation_id
    traceparent = request.headers.get("traceparent")
    user_id = get_user_id_from_request(request)

    # Check if approval task exists
    if approval_task_id not in approval_tasks:
        # Try to fetch from CORTX Workflow service
        try:
            task_status = client.get_json(
                f"/workflow/tasks/{approval_task_id}",
                correlation_id=corr_id,
                traceparent=traceparent,
            )
            if task_status.get("status") == "approved":
                return JSONResponse(
                    {
                        "status": "already_approved",
                        "message": "Task was already approved",
                        "correlation_id": corr_id,
                    }
                )
        except Exception:
            pass

        raise HTTPException(status_code=404, detail="Approval task not found")

    task = approval_tasks[approval_task_id]

    # Check if already approved (idempotency)
    if task["status"] == "approved":
        return JSONResponse(
            {
                "status": "already_approved",
                "workflow_id": task["workflow_id"],
                "message": "Task was already approved",
                "correlation_id": corr_id,
            }
        )

    # Hash approval for audit
    input_hash = sha256_hex({"approval_task_id": approval_task_id, "approval_data": approval_data})

    try:
        # Update approval status
        task["status"] = "approved"
        task["approved_by"] = user_id
        task["approved_at"] = time.time()
        task["approval_data"] = approval_data

        # Notify CORTX Workflow service of approval
        try:
            client.post_json(
                f"/workflow/tasks/{approval_task_id}/approve",
                correlation_id=corr_id,
                traceparent=traceparent,
                json={"approved_by": user_id, "approval_data": approval_data},
            )
        except Exception as e:
            logger.warning(f"Failed to notify Gateway of approval: {e}")

        # Execute the workflow now that it's approved
        workflow_req = task["workflow_request"]
        workflow_payload = {
            "workflow_pack_id": workflow_req["workflow_pack_id"],
            "workflow_type": workflow_req["workflow_type"],
            "payload": workflow_req["payload"],
            "metadata": workflow_req.get("metadata", {}),
            "workflow_id": task["workflow_id"],
            "approval_task_id": approval_task_id,
        }

        # Execute via CORTX Workflow service
        exec_response = client.post_json(
            "/workflow/execute",
            correlation_id=task["correlation_id"],  # Use original correlation ID
            traceparent=traceparent,
            json=workflow_payload,
        )

        result = {
            "status": "approved_and_executed",
            "workflow_id": task["workflow_id"],
            "execution_status": exec_response.get("status", "executed"),
            "message": "Workflow approved and executed",
            "correlation_id": corr_id,
        }

    except Exception as e:
        logger.error(f"Failed to execute approved workflow: {e}")
        result = {
            "status": "approved_but_failed",
            "workflow_id": task["workflow_id"],
            "error": str(e),
            "message": "Workflow approved but execution failed",
            "correlation_id": corr_id,
        }

    # Log approval to audit system
    output_hash = sha256_hex(json.dumps(result, sort_keys=True))
    event = ComplianceEvent(
        event_type=EventType.APPROVAL_GRANTED,
        compliance_level=ComplianceLevel.CRITICAL,
        action="workflow_approval",
        resource=f"workflow:{task['workflow_id']}",
        user_id=user_id,
        correlation_id=corr_id,
        details={
            "approval_task_id": approval_task_id,
            "approved_by": user_id,
            "input_hash": input_hash,
            "output_hash": output_hash,
            "execution_status": result.get("execution_status"),
        },
    )
    cortex_client.log_compliance_event(event)

    return JSONResponse(result)


@app.get("/workflow/status/{workflow_id}", tags=["workflow"])
async def get_workflow_status(
    request: Request,
    workflow_id: str,
    _claims: Optional[dict] = Depends(auth_dependency),
) -> JSONResponse:
    """Get the status of a workflow execution."""
    corr_id = request.state.correlation_id
    traceparent = request.headers.get("traceparent")

    try:
        # Query CORTX Workflow service for status
        status_response = client.get_json(
            f"/workflow/status/{workflow_id}", correlation_id=corr_id, traceparent=traceparent
        )

        return JSONResponse(status_response)

    except Exception as e:
        # Check local approval tasks as fallback
        for task_id, task in approval_tasks.items():
            if task.get("workflow_id") == workflow_id:
                return JSONResponse(
                    {
                        "workflow_id": workflow_id,
                        "status": task.get("status", "unknown"),
                        "approval_task_id": (
                            task_id if task["status"] == "pending_approval" else None
                        ),
                        "correlation_id": corr_id,
                    }
                )

        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(status_code=404, detail="Workflow not found")


class DesignerCompileRequest(BaseModel):
    """Request model for Designer BPMN/JSON compilation."""

    designer_output: dict = Field(..., description="BPMN/JSON from Designer service")
    output_format: str = Field(default="json", description="Output format: json or bpmn")
    validate_schema: bool = Field(default=True, description="Whether to validate schema")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class DesignerCompileResponse(BaseModel):
    """Response model for Designer compilation."""

    status: str = Field(..., description="Status: compiled, failed, validation_error")
    pack_id: Optional[str] = Field(default=None, description="Compiled Pack ID if successful")
    orchestrator_job_id: Optional[str] = Field(
        default=None, description="Orchestrator job ID if submitted"
    )
    validation_errors: list = Field(default_factory=list, description="Validation errors if any")
    correlation_id: str = Field(..., description="Correlation ID for tracing")
    message: Optional[str] = Field(default=None, description="Status message")


@app.post("/designer/compile", tags=["designer"], response_model=DesignerCompileResponse)
async def compile_designer_output(
    request: Request,
    compile_req: DesignerCompileRequest,
    _claims: Optional[dict] = Depends(auth_dependency),
) -> JSONResponse:
    """Compile Designer BPMN/JSON and emit Orchestrator job.

    Accepts Designer output, validates schema, calls CORTX Pack Compiler via Gateway,
    and on success emits a job request to Orchestrator. All operations are logged to audit.
    """
    corr_id = request.state.correlation_id
    traceparent = request.headers.get("traceparent")
    user_id = get_user_id_from_request(request)

    # Hash input for audit
    input_hash = sha256_hex(json.dumps(compile_req.model_dump(), sort_keys=True))

    try:
        # Step 1: Validate schema if requested
        validation_errors = []
        if compile_req.validate_schema:
            try:
                # Call CORTX Schemas service to validate
                schema_response = client.post_json(
                    "/schemas/validate",
                    correlation_id=corr_id,
                    traceparent=traceparent,
                    json={"data": compile_req.designer_output, "schema_type": "workflow_pack"},
                )
                if not schema_response.get("valid", False):
                    validation_errors = schema_response.get("errors", ["Schema validation failed"])
            except Exception as e:
                logger.warning(f"Schema validation service unavailable: {e}")
                # Continue without schema validation if service is down

        if validation_errors:
            result = DesignerCompileResponse(
                status="validation_error",
                pack_id=None,
                orchestrator_job_id=None,
                validation_errors=validation_errors,
                correlation_id=corr_id,
                message="Schema validation failed",
            )
        else:
            # Step 2: Call CORTX Pack Compiler via Gateway
            compile_response = client.post_json(
                "/packs/compile",
                correlation_id=corr_id,
                traceparent=traceparent,
                json={
                    "source": compile_req.designer_output,
                    "format": compile_req.output_format,
                    "metadata": compile_req.metadata or {},
                },
            )

            pack_id = compile_response.get("pack_id")
            if not pack_id:
                raise ValueError("Pack Compiler did not return pack_id")

            # Step 3: Emit job to Orchestrator
            orchestrator_job = {
                "job_type": "workflow_pack_execution",
                "pack_id": pack_id,
                "source": "designer_compilation",
                "requester": user_id,
                "created_at": int(time.time()),
                "metadata": compile_req.metadata or {},
                "correlation_id": corr_id,
            }

            try:
                job_response = client.post_json(
                    "/orchestrator/jobs/submit",
                    correlation_id=corr_id,
                    traceparent=traceparent,
                    json=orchestrator_job,
                )
                orchestrator_job_id = job_response.get("job_id")
            except Exception as e:
                logger.warning(f"Failed to submit to Orchestrator: {e}")
                orchestrator_job_id = None

            result = DesignerCompileResponse(
                status="compiled",
                pack_id=pack_id,
                orchestrator_job_id=orchestrator_job_id,
                validation_errors=[],
                correlation_id=corr_id,
                message=(
                    "Successfully compiled and submitted to Orchestrator"
                    if orchestrator_job_id
                    else "Compiled but Orchestrator submission failed"
                ),
            )

        # Log to audit system
        output_hash = sha256_hex(json.dumps(result.model_dump(), sort_keys=True))
        event = ComplianceEvent(
            event_type=EventType.WORKFLOW_STEP,
            compliance_level=ComplianceLevel.MEDIUM,
            action="designer_compile_success",
            resource=f"pack:{result.pack_id}" if result.pack_id else "pack:unknown",
            user_id=user_id,
            correlation_id=corr_id,
            details={
                "input_hash": input_hash,
                "output_hash": output_hash,
                "orchestrator_job_id": result.orchestrator_job_id,
                "validation_errors": result.validation_errors,
            },
        )
        cortex_client.log_compliance_event(event)

        return JSONResponse(result.model_dump())

    except Exception as e:
        logger.error(f"Designer compilation error: {e}")
        result = DesignerCompileResponse(
            status="failed",
            pack_id=None,
            orchestrator_job_id=None,
            validation_errors=[str(e)],
            correlation_id=corr_id,
            message=f"Compilation failed: {str(e)}",
        )

        # Log failure to audit
        output_hash = sha256_hex(json.dumps(result.model_dump(), sort_keys=True))
        event = ComplianceEvent(
            event_type=EventType.WORKFLOW_FAIL,
            compliance_level=ComplianceLevel.HIGH,
            action="designer_compile_failed",
            resource="designer_pack",
            user_id=user_id,
            correlation_id=corr_id,
            details={"error": str(e), "input_hash": input_hash, "output_hash": output_hash},
        )
        cortex_client.log_compliance_event(event)

        return JSONResponse(result.model_dump(), status_code=500)
