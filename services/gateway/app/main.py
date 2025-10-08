import os
from contextlib import asynccontextmanager

from cortx_core.logging import configure_logging
from cortx_core.middleware import RequestContextMiddleware
from cortx_rulepack_sdk.registry import RegistryClient
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Optional: settings may provide env, allowed origins, log level
try:
    from cortx_core.config import settings  # type: ignore
except Exception:  # fallback defaults if settings not present

    class _Defaults:
        env = "dev"
        log_level = "INFO"
        allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
        registry_url = "http://localhost:8081"  # Default registry URL

    settings = _Defaults()  # type: ignore

from app.policy_router import PolicyRouter
from app.routers import analytics, fedsuite_proxy, orchestrator, platform_services, propverify_proxy
from app.routers import services as services_router

# DEPRECATED: Legacy reconciliation module - functionality moved to Validation service
# from cortx_recon.api.router import router as recon_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure logging
    configure_logging(level=getattr(settings, "log_level", "INFO"))

    # Initialize registry client
    registry_url = os.getenv(
        "CORTX_REGISTRY_URL", getattr(settings, "registry_url", "http://localhost:8081")
    )
    registry_client = RegistryClient(registry_url)

    # Initialize policy router
    policy_router = PolicyRouter(registry_client)

    # Store in orchestrator module for dependency injection
    orchestrator.policy_router = policy_router
    analytics.policy_router = policy_router

    try:
        # Connect to registry
        await registry_client.connect()
        print(f"✅ Connected to CORTX Registry at {registry_url}")

        yield

    finally:
        # Cleanup
        await policy_router.cleanup()
        await registry_client.disconnect()
        print("🧹 CORTX Gateway cleanup completed")


app = FastAPI(title="CORTX Gateway", version="0.1.0", lifespan=lifespan)

# Core middlewares (request context, CORS)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "allowed_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-request-id", "x-tenant-id"],
)


# Health endpoint
@app.get("/health")
async def health():
    return {"ok": True}


# Root endpoint
@app.get("/")
async def root():
    return {"service": "cortx-gateway", "status": "ok", "env": getattr(settings, "env", "dev")}


# Service info endpoint (useful in CI/CD and probes)
@app.get("/_info")
async def info():
    return {
        "name": "CORTX Gateway",
        "version": "0.1.0",
        "env": getattr(settings, "env", "dev"),
        "routers": ["/orchestrator", "/v1/rag", "/v1/ocr", "/v1/ledger", "/v1/validation"],
        "features": [
            "RulePack orchestration",
            "Policy-based routing",
            "Multi-mode validation",
            "AI/JSON hybrid processing",
            "Hierarchical RAG (ThinkTank)",
            "OCR text extraction",
            "Immutable audit ledger",
        ],
    }


# Mount API routers
app.include_router(orchestrator.router, prefix="", tags=["Orchestrator"])  # Main CORTX API
app.include_router(
    analytics.router, prefix="/analytics", tags=["Analytics"]
)  # Hybrid mode analytics
# DEPRECATED: Legacy reconciliation API - use Validation service instead
# app.include_router(
#     recon_router, prefix="/recon", tags=["Reconciliation"]
# )  # Legacy reconciliation API
app.include_router(services_router.router, prefix="", tags=["Services"])  # Service discovery
app.include_router(
    platform_services.router, prefix="", tags=["Platform Services"]
)  # RAG, OCR, Ledger
app.include_router(fedsuite_proxy.router, tags=["FedSuite"])  # FedSuite proxy with JWT auth
app.include_router(propverify_proxy.router, tags=["PropVerify"])  # PropVerify proxy (dev/local)
