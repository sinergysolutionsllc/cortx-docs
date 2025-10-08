"""
Shared data models for CORTX integration.
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
import uuid
import hashlib

class EventType(str, Enum):
    """Canonical CORTX event types for audit logging."""
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_ACTION = "user.action"
    DATA_UPLOAD = "data.upload"
    DATA_VALIDATE = "data.validate"
    DATA_PROCESS = "data.process"
    DATA_EXPORT = "data.export"
    WORKFLOW_START = "workflow.start"
    WORKFLOW_STEP = "workflow.step"
    WORKFLOW_COMPLETE = "workflow.complete"
    WORKFLOW_FAIL = "workflow.fail"
    RULEPACK_EXECUTE = "rulepack.execute"
    RULEPACK_DEPLOY = "rulepack.deploy"
    AI_REQUEST = "ai.request"
    AI_RESPONSE = "ai.response"
    APPROVAL_REQUIRED = "approval.required"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_DENIED = "approval.denied"
    SYSTEM_ERROR = "system.error"
    SYSTEM_ALERT = "system.alert"

class ComplianceLevel(str, Enum):
    """Compliance levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ComplianceEvent(BaseModel):
    """
    Represents a canonical compliance event for the CORTX audit log.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: EventType
    compliance_level: ComplianceLevel
    user_id: str | None = None
    tenant_id: str = "default"
    session_id: str | None = None
    ip_address: str | None = None
    action: str
    resource: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    retention_years: int = 7
    immutable: bool = True
    hash: str | None = None
    source_system: str = "propverify"
    correlation_id: str | None = None

    def calculate_hash(self) -> str:
        """Calculates the tamper-evident hash of the event."""
        import json
        event_dict = self.model_dump(exclude={'hash'})
        event_str = json.dumps(event_dict, sort_keys=True, default=str)
        return hashlib.sha256(event_str.encode()).hexdigest()

    def sign(self) -> None:
        """Signs the event by setting its hash."""
        self.hash = self.calculate_hash()
