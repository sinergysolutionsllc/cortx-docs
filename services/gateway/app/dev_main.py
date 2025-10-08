from typing import Optional

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CORTX Gateway (Dev Minimal)", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID", "x-correlation-id", "traceparent"],
)


@app.get("/health")
async def health():
    return {"ok": True, "service": "gateway-dev"}


@app.get("/")
async def root():
    return {"service": "gateway-dev", "status": "ok"}


# Minimal PropVerify proxy (inline)
from fastapi import HTTPException, Request, Response  # noqa: E402

INGESTION_URL = "http://localhost:8000"
VALIDATION_URL = "http://localhost:8003"
WORKFLOW_URL = "http://localhost:8001"
LEDGER_URL = "http://localhost:8002"
AI_URL = "http://localhost:8004"


def _forward_headers(request: Request, extra: Optional[dict[str, str]] = None) -> dict[str, str]:
    headers: dict[str, str] = {}
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


async def _proxy(request: Request, base: str, path: str) -> Response:
    url = f"{base}/{path.lstrip('/')}"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            body = await request.body()
            resp = await client.request(
                method=request.method,
                url=url,
                params=dict(request.query_params),
                content=body if body else None,
                headers=_forward_headers(request),
            )
        return Response(
            content=resp.content, status_code=resp.status_code, headers=dict(resp.headers)
        )
    except httpx.TimeoutException as e:
        raise HTTPException(status_code=504, detail="PropVerify backend timeout") from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"PropVerify backend error: {str(e)}") from e


@app.post("/ingestion/ingest")
async def pv_ingest(request: Request) -> Response:
    return await _proxy(request, INGESTION_URL, "/ingest")


@app.post("/ingestion/ingest-url")
async def pv_ingest_url(request: Request) -> Response:
    return await _proxy(request, INGESTION_URL, "/ingest-url")


@app.post("/validation/validate")
async def pv_validate(request: Request) -> Response:
    return await _proxy(request, VALIDATION_URL, "/validate")


@app.post("/workflow/execute-workflow")
async def pv_workflow_execute(request: Request) -> Response:
    return await _proxy(request, WORKFLOW_URL, "/execute-workflow")


@app.post("/workflow/approve/{approval_task_id}")
async def pv_workflow_approve(request: Request, approval_task_id: str) -> Response:
    return await _proxy(request, WORKFLOW_URL, f"/workflow/approve/{approval_task_id}")


@app.get("/workflow/status/{workflow_id}")
async def pv_workflow_status(request: Request, workflow_id: str) -> Response:
    return await _proxy(request, WORKFLOW_URL, f"/workflow/status/{workflow_id}")


@app.post("/designer/compile")
async def pv_designer_compile(request: Request) -> Response:
    return await _proxy(request, WORKFLOW_URL, "/designer/compile")


@app.get("/ai-models")
async def pv_ai_models(request: Request) -> Response:
    return await _proxy(request, AI_URL, "/ai-models")


@app.post("/generate")
async def pv_generate(request: Request) -> Response:
    return await _proxy(request, AI_URL, "/generate")


@app.get("/signing-status")
async def pv_signing_status(request: Request) -> Response:
    return await _proxy(request, AI_URL, "/signing-status")


@app.post("/verify-signature")
async def pv_verify_signature(request: Request) -> Response:
    return await _proxy(request, AI_URL, "/verify-signature")


@app.post("/ledger/anchor-hash")
async def pv_anchor_hash(request: Request) -> Response:
    return await _proxy(request, LEDGER_URL, "/anchor-hash")


@app.get("/ledger/verify-anchor/{txid}")
async def pv_verify_anchor(request: Request, txid: str) -> Response:
    return await _proxy(request, LEDGER_URL, f"/verify-anchor/{txid}")


@app.get("/ledger/transaction-status/{txid}")
async def pv_transaction_status(request: Request, txid: str) -> Response:
    return await _proxy(request, LEDGER_URL, f"/transaction-status/{txid}")
