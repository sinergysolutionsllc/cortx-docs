"""
Integration tests for FedSuite Proxy

Tests proxying to FedSuite Flask backend with JWT authentication
"""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.integration
@pytest.mark.proxy
@pytest.mark.auth
class TestFedSuiteProxyPublicEndpoints:
    """Test public FedSuite endpoints (no auth required)"""

    def test_health_check_no_auth(self, client, mock_httpx_client, mock_platform_service):
        """Test /fedsuite/health doesn't require authentication"""
        mock_platform_service(200, {"status": "healthy"})

        with patch("app.routers.fedsuite_proxy.httpx.AsyncClient", return_value=mock_httpx_client):
            response = client.get("/fedsuite/health")

            assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.proxy
@pytest.mark.auth
class TestFedSuiteProxyProtectedEndpoints:
    """Test protected FedSuite endpoints (require JWT auth)"""

    def test_proxy_with_jwt_auth(
        self, client, auth_headers, mock_httpx_client, mock_platform_service
    ):
        """Test proxy forwards JWT user context"""
        mock_platform_service(200, {"status": "ok"})

        with patch("app.middleware.auth.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "username": "test_user",
                "tenant_id": "test_tenant",
                "roles": ["user"],
            }

            with patch(
                "app.routers.fedsuite_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.get("/fedsuite/api/data", headers=auth_headers)

                assert response.status_code == 200
                # Verify user context headers were added
                assert mock_httpx_client.request.called

    def test_upload_trial_balance(
        self, client, auth_headers, mock_httpx_client, mock_platform_service
    ):
        """Test POST /fedsuite/upload-raw-tb/"""
        mock_platform_service(200, {"upload_id": "upload-123", "status": "processing"})

        with patch("app.middleware.auth.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "username": "test_user",
                "tenant_id": "test_tenant",
                "roles": ["user"],
            }

            with patch(
                "app.routers.fedsuite_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.post(
                    "/fedsuite/upload-raw-tb/",
                    files={"file": ("tb.csv", b"CSV content", "text/csv")},
                    headers=auth_headers,
                )

                assert response.status_code == 200

    def test_upload_gtas(self, client, auth_headers, mock_httpx_client, mock_platform_service):
        """Test POST /fedsuite/upload-gtas/"""
        mock_platform_service(200, {"upload_id": "gtas-123", "status": "processing"})

        with patch("app.middleware.auth.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "username": "test_user",
                "tenant_id": "test_tenant",
                "roles": ["user"],
            }

            with patch(
                "app.routers.fedsuite_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.post(
                    "/fedsuite/upload-gtas/",
                    files={"file": ("gtas.csv", b"GTAS content", "text/csv")},
                    headers=auth_headers,
                )

                assert response.status_code == 200

    def test_reconcile(self, client, auth_headers, mock_httpx_client, mock_platform_service):
        """Test POST /fedsuite/reconcile/"""
        mock_platform_service(200, {"job_id": "recon-123", "status": "started"})

        with patch("app.middleware.auth.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "username": "test_user",
                "tenant_id": "test_tenant",
                "roles": ["user"],
            }

            with patch(
                "app.routers.fedsuite_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.post(
                    "/fedsuite/reconcile/",
                    json={"tb_id": "tb-123", "gtas_id": "gtas-123"},
                    headers=auth_headers,
                )

                assert response.status_code == 200

    def test_validate_edits(self, client, auth_headers, mock_httpx_client, mock_platform_service):
        """Test POST /fedsuite/validate-edits/"""
        mock_platform_service(200, {"validation_id": "val-123", "errors": []})

        with patch("app.middleware.auth.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "username": "test_user",
                "tenant_id": "test_tenant",
                "roles": ["user"],
            }

            with patch(
                "app.routers.fedsuite_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.post(
                    "/fedsuite/validate-edits/", json={"edits": []}, headers=auth_headers
                )

                assert response.status_code == 200

    def test_ai_recommendations(
        self, client, auth_headers, mock_httpx_client, mock_platform_service
    ):
        """Test POST /fedsuite/ai-recommendations/"""
        mock_platform_service(200, {"recommendations": []})

        with patch("app.middleware.auth.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "username": "test_user",
                "tenant_id": "test_tenant",
                "roles": ["user"],
            }

            with patch(
                "app.routers.fedsuite_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.post(
                    "/fedsuite/ai-recommendations/", json={"context": "test"}, headers=auth_headers
                )

                assert response.status_code == 200

    def test_proxy_timeout(self, client, auth_headers, mock_httpx_client):
        """Test FedSuite proxy timeout handling"""
        mock_httpx_client.request = AsyncMock(side_effect=Exception("Timeout"))

        with patch("app.middleware.auth.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "username": "test_user",
                "tenant_id": "test_tenant",
                "roles": ["user"],
            }

            with patch(
                "app.routers.fedsuite_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.get("/fedsuite/api/test", headers=auth_headers)

                assert response.status_code == 502
