from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationClient:
    """Thin client wrapper for CORTX Validation service.

    Interfaces only; integrate via Gateway or direct service URL with JWT.
    """

    base_url: str = os.getenv("CORTX_VALIDATION_URL", "") or os.getenv("CORTX_GATEWAY_URL", "")

    def execute_rulepack(self, *, pack_id: str, payload: dict) -> None:
        raise NotImplementedError("Validation integration must be implemented by core logic agent.")


@dataclass(frozen=True)
class SchemasClient:
    base_url: str = os.getenv("CORTX_SCHEMAS_URL", "") or os.getenv("CORTX_GATEWAY_URL", "")

    def get_schema(self, *, name: str, version: str | None = None) -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class ComplianceClient:
    base_url: str = os.getenv("CORTX_COMPLIANCE_URL", "") or os.getenv("CORTX_GATEWAY_URL", "")

    def log_event(self, *, event: dict) -> None:
        raise NotImplementedError
