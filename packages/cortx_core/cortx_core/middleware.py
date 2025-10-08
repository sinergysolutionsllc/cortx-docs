import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from .config import settings
from .logging import logger


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        tenant_id = request.headers.get("x-tenant-id", settings.default_tenant_id)
        user_id = request.headers.get("x-user-id")
        log = logger.bind(request_id=request_id, tenant_id=tenant_id, path=request.url.path)
        request.state.request_id = request_id
        request.state.tenant_id = tenant_id
        request.state.user_id = user_id
        log.info("http.request.start", method=request.method)
        try:
            response = await call_next(request)
            log.info("http.request.end", status_code=response.status_code)
            response.headers["x-request-id"] = request_id
            response.headers["x-tenant-id"] = tenant_id
            return response
        except Exception as e:
            log.exception("http.request.error", error=str(e))
            raise
