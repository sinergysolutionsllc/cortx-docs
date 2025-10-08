"""
Flask to FastAPI proxy for FedSuite during migration
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from ..middleware.auth import get_current_user

router = APIRouter(prefix="/fedsuite", tags=["FedSuite Proxy"])

# FedSuite Flask backend URL
FEDSUITE_URL = "http://localhost:8081"


async def proxy_request(
    request: Request, path: str, user: dict | None = None, add_headers: dict | None = None
):
    """Proxy requests to Flask FedSuite with JWT context"""

    # Build target URL
    target_url = f"{FEDSUITE_URL}/{path}"

    # Prepare headers
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("authorization", None)  # Remove JWT, add session

    # Add user context headers for Flask backend
    if user:
        headers["X-User-Id"] = user.get("username", "anonymous")
        headers["X-Tenant-Id"] = user.get("tenant_id", "default")
        headers["X-User-Roles"] = ",".join(user.get("roles", []))

    if add_headers:
        headers.update(add_headers)

    # Handle different content types
    content_type = request.headers.get("content-type", "")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if "multipart/form-data" in content_type:
                # Handle file uploads
                form = await request.form()
                files = {}
                data = {}

                for key, value in form.items():
                    if hasattr(value, "file"):
                        files[key] = (value.filename, await value.read(), value.content_type)
                    else:
                        data[key] = value

                response = await client.request(
                    method=request.method,
                    url=target_url,
                    params=dict(request.query_params),
                    files=files if files else None,
                    data=data if data else None,
                    headers={k: v for k, v in headers.items() if k.lower() != "content-type"},
                )
            else:
                # Handle JSON and other requests
                body = await request.body()
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    params=dict(request.query_params),
                    content=body if body else None,
                    headers=headers,
                )

        # Return proxied response
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )

    except httpx.TimeoutException as e:
        raise HTTPException(status_code=504, detail="FedSuite backend timeout") from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FedSuite backend error: {str(e)}") from e


# Public endpoints (no auth required)
@router.api_route("/health", methods=["GET"])
async def health_check(request: Request):
    """Health check doesn't require auth"""
    return await proxy_request(request, "health")


# Protected endpoints (require JWT auth)
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_all(
    request: Request, path: str, user: dict = Depends(get_current_user)
):  # noqa: B008
    """Proxy all other requests with JWT validation"""
    return await proxy_request(request, path, user)


# Special handling for file uploads
@router.post("/upload-raw-tb/")
async def upload_trial_balance(
    request: Request, user: dict = Depends(get_current_user)
):  # noqa: B008
    """Handle trial balance upload with JWT auth"""
    return await proxy_request(request, "upload-raw-tb/", user)


@router.post("/upload-gtas/")
async def upload_gtas(request: Request, user: dict = Depends(get_current_user)):  # noqa: B008
    """Handle GTAS upload with JWT auth"""
    return await proxy_request(request, "upload-gtas/", user)


@router.post("/reconcile/")
async def reconcile(request: Request, user: dict = Depends(get_current_user)):  # noqa: B008
    """Handle reconciliation with JWT auth"""
    return await proxy_request(request, "reconcile/", user)


@router.post("/validate-edits/")
async def validate_edits(request: Request, user: dict = Depends(get_current_user)):  # noqa: B008
    """Handle validation with JWT auth"""
    return await proxy_request(request, "validate-edits/", user)


@router.post("/ai-recommendations/")
async def ai_recommendations(
    request: Request, user: dict = Depends(get_current_user)
):  # noqa: B008
    """Handle AI recommendations with JWT auth"""
    return await proxy_request(request, "ai-recommendations/", user)
