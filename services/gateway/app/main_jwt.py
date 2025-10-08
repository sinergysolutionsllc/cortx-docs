"""
CORTX Gateway with JWT Authentication
"""

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import auth middleware
try:
    from app.middleware.auth import auth_middleware, get_current_user
except ImportError:
    # Fallback for testing
    auth_middleware = None
    get_current_user = None

# Import routers
try:
    from app.routers import analytics, orchestrator
    from app.routers import services as services_router
except ImportError:
    services_router = None
    orchestrator = None
    analytics = None


# Settings
class Settings:
    env = os.getenv("ENV", "dev")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    identity_service_url = os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8082")


settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    print(f"🚀 Starting CORTX Gateway in {settings.env} mode")
    print(f"🔐 Identity Service: {settings.identity_service_url}")

    yield

    print("🧹 CORTX Gateway shutting down")


app = FastAPI(
    title="CORTX Gateway",
    version="0.2.0",
    description="API Gateway with JWT Authentication",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-request-id", "x-tenant-id"],
)


# Public endpoints (no auth required)
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "gateway", "version": "0.2.0"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "cortx-gateway",
        "version": "0.2.0",
        "status": "operational",
        "env": settings.env,
        "auth": "JWT",
    }


@app.get("/_info")
async def info():
    """Service information"""
    return {
        "name": "CORTX Gateway",
        "version": "0.2.0",
        "env": settings.env,
        "features": [
            "JWT Authentication",
            "Multi-tenant support",
            "Service discovery",
            "Event-driven architecture",
            "RulePack orchestration",
            "AI service broker",
        ],
        "services": {"identity": settings.identity_service_url, "gateway": "http://localhost:8080"},
    }


# Auth proxy endpoint (forward to identity service)
@app.post("/auth/login")
async def login_proxy(request: Request):
    """Proxy login requests to identity service"""
    import httpx

    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{settings.identity_service_url}/v1/auth/login", json=body)

    return JSONResponse(content=response.json(), status_code=response.status_code)


# Protected endpoints (require authentication)
@app.get("/v1/services")
async def get_services(
    user: dict = Depends(get_current_user) if get_current_user else None,
):  # noqa: B008
    """Service discovery endpoint"""
    return {
        "services": {
            "gateway": {
                "url": "http://localhost:8080",
                "status": "operational",
                "version": "0.2.0",
            },
            "identity": {
                "url": "http://localhost:8082",
                "status": "operational",
                "version": "0.1.0",
            },
            "fedsuite": {
                "url": "http://localhost:8081",
                "status": "operational",
                "version": "1.0.0",
            },
            "validation": {"url": "http://localhost:8083", "status": "planned"},
            "rulepacks": {"url": "http://localhost:8084", "status": "planned"},
            "ai-broker": {"url": "http://localhost:8085", "status": "planned"},
            "workflow": {"url": "http://localhost:8086", "status": "planned"},
            "compliance": {"url": "http://localhost:8087", "status": "planned"},
        },
        "user": user.get("username") if user else "anonymous",
        "tenant": user.get("tenant_id") if user else "default",
    }


@app.get("/v1/user")
async def get_user_info(
    user: dict = Depends(get_current_user) if get_current_user else None,
):  # noqa: B008
    """Get current user information"""
    if not user:
        return {"error": "Not authenticated"}

    return {
        "username": user.get("username"),
        "tenant_id": user.get("tenant_id"),
        "roles": user.get("roles"),
        "scopes": user.get("scopes"),
    }


# Mount existing routers if available
if orchestrator and orchestrator.router:
    app.include_router(orchestrator.router, prefix="/orchestrator", tags=["Orchestrator"])

if analytics and analytics.router:
    app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

if services_router and services_router.router:
    app.include_router(services_router.router, prefix="/discovery", tags=["Discovery"])


# Error handlers
@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc):
    return JSONResponse(status_code=401, content={"detail": "Authentication required"})


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc):
    return JSONResponse(status_code=403, content={"detail": "Insufficient permissions"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
