from __future__ import annotations

from typing import Any

try:
    from prometheus_fastapi_instrumentator import Instrumentator
except Exception:  # pragma: no cover - optional dependency
    Instrumentator = None  # type: ignore[assignment]


def instrument_metrics(app: Any) -> None:
    """Attach Prometheus metrics to a FastAPI app if instrumentator is available.

    Safe no-op if the dependency is missing.
    """
    if Instrumentator is None:
        return
    Instrumentator().instrument(app).expose(app)
