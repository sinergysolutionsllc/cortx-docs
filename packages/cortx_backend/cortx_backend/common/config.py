from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CORTXConfig:
    gateway_url: str
    compliance_url: str | None = None
    workflow_url: str | None = None
    validation_url: str | None = None
    schemas_url: str | None = None
    identity_url: str | None = None
    config_url: str | None = None
    otel_exporter_otlp_endpoint: str | None = None
    log_level: str = "INFO"

    @staticmethod
    def from_env() -> CORTXConfig:
        return CORTXConfig(
            gateway_url=os.getenv("CORTX_GATEWAY_URL", ""),
            compliance_url=os.getenv("CORTX_COMPLIANCE_URL"),
            workflow_url=os.getenv("CORTX_WORKFLOW_URL"),
            validation_url=os.getenv("CORTX_VALIDATION_URL"),
            schemas_url=os.getenv("CORTX_SCHEMAS_URL"),
            identity_url=os.getenv("CORTX_IDENTITY_URL"),
            config_url=os.getenv("CORTX_CONFIG_URL"),
            otel_exporter_otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
