"""
Integration tests for Platform Services Proxy

Tests proxying to RAG, OCR, and Ledger services
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest


@pytest.mark.integration
@pytest.mark.proxy
class TestRAGServiceProxy:
    """Test RAG service proxy endpoints"""

    def test_rag_query(self, client, mock_httpx_client, mock_platform_service):
        """Test POST /v1/rag/query"""
        mock_platform_service(200, {"answer": "Test answer", "sources": []})

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.post("/v1/rag/query", json={"query": "Test query", "top_k": 5})

            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "Test answer"

    def test_rag_retrieve(self, client, mock_httpx_client, mock_platform_service):
        """Test POST /v1/rag/retrieve"""
        mock_platform_service(200, {"chunks": [], "count": 0})

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.post("/v1/rag/retrieve", json={"query": "Test query"})

            assert response.status_code == 200

    def test_rag_upload_document(self, client, mock_httpx_client, mock_platform_service):
        """Test POST /v1/rag/documents/upload"""
        mock_platform_service(200, {"document_id": "doc-123", "status": "uploaded"})

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.post(
                "/v1/rag/documents/upload",
                files={"file": ("test.pdf", b"PDF content", "application/pdf")},
            )

            assert response.status_code == 200

    def test_rag_list_documents(self, client, mock_httpx_client, mock_platform_service):
        """Test GET /v1/rag/documents"""
        mock_platform_service(200, {"documents": [], "total": 0})

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.get("/v1/rag/documents")

            assert response.status_code == 200

    def test_rag_delete_document(self, client, mock_httpx_client, mock_platform_service):
        """Test DELETE /v1/rag/documents/{document_id}"""
        mock_platform_service(200, {"status": "deleted"})

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.delete("/v1/rag/documents/doc-123")

            assert response.status_code == 200

    def test_rag_health_check(self, client, mock_httpx_client, mock_platform_service):
        """Test GET /v1/rag/healthz"""
        mock_platform_service(200, {"status": "healthy"})

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.get("/v1/rag/healthz")

            assert response.status_code == 200

    def test_rag_service_timeout(self, client, mock_httpx_client):
        """Test RAG service timeout handling"""
        mock_httpx_client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.post("/v1/rag/query", json={"query": "test"})

            assert response.status_code == 504
            assert "timeout" in response.json()["detail"].lower()

    def test_rag_service_unavailable(self, client, mock_httpx_client):
        """Test RAG service connection error handling"""
        mock_httpx_client.request = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.post("/v1/rag/query", json={"query": "test"})

            assert response.status_code == 503
            assert "unavailable" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.proxy
class TestOCRServiceProxy:
    """Test OCR service proxy endpoints"""

    def test_ocr_extract(self, client, mock_httpx_client, mock_platform_service):
        """Test POST /v1/ocr/extract"""
        mock_platform_service(200, {"job_id": "ocr-123", "status": "processing"})

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.post(
                "/v1/ocr/extract",
                files={"file": ("document.pdf", b"PDF content", "application/pdf")},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "ocr-123"

    def test_ocr_get_results(self, client, mock_httpx_client, mock_platform_service):
        """Test GET /v1/ocr/results/{job_id}"""
        mock_platform_service(
            200, {"job_id": "ocr-123", "status": "completed", "text": "Extracted text"}
        )

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.get("/v1/ocr/results/ocr-123")

            assert response.status_code == 200

    def test_ocr_health_check(self, client, mock_httpx_client, mock_platform_service):
        """Test GET /v1/ocr/healthz"""
        mock_platform_service(200, {"status": "healthy"})

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.get("/v1/ocr/healthz")

            assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.proxy
class TestLedgerServiceProxy:
    """Test Ledger service proxy endpoints"""

    def test_ledger_append(self, client, mock_httpx_client, mock_platform_service):
        """Test POST /v1/ledger/append"""
        mock_platform_service(200, {"event_id": "evt-123", "status": "appended"})

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.post(
                "/v1/ledger/append", json={"event_type": "validation", "data": {"test": "data"}}
            )

            assert response.status_code == 200

    def test_ledger_verify(self, client, mock_httpx_client, mock_platform_service):
        """Test GET /v1/ledger/verify"""
        mock_platform_service(200, {"valid": True, "chain_length": 100})

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.get("/v1/ledger/verify")

            assert response.status_code == 200

    def test_ledger_events(self, client, mock_httpx_client, mock_platform_service):
        """Test GET /v1/ledger/events"""
        mock_platform_service(200, {"events": [], "total": 0})

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.get("/v1/ledger/events")

            assert response.status_code == 200

    def test_ledger_export(self, client, mock_httpx_client, mock_platform_service):
        """Test GET /v1/ledger/export"""
        mock_platform_service(200, {"download_url": "https://example.com/export.csv"})

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.get("/v1/ledger/export")

            assert response.status_code == 200

    def test_ledger_health_check(self, client, mock_httpx_client, mock_platform_service):
        """Test GET /v1/ledger/healthz"""
        mock_platform_service(200, {"status": "healthy"})

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.get("/v1/ledger/healthz")

            assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.proxy
class TestProxyErrorHandling:
    """Test proxy error handling"""

    def test_proxy_general_error(self, client, mock_httpx_client):
        """Test proxy handles general errors"""
        mock_httpx_client.request = AsyncMock(side_effect=Exception("Unexpected error"))

        with patch(
            "app.routers.platform_services.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            response = client.post("/v1/rag/query", json={"query": "test"})

            assert response.status_code == 502
            assert "error" in response.json()["detail"].lower()
