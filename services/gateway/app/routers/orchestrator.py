"""
Orchestrator API Router

Main API endpoints that use the policy router to handle validation requests.
"""

import uuid
from datetime import datetime
from typing import Any

from app.policy_router import PolicyRouter
from cortx_core.auditing import emit_audit
from cortx_core.logging import logger
from cortx_core.models import AuditEvent
from cortx_rulepack_sdk.contracts import (
    ExplanationRequest,
    ExplanationResponse,
    ValidationMode,
    ValidationOptions,
    ValidationRequest,
    ValidationResponse,
)
from fastapi import APIRouter, Depends, Header, HTTPException

router = APIRouter()

# This will be injected by the main app
policy_router: PolicyRouter = None


def get_policy_router() -> PolicyRouter:
    """Dependency to get policy router instance"""
    if policy_router is None:
        raise HTTPException(status_code=503, detail="Policy router not initialized")
    return policy_router


@router.post("/jobs/validate")
async def create_validation_job(  # noqa: PLR0913
    domain: str,
    mode: ValidationMode = ValidationMode.STATIC,
    input_ref: str = None,
    input_data: dict[str, Any] = None,
    options: dict[str, Any] = None,
    x_tenant_id: str = Header(default="default"),
    x_request_id: str = Header(default_factory=lambda: str(uuid.uuid4())),
    router: PolicyRouter = Depends(get_policy_router),  # noqa: B008
) -> ValidationResponse:
    """
    Create and execute validation job.

    This is the main entry point for validation requests from suite applications.
    """
    if not input_ref and not input_data:
        raise HTTPException(
            status_code=400, detail="Either input_ref or input_data must be provided"
        )

    # Create validation options
    validation_options = ValidationOptions(mode=mode)
    if options:
        # Update options from request
        for key, value in options.items():
            if hasattr(validation_options, key):
                setattr(validation_options, key, value)

    validation_options.tenant_id = x_tenant_id

    # Create validation request
    request = ValidationRequest(
        domain=domain,
        input_type="reference" if input_ref else "records",
        input_data=input_data,
        input_ref=input_ref,
        options=validation_options,
        request_id=x_request_id,
        submitted_at=datetime.utcnow(),
    )

    logger.info(
        f"Starting validation job for domain '{domain}' "
        f"with mode '{mode}' and request_id '{x_request_id}'"
    )

    try:
        # Route through policy router
        response = await router.route_validation(request)

        # Emit audit event
        await emit_audit(
            AuditEvent(
                tenant_id=x_tenant_id,
                action="validate",
                resource="validation_job",
                request_id=x_request_id,
                details={
                    "domain": domain,
                    "mode_requested": mode.value,
                    "mode_executed": (
                        response.mode_executed.value
                        if hasattr(response.mode_executed, "value")
                        else response.mode_executed
                    ),
                    "total_failures": response.summary.total_failures,
                    "success": response.success,
                },
            )
        )

        logger.info(
            f"Validation job completed for request_id '{x_request_id}' "
            f"with {response.summary.total_failures} failures"
        )

        return response

    except Exception as e:
        logger.error(f"Validation job failed for request_id '{x_request_id}': {str(e)}")

        # Emit failure audit
        await emit_audit(
            AuditEvent(
                tenant_id=x_tenant_id,
                action="validate_failed",
                resource="validation_job",
                request_id=x_request_id,
                details={"error": str(e), "domain": domain},
            )
        )

        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}") from e


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str, x_tenant_id: str = Header(default="default")
) -> dict[str, Any]:
    """
    Get validation job status and results.

    For now, returns basic info. In production, this would check
    a job store for async job status.
    """
    # This is a placeholder - in production you'd look up the job
    # from a database or job queue
    return {
        "job_id": job_id,
        "status": "completed",
        "message": "Job status lookup not implemented - use synchronous validation for now",
        "tenant_id": x_tenant_id,
    }


@router.post("/explain")
async def explain_failure(  # noqa: PLR0913
    domain: str,
    failure_id: str,
    failure_data: dict[str, Any],
    include_policy_refs: bool = True,
    include_remediation: bool = True,
    x_tenant_id: str = Header(default="default"),
    x_request_id: str = Header(default_factory=lambda: str(uuid.uuid4())),
    router: PolicyRouter = Depends(get_policy_router),  # noqa: B008
) -> ExplanationResponse:
    """
    Get explanation for a validation failure.
    """
    try:
        # Convert failure_data to ValidationFailure object
        from cortx_rulepack_sdk.contracts import ValidationFailure

        failure = ValidationFailure.model_validate(failure_data)

        # Create explanation request
        request = ExplanationRequest(
            failure=failure,
            include_policy_refs=include_policy_refs,
            include_remediation=include_remediation,
        )

        logger.info(
            f"Generating explanation for failure_id '{failure_id}' " f"in domain '{domain}'"
        )

        # Route to appropriate RulePack
        response = await router.route_explanation(request, domain)

        # Emit audit event
        await emit_audit(
            AuditEvent(
                tenant_id=x_tenant_id,
                action="explain",
                resource="failure_explanation",
                request_id=x_request_id,
                details={
                    "domain": domain,
                    "failure_id": failure_id,
                    "rule_id": failure.rule_id,
                    "confidence": response.confidence,
                },
            )
        )

        return response

    except Exception as e:
        logger.error(f"Explanation failed for failure_id '{failure_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}") from e


@router.put("/failures/{failure_id}/decision")
async def update_failure_decision(  # noqa: PLR0913
    failure_id: str,
    decision: str,
    reason: str = None,
    notes: str = None,
    x_tenant_id: str = Header(default="default"),
    x_request_id: str = Header(default_factory=lambda: str(uuid.uuid4())),
) -> dict[str, Any]:
    """
    Update user decision on a validation failure.

    This endpoint allows users to accept, defer, ignore, or override failures.
    """
    valid_decisions = ["accept", "defer", "ignore", "override"]
    if decision not in valid_decisions:
        raise HTTPException(
            status_code=400, detail=f"Invalid decision. Must be one of: {valid_decisions}"
        )

    # In production, this would update a database
    decision_record = {
        "failure_id": failure_id,
        "decision": decision,
        "reason": reason,
        "notes": notes,
        "decided_by": x_tenant_id,  # In production, use actual user ID
        "decided_at": datetime.utcnow().isoformat(),
        "request_id": x_request_id,
    }

    logger.info(f"User decision recorded for failure_id '{failure_id}': {decision}")

    # Emit audit event
    await emit_audit(
        AuditEvent(
            tenant_id=x_tenant_id,
            action="failure_decision",
            resource="validation_failure",
            request_id=x_request_id,
            details=decision_record,
        )
    )

    return {
        "message": "Decision recorded successfully",
        "failure_id": failure_id,
        "decision": decision,
    }


@router.post("/feedback/rag/{interaction_id}")
async def submit_rag_feedback(
    interaction_id: str,
    feedback: str,
    details: str = None,
    x_tenant_id: str = Header(default="default"),
    x_request_id: str = Header(default_factory=lambda: str(uuid.uuid4())),
) -> dict[str, Any]:
    """
    Submit feedback on RAG/AI explanations.
    """
    valid_feedback = ["helpful", "not_helpful", "partially_helpful", "irrelevant"]
    if feedback not in valid_feedback:
        raise HTTPException(
            status_code=400, detail=f"Invalid feedback. Must be one of: {valid_feedback}"
        )

    # In production, this would store feedback for model improvement
    feedback_record = {
        "interaction_id": interaction_id,
        "feedback": feedback,
        "details": details,
        "submitted_by": x_tenant_id,
        "submitted_at": datetime.utcnow().isoformat(),
        "request_id": x_request_id,
    }

    logger.info(f"RAG feedback received for interaction '{interaction_id}': {feedback}")

    # Emit audit event
    await emit_audit(
        AuditEvent(
            tenant_id=x_tenant_id,
            action="rag_feedback",
            resource="rag_interaction",
            request_id=x_request_id,
            details=feedback_record,
        )
    )

    return {
        "message": "Feedback recorded successfully",
        "interaction_id": interaction_id,
        "feedback": feedback,
    }


@router.get("/health")
async def health_check(
    router: PolicyRouter = Depends(get_policy_router),
) -> dict[str, Any]:  # noqa: B008
    """
    Health check for orchestrator and connected RulePacks.
    """
    try:
        policy_health = await router.health_check()

        return {
            "status": "healthy",
            "orchestrator": "running",
            "policy_router": policy_health,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
