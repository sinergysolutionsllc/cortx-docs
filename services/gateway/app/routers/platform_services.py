"""
Platform Services Proxy Router
Proxies requests to core CORTX platform services: RAG, OCR, Ledger
"""

import httpx
from fastapi import APIRouter, HTTPException, Request, Response

router = APIRouter(tags=["Platform Services"])

# Service URLs (configurable via environment variables)
import os

RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8138")
OCR_SERVICE_URL = os.getenv("OCR_SERVICE_URL", "http://localhost:8137")
LEDGER_SERVICE_URL = os.getenv("LEDGER_SERVICE_URL", "http://localhost:8136")


async def proxy_request(request: Request, target_url: str, service_name: str):
    """Generic proxy function for platform services"""

    # Prepare headers (copy from incoming request)
    headers = dict(request.headers)
    headers.pop("host", None)

    # Handle different content types
    content_type = request.headers.get("content-type", "")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if "multipart/form-data" in content_type:
                # Handle file uploads (for RAG document upload, OCR extraction)
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
        raise HTTPException(status_code=504, detail=f"{service_name} service timeout") from e
    except httpx.ConnectError as e:
        raise HTTPException(status_code=503, detail=f"{service_name} service unavailable") from e
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"{service_name} service error: {str(e)}"
        ) from e


# ============================================================================
# RAG Service Routes
# ============================================================================


@router.post("/v1/rag/query")
async def rag_query(request: Request):
    """Query the RAG system with hierarchical context"""
    return await proxy_request(request, f"{RAG_SERVICE_URL}/query", "RAG")


@router.post("/v1/rag/retrieve")
async def rag_retrieve(request: Request):
    """Retrieve relevant chunks without LLM generation"""
    return await proxy_request(request, f"{RAG_SERVICE_URL}/retrieve", "RAG")


@router.post("/v1/rag/documents/upload")
async def rag_upload_document(request: Request):
    """Upload a document to the RAG knowledge base"""
    return await proxy_request(request, f"{RAG_SERVICE_URL}/documents/upload", "RAG")


@router.get("/v1/rag/documents")
async def rag_list_documents(request: Request):
    """List documents in the RAG knowledge base"""
    return await proxy_request(request, f"{RAG_SERVICE_URL}/documents", "RAG")


@router.delete("/v1/rag/documents/{document_id}")
async def rag_delete_document(request: Request, document_id: str):
    """Delete a document from the RAG knowledge base"""
    return await proxy_request(request, f"{RAG_SERVICE_URL}/documents/{document_id}", "RAG")


@router.get("/v1/rag/healthz")
async def rag_health(request: Request):
    """RAG service health check"""
    return await proxy_request(request, f"{RAG_SERVICE_URL}/healthz", "RAG")


@router.get("/v1/rag/readyz")
async def rag_ready(request: Request):
    """RAG service ready check"""
    return await proxy_request(request, f"{RAG_SERVICE_URL}/readyz", "RAG")


# ============================================================================
# OCR Service Routes (when implemented)
# ============================================================================


@router.post("/v1/ocr/extract")
async def ocr_extract(request: Request):
    """Extract text from document"""
    return await proxy_request(request, f"{OCR_SERVICE_URL}/extract", "OCR")


@router.get("/v1/ocr/results/{job_id}")
async def ocr_get_results(request: Request, job_id: str):
    """Get OCR extraction results"""
    return await proxy_request(request, f"{OCR_SERVICE_URL}/results/{job_id}", "OCR")


@router.get("/v1/ocr/healthz")
async def ocr_health(request: Request):
    """OCR service health check"""
    return await proxy_request(request, f"{OCR_SERVICE_URL}/healthz", "OCR")


@router.get("/v1/ocr/readyz")
async def ocr_ready(request: Request):
    """OCR service ready check"""
    return await proxy_request(request, f"{OCR_SERVICE_URL}/readyz", "OCR")


# ============================================================================
# Ledger Service Routes (when implemented)
# ============================================================================


@router.post("/v1/ledger/append")
async def ledger_append(request: Request):
    """Append event to ledger"""
    return await proxy_request(request, f"{LEDGER_SERVICE_URL}/append", "Ledger")


@router.get("/v1/ledger/verify")
async def ledger_verify(request: Request):
    """Verify ledger integrity"""
    return await proxy_request(request, f"{LEDGER_SERVICE_URL}/verify", "Ledger")


@router.get("/v1/ledger/events")
async def ledger_events(request: Request):
    """List ledger events"""
    return await proxy_request(request, f"{LEDGER_SERVICE_URL}/events", "Ledger")


@router.get("/v1/ledger/export")
async def ledger_export(request: Request):
    """Export ledger events as CSV"""
    return await proxy_request(request, f"{LEDGER_SERVICE_URL}/export", "Ledger")


@router.get("/v1/ledger/healthz")
async def ledger_health(request: Request):
    """Ledger service health check"""
    return await proxy_request(request, f"{LEDGER_SERVICE_URL}/healthz", "Ledger")


@router.get("/v1/ledger/readyz")
async def ledger_ready(request: Request):
    """Ledger service ready check"""
    return await proxy_request(request, f"{LEDGER_SERVICE_URL}/readyz", "Ledger")
