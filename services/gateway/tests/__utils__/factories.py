"""
Test data factories for Gateway service tests

Provides factory functions to create test data objects
"""

import uuid
from datetime import datetime
from typing import Any


def create_validation_request_data(
    domain: str = "test.domain",
    mode: str = "static",
    input_data: dict[str, Any] = None,
    input_ref: str = None,
    options: dict[str, Any] = None,
    tenant_id: str = "test_tenant",
    request_id: str = None,
) -> dict[str, Any]:
    """Factory for validation request data"""
    if input_data is None and input_ref is None:
        input_data = {"test_field": "test_value"}

    if request_id is None:
        request_id = f"test-{uuid.uuid4().hex[:8]}"

    return {
        "domain": domain,
        "mode": mode,
        "input_data": input_data,
        "input_ref": input_ref,
        "options": options or {},
        "x-tenant-id": tenant_id,
        "x-request-id": request_id,
    }


def create_validation_failure(
    rule_id: str = "TEST_001",
    severity: str = "error",
    field: str = "test_field",
    message: str = "Test validation failure",
    value: Any = None,
    ai_explanation: str = None,
    ai_recommendation: str = None,
    ai_confidence: float = None,
) -> dict[str, Any]:
    """Factory for validation failure data"""
    failure = {
        "rule_id": rule_id,
        "severity": severity,
        "field": field,
        "message": message,
        "value": value or "invalid_value",
        "policy_references": [],
        "suggested_actions": [],
    }

    if ai_explanation:
        failure["ai_explanation"] = ai_explanation
    if ai_recommendation:
        failure["ai_recommendation"] = ai_recommendation
    if ai_confidence is not None:
        failure["ai_confidence"] = ai_confidence

    return failure


def create_validation_response_data(
    request_id: str = "test-request-123",
    domain: str = "test.domain",
    success: bool = True,
    failures: list[dict[str, Any]] = None,
    mode_executed: str = "static",
    total_records: int = 1,
    processing_time_ms: int = 150,
) -> dict[str, Any]:
    """Factory for validation response data"""
    if failures is None:
        failures = []

    return {
        "request_id": request_id,
        "domain": domain,
        "success": success,
        "summary": {
            "total_records": total_records,
            "records_processed": total_records,
            "total_failures": len(failures),
            "fatal_count": sum(1 for f in failures if f.get("severity") == "fatal"),
            "error_count": sum(1 for f in failures if f.get("severity") == "error"),
            "warning_count": sum(1 for f in failures if f.get("severity") == "warning"),
            "info_count": sum(1 for f in failures if f.get("severity") == "info"),
            "processing_time_ms": processing_time_ms,
            "mode_used": mode_executed,
        },
        "failures": failures,
        "mode_requested": mode_executed,
        "mode_executed": mode_executed,
        "completed_at": datetime.utcnow().isoformat(),
    }


def create_explanation_request_data(
    failure_data: dict[str, Any] = None,
    include_policy_refs: bool = True,
    include_remediation: bool = True,
) -> dict[str, Any]:
    """Factory for explanation request data"""
    if failure_data is None:
        failure_data = create_validation_failure()

    return {
        "failure": failure_data,
        "include_policy_refs": include_policy_refs,
        "include_remediation": include_remediation,
    }


def create_explanation_response_data(
    explanation: str = "Test explanation",
    recommendation: str = "Test recommendation",
    confidence: float = 0.85,
    policy_references: list[str] = None,
    suggested_actions: list[str] = None,
) -> dict[str, Any]:
    """Factory for explanation response data"""
    return {
        "explanation": explanation,
        "recommendation": recommendation,
        "confidence": confidence,
        "policy_references": policy_references or ["Policy Reference 1"],
        "suggested_actions": suggested_actions or ["Action 1", "Action 2"],
    }


def create_rulepack_registration(
    domain: str = "test.domain",
    endpoint_url: str = "http://localhost:9000/rulepack",
    status: str = "active",
    supported_modes: list[str] = None,
):
    """Factory for RulePack registration mock"""
    from unittest.mock import Mock

    registration = Mock()
    registration.domain = domain
    registration.endpoint_url = endpoint_url
    registration.status = Mock(value=status)
    registration.supported_modes = supported_modes or ["static", "hybrid", "agentic"]

    return registration


def create_user_info(
    username: str = "test_user",
    tenant_id: str = "test_tenant",
    roles: list[str] = None,
    scopes: list[str] = None,
) -> dict[str, Any]:
    """Factory for user info data"""
    if roles is None:
        roles = ["user"]
    if scopes is None:
        scopes = ["read", "write"]

    return {
        "valid": True,
        "username": username,
        "tenant_id": tenant_id,
        "roles": roles,
        "scopes": scopes,
    }


def create_audit_event(
    tenant_id: str = "test_tenant",
    action: str = "test_action",
    resource: str = "test_resource",
    request_id: str = None,
    details: dict[str, Any] = None,
) -> dict[str, Any]:
    """Factory for audit event data"""
    if request_id is None:
        request_id = f"test-{uuid.uuid4().hex[:8]}"

    return {
        "tenant_id": tenant_id,
        "action": action,
        "resource": resource,
        "request_id": request_id,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat(),
    }


def create_comparison_delta(
    json_only_failures: list[str] = None,
    rag_only_failures: list[str] = None,
    common_failures: list[str] = None,
    agreement_rate: float = 0.85,
) -> dict[str, Any]:
    """Factory for comparison delta data (hybrid mode)"""
    if json_only_failures is None:
        json_only_failures = ["JSON_001"]
    if rag_only_failures is None:
        rag_only_failures = ["RAG_001"]
    if common_failures is None:
        common_failures = ["COMMON_001", "COMMON_002"]

    return {
        "json_only_failures": json_only_failures,
        "rag_only_failures": rag_only_failures,
        "common_failures": common_failures,
        "agreement_rate": agreement_rate,
        "json_failure_count": len(json_only_failures) + len(common_failures),
        "rag_failure_count": len(rag_only_failures) + len(common_failures),
        "avg_rag_confidence": 0.85,
        "validation_mode": "hybrid_comparison",
        "analysis_timestamp": datetime.utcnow().isoformat(),
    }


def create_rag_validation_data(
    failures: list[dict[str, Any]] = None,
    confidence_scores: list[float] = None,
    processing_time_ms: int = 250,
) -> dict[str, Any]:
    """Factory for RAG validation data"""
    if failures is None:
        failures = []
    if confidence_scores is None:
        confidence_scores = []

    return {
        "failures": failures,
        "confidence_scores": confidence_scores,
        "processing_time_ms": processing_time_ms,
        "source": "rag_validation",
    }
