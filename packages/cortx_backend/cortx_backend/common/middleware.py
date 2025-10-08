from __future__ import annotations

import uuid

from fastapi import Request, Response


def add_common_middleware(app) -> None:
    @app.middleware("http")
    async def correlation_id_middleware(request: Request, call_next):
        corr_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = corr_id
        response: Response = await call_next(request)
        response.headers["X-Correlation-ID"] = corr_id
        return response
