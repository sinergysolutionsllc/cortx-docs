from typing import Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class TraceContext(BaseModel):
    request_id: str = Field(..., description="Unique ID per request")
    session_id: str | None = None
    user_id: str | None = None
    tenant_id: str = Field(...)
    model_ref: str | None = None


class MessageEnvelope(BaseModel):
    version: str = "1.0"
    kind: Literal["ingest", "validate", "transform", "ai_task", "orchestrate", "report"]
    ts: datetime = Field(default_factory=datetime.utcnow)
    trace: TraceContext
    payload: dict[str, Any]
    labels: dict[str, str] = Field(default_factory=dict)


class ValidationIssue(BaseModel):
    code: str
    severity: Literal["fatal", "error", "warning", "info"]
    field: str | None = None
    message: str
    hint: str | None = None


class ValidationReport(BaseModel):
    ok: bool
    issues: list[ValidationIssue] = []
    stats: dict[str, int] = Field(default_factory=dict)


class AuditEvent(BaseModel):
    ts: datetime = Field(default_factory=datetime.utcnow)
    user_id: str | None = None
    tenant_id: str
    action: str
    resource: str
    request_id: str
    details: dict[str, Any] = Field(default_factory=dict)


class WorkflowJob(BaseModel):
    job_id: str
    name: str
    status: Literal["queued", "running", "succeeded", "failed", "canceled"]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tenant_id: str
    meta: dict[str, Any] = Field(default_factory=dict)
