"""
RulePack Contract Definitions

These are the standard interfaces that all RulePacks must implement.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ValidationMode(str, Enum):
    """Validation execution modes"""

    STATIC = "static"  # JSON rules only
    HYBRID = "hybrid"  # Both JSON and AI, compare results
    AGENTIC = "agentic"  # AI primary with JSON fallback


class SeverityLevel(str, Enum):
    """Severity levels for validation failures"""

    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationOptions(BaseModel):
    """Options for validation execution"""

    mode: ValidationMode = Field(default=ValidationMode.STATIC)
    include_explanations: bool = Field(default=True)
    include_recommendations: bool = Field(default=True)
    max_failures: int | None = Field(default=None, description="Stop after N failures")
    confidence_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    timeout_seconds: int | None = Field(default=300)
    tenant_id: str = Field(default="default")
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValidationFailure(BaseModel):
    """Individual validation failure"""

    rule_id: str = Field(..., description="Unique rule identifier")
    rule_name: str = Field(..., description="Human-readable rule name")
    severity: SeverityLevel
    line_number: int | None = Field(default=None)
    field: str | None = Field(default=None)
    record_identifier: str | None = Field(default=None)
    failure_description: str
    expected_value: Any | None = None
    actual_value: Any | None = None

    # AI/RAG enhancements (optional)
    ai_explanation: str | None = None
    ai_recommendation: str | None = None
    ai_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    policy_references: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)

    # Tracking
    failure_id: str | None = Field(default=None, description="UUID for tracking")
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class ValidationStats(BaseModel):
    """Statistics from validation run"""

    total_records: int = 0
    records_processed: int = 0
    records_failed: int = 0
    total_failures: int = 0
    fatal_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    processing_time_ms: int | None = None
    mode_used: ValidationMode = ValidationMode.STATIC
    ai_queries_executed: int = 0
    avg_ai_confidence: float | None = None


class ValidationRequest(BaseModel):
    """Request to validate data"""

    domain: str = Field(..., description="Domain identifier (gtas, grants, claims, etc.)")
    input_type: Literal["file", "records", "reference"] = Field(default="records")
    input_data: Any | None = Field(default=None, description="Inline data for validation")
    input_ref: str | None = Field(default=None, description="Reference to stored data")
    options: ValidationOptions = Field(default_factory=ValidationOptions)
    request_id: str = Field(..., description="Unique request identifier")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)


class ValidationResponse(BaseModel):
    """Response from validation"""

    request_id: str
    domain: str
    success: bool = Field(..., description="True if validation completed (may have failures)")
    summary: ValidationStats
    failures: list[ValidationFailure] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    # Mode tracking
    mode_requested: ValidationMode
    mode_executed: ValidationMode
    fallback_reason: str | None = Field(default=None, description="Why fallback was triggered")

    # For hybrid mode
    comparison_delta: dict[str, Any] | None = Field(
        default=None, description="Differences between static and AI validation"
    )


class ExplanationRequest(BaseModel):
    """Request for failure explanation"""

    failure: ValidationFailure
    include_policy_refs: bool = Field(default=True)
    include_remediation: bool = Field(default=True)
    context: dict[str, Any] = Field(default_factory=dict)


class ExplanationResponse(BaseModel):
    """Enhanced explanation for a failure"""

    failure_id: str
    explanation: str
    recommendation: str
    confidence: float = Field(ge=0.0, le=1.0)
    policy_references: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    source: Literal["rag", "static", "hybrid"] = "static"
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class RuleInfo(BaseModel):
    """Information about a single rule"""

    rule_id: str
    rule_name: str
    category: str
    severity: SeverityLevel
    description: str
    version: str
    active: bool = True
    tags: list[str] = Field(default_factory=list)


class RulePackInfo(BaseModel):
    """Information about the RulePack"""

    domain: str
    name: str
    version: str
    rule_count: int
    categories: list[str]
    supported_modes: list[ValidationMode]
    capabilities: list[str] = Field(
        default_factory=list, description="e.g., ['validate', 'explain', 'remediate']"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class RulePackMetadata(BaseModel):
    """Detailed RulePack metadata"""

    info: RulePackInfo
    rules: list[RuleInfo] = Field(default_factory=list)
    schema_version: str = Field(default="1.0")
    created_at: datetime
    updated_at: datetime
    author: str | None = None
    description: str | None = None
    compliance_frameworks: list[str] = Field(
        default_factory=list, description="e.g., ['NIST-800-53', 'FedRAMP-High', 'HIPAA']"
    )
