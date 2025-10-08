import os

from fastapi import APIRouter

router = APIRouter()


def _service(name: str, port_env: str, default_port: int, status: str = "operational"):
    port = int(os.getenv(port_env, default_port))
    return {
        "name": name,
        "url": f"http://localhost:{port}",
        "port": port,
        "status": status,
    }


@router.get("/v1/services")
async def get_services():
    """Simple service discovery endpoint for local dev.

    Frontend still reads ~/.cortx/services in Phase 0; this prepares
    for Phase 1 when frontend can call the gateway.
    """
    return {
        "gateway": _service("gateway", "CORTX_GATEWAY_PORT", 8000),
        "fedsuite": _service("fedsuite", "FEDSUITE_PORT", 8081),
        "claimsuite": _service("claimsuite", "CLAIMSUITE_PORT", 8082, status="planned"),
        "govsuite": _service("govsuite", "GOVSUITE_PORT", 8083, status="planned"),
        "medsuite": _service("medsuite", "MEDSUITE_PORT", 8084, status="planned"),
        "identity": _service("identity", "CORTX_IDENTITY_PORT", 8082, status="planned"),
        "schemas": _service("schemas", "CORTX_SCHEMAS_PORT", 8085, status="planned"),
    }
