from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowClient:
    """Thin client wrapper for CORTX Workflow service.

    Interfaces only; integrate via Gateway or direct service URL with JWT.
    """

    base_url: str = os.getenv("CORTX_WORKFLOW_URL", "") or os.getenv("CORTX_GATEWAY_URL", "")

    def start_workflow(self, *, pack_id: str, payload: dict) -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class ComplianceClient:
    base_url: str = os.getenv("CORTX_COMPLIANCE_URL", "") or os.getenv("CORTX_GATEWAY_URL", "")

    def log_event(self, *, event: dict) -> None:
        raise NotImplementedError
