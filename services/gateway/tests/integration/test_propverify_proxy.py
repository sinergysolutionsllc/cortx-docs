"""
Integration tests for PropVerify Proxy

Tests proxying to PropVerify backend services with role-based authentication
"""

from unittest.mock import patch

import pytest


@pytest.mark.integration
@pytest.mark.proxy
@pytest.mark.auth
class TestPropVerifyIngestionProxy:
    """Test PropVerify ingestion service proxy"""

    def test_ingest_requires_role(
        self, client, auth_headers, mock_httpx_client, mock_platform_service
    ):
        """Test /ingestion/ingest requires propverify:ingest role"""
        mock_platform_service(200, {"ingestion_id": "ing-123"})

        with patch("app.middleware.auth.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "username": "test_user",
                "tenant_id": "test_tenant",
                "roles": ["propverify:ingest"],
            }

            with patch(
                "app.routers.propverify_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.post(
                    "/ingestion/ingest", json={"data": "test"}, headers=auth_headers
                )

                assert response.status_code == 200

    def test_ingest_url_requires_role(
        self, client, propverify_auth_headers, mock_httpx_client, mock_platform_service
    ):
        """Test /ingestion/ingest-url requires propverify:ingest role"""
        mock_platform_service(200, {"ingestion_id": "ing-123"})

        with patch("app.middleware.auth.require_role"):
            with patch(
                "app.routers.propverify_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.post(
                    "/ingestion/ingest-url",
                    json={"url": "https://example.com/data"},
                    headers=propverify_auth_headers,
                )

                assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.proxy
@pytest.mark.auth
class TestPropVerifyValidationProxy:
    """Test PropVerify validation service proxy"""

    def test_validate_requires_role(
        self, client, propverify_auth_headers, mock_httpx_client, mock_platform_service
    ):
        """Test /validation/validate requires propverify:validate role"""
        mock_platform_service(200, {"validation_id": "val-123", "results": []})

        with patch("app.middleware.auth.require_role"):
            with patch(
                "app.routers.propverify_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.post(
                    "/validation/validate", json={"data": "test"}, headers=propverify_auth_headers
                )

                assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.proxy
@pytest.mark.auth
class TestPropVerifyWorkflowProxy:
    """Test PropVerify workflow service proxy"""

    def test_execute_workflow_requires_role(
        self, client, propverify_auth_headers, mock_httpx_client, mock_platform_service
    ):
        """Test /workflow/execute-workflow requires propverify:workflow:execute role"""
        mock_platform_service(200, {"workflow_id": "wf-123", "status": "running"})

        with patch("app.middleware.auth.require_role"):
            with patch(
                "app.routers.propverify_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.post(
                    "/workflow/execute-workflow",
                    json={"workflow": "test"},
                    headers=propverify_auth_headers,
                )

                assert response.status_code == 200

    def test_approve_workflow_requires_role(
        self, client, propverify_auth_headers, mock_httpx_client, mock_platform_service
    ):
        """Test /workflow/approve/{approval_task_id} requires propverify:workflow:approve role"""
        mock_platform_service(200, {"status": "approved"})

        with patch("app.middleware.auth.require_role"):
            with patch(
                "app.routers.propverify_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.post(
                    "/workflow/approve/task-123", headers=propverify_auth_headers
                )

                assert response.status_code == 200

    def test_workflow_status(self, client, auth_headers, mock_httpx_client, mock_platform_service):
        """Test /workflow/status/{workflow_id}"""
        mock_platform_service(200, {"workflow_id": "wf-123", "status": "completed"})

        with patch("app.middleware.auth.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "username": "test_user",
                "tenant_id": "test_tenant",
                "roles": ["user"],
            }

            with patch(
                "app.routers.propverify_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.get("/workflow/status/wf-123", headers=auth_headers)

                assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.proxy
@pytest.mark.auth
class TestPropVerifyAIProxy:
    """Test PropVerify AI service proxy"""

    def test_ai_models(self, client, auth_headers, mock_httpx_client, mock_platform_service):
        """Test /ai-models"""
        mock_platform_service(200, {"models": ["model1", "model2"]})

        with patch("app.middleware.auth.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "username": "test_user",
                "tenant_id": "test_tenant",
                "roles": ["user"],
            }

            with patch(
                "app.routers.propverify_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.get("/ai-models", headers=auth_headers)

                assert response.status_code == 200

    def test_generate_requires_role(
        self, client, propverify_auth_headers, mock_httpx_client, mock_platform_service
    ):
        """Test /generate requires propverify:ai:generate role"""
        mock_platform_service(200, {"generated": "content"})

        with patch("app.middleware.auth.require_role"):
            with patch(
                "app.routers.propverify_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.post(
                    "/generate", json={"prompt": "test"}, headers=propverify_auth_headers
                )

                assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.proxy
@pytest.mark.auth
class TestPropVerifyLedgerProxy:
    """Test PropVerify ledger service proxy"""

    def test_anchor_hash_requires_role(
        self, client, propverify_auth_headers, mock_httpx_client, mock_platform_service
    ):
        """Test /ledger/anchor-hash requires propverify:ledger:anchor role"""
        mock_platform_service(200, {"txid": "tx-123"})

        with patch("app.middleware.auth.require_role"):
            with patch(
                "app.routers.propverify_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.post(
                    "/ledger/anchor-hash", json={"hash": "abc123"}, headers=propverify_auth_headers
                )

                assert response.status_code == 200

    def test_verify_anchor(self, client, auth_headers, mock_httpx_client, mock_platform_service):
        """Test /ledger/verify-anchor/{txid}"""
        mock_platform_service(200, {"valid": True})

        with patch("app.middleware.auth.get_current_user") as mock_auth:
            mock_auth.return_value = {
                "username": "test_user",
                "tenant_id": "test_tenant",
                "roles": ["user"],
            }

            with patch(
                "app.routers.propverify_proxy.httpx.AsyncClient", return_value=mock_httpx_client
            ):
                response = client.get("/ledger/verify-anchor/tx-123", headers=auth_headers)

                assert response.status_code == 200
