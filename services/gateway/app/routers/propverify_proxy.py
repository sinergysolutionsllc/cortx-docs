"""
PropVerify proxy routes for local development and integration testing.

Forwards Gateway requests to PropVerify backend services running locally:
- ingestion-svc (http://localhost:8000)
- validation-svc (http://localhost:8003)
- workflow-svc (http://localhost:8001)
- ledger-svc (http://localhost:8002)
- ai-svc (http://localhost:8004)

Notes:
- Preserves Authorization, X-Correlation-ID, and traceparent headers.
- Secures routes with JWT where applicable; uses role checks for write paths.
"""

from typing import Optional

import httpx
from app.middleware.auth import get_current_user, require_role
from fastapi import APIRouter, Depends, HTTPException, Request, Response

router = APIRouter(tags=["PropVerify Proxy"])

INGESTION_URL = "http://localhost:8000"
VALIDATION_URL = "http://localhost:8003"
WORKFLOW_URL = "http://localhost:8001"
LEDGER_URL = "http://localhost:8002"
AI_URL = "http://localhost:8004"


def _forward_headers(request: Request, extra: Optional[dict[str, str]] = None) -> dict[str, str]:
    headers = {}
    auth = request.headers.get("authorization")
    if auth:
        headers["authorization"] = auth
    corr = request.headers.get("x-correlation-id") or request.headers.get("X-Correlation-ID")
    if corr:
        headers["X-Correlation-ID"] = corr
    trace = request.headers.get("traceparent")
    if trace:
        headers["traceparent"] = trace
    if extra:
        headers.update(extra)
    return headers


async def _proxy(request: Request, target_base: str, target_path: str) -> Response:
    url = f"{target_base}/{target_path.lstrip('/')}"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            body = await request.body()
            response = await client.request(
                method=request.method,
                url=url,
                params=dict(request.query_params),
                content=body if body else None,
                headers=_forward_headers(request),
            )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
    except httpx.TimeoutException as e:
        raise HTTPException(status_code=504, detail="PropVerify backend timeout") from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"PropVerify backend error: {str(e)}") from e


# Ingestion
@router.post("/ingestion/ingest")
async def pv_ingest(
    request: Request, user: dict = Depends(require_role("propverify:ingest"))
):  # noqa: B008
    return await _proxy(request, INGESTION_URL, "/ingest")


@router.post("/ingestion/ingest-url")
async def pv_ingest_url(
    request: Request, user: dict = Depends(require_role("propverify:ingest"))
):  # noqa: B008
    return await _proxy(request, INGESTION_URL, "/ingest-url")


# Validation
@router.post("/validation/validate")
async def pv_validate(
    request: Request, user: dict = Depends(require_role("propverify:validate"))
):  # noqa: B008
    return await _proxy(request, VALIDATION_URL, "/validate")


# Workflow
@router.post("/workflow/execute-workflow")
async def pv_workflow_execute(
    request: Request, user: dict = Depends(require_role("propverify:workflow:execute"))
):  # noqa: B008
    return await _proxy(request, WORKFLOW_URL, "/execute-workflow")


@router.post("/workflow/approve/{approval_task_id}")
async def pv_workflow_approve(
    request: Request,
    approval_task_id: str,
    user: dict = Depends(require_role("propverify:workflow:approve")),
):  # noqa: B008
    return await _proxy(request, WORKFLOW_URL, f"/workflow/approve/{approval_task_id}")


@router.get("/workflow/status/{workflow_id}")
async def pv_workflow_status(
    request: Request, workflow_id: str, user: dict = Depends(get_current_user)
):  # noqa: B008
    return await _proxy(request, WORKFLOW_URL, f"/workflow/status/{workflow_id}")


# Designer
@router.post("/designer/compile")
async def pv_designer_compile(
    request: Request, user: dict = Depends(require_role("propverify:workflow:execute"))
):  # noqa: B008
    return await _proxy(request, WORKFLOW_URL, "/designer/compile")


# AI
@router.get("/ai-models")
async def pv_ai_models(request: Request, user: dict = Depends(get_current_user)):  # noqa: B008
    return await _proxy(request, AI_URL, "/ai-models")


@router.post("/generate")
async def pv_generate(
    request: Request, user: dict = Depends(require_role("propverify:ai:generate"))
):  # noqa: B008
    return await _proxy(request, AI_URL, "/generate")


@router.get("/signing-status")
async def pv_signing_status(request: Request, user: dict = Depends(get_current_user)):  # noqa: B008
    return await _proxy(request, AI_URL, "/signing-status")


@router.post("/verify-signature")
async def pv_verify_signature(
    request: Request, user: dict = Depends(require_role("propverify:ai:sign"))
):  # noqa: B008
    return await _proxy(request, AI_URL, "/verify-signature")


# Ledger
@router.post("/ledger/anchor-hash")
async def pv_anchor_hash(
    request: Request, user: dict = Depends(require_role("propverify:ledger:anchor"))
):  # noqa: B008
    return await _proxy(request, LEDGER_URL, "/anchor-hash")


@router.get("/ledger/verify-anchor/{txid}")
async def pv_verify_anchor(
    request: Request, txid: str, user: dict = Depends(get_current_user)
):  # noqa: B008
    return await _proxy(request, LEDGER_URL, f"/verify-anchor/{txid}")


@router.get("/ledger/transaction-status/{txid}")
async def pv_transaction_status(
    request: Request, txid: str, user: dict = Depends(get_current_user)
):  # noqa: B008
    return await _proxy(request, LEDGER_URL, f"/transaction-status/{txid}")
