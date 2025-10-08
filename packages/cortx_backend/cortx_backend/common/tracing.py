from __future__ import annotations

from typing import Any
import os
import uuid


def setup_tracing(service_name: str, app: Any | None = None) -> None:
    """Best-effort OpenTelemetry setup.

    - No-ops if OTEL packages are unavailable or endpoint not configured.
    - Instruments FastAPI app (if provided) and httpx client library.
    """
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return
    try:
        # Core SDK and exporter
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        # Instrumentations
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        except Exception:
            FastAPIInstrumentor = None  # type: ignore
        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        except Exception:
            HTTPXClientInstrumentor = None  # type: ignore

        resource = Resource.create({
            "service.name": service_name,
            "service.instance.id": str(uuid.uuid4()),
        })
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        if app is not None and FastAPIInstrumentor is not None:
            try:
                FastAPIInstrumentor.instrument_app(app)
            except Exception:
                pass
        if HTTPXClientInstrumentor is not None:
            try:
                HTTPXClientInstrumentor().instrument()
            except Exception:
                pass
    except Exception:
        # Silent no-op if any import/config fails
        return
