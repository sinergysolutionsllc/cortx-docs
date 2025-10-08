"""Integration tests for health and meta endpoints."""



class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_healthz_endpoint(self, client):
        """Test /healthz liveness endpoint."""
        response = client.get("/healthz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_readyz_endpoint(self, client):
        """Test /readyz readiness endpoint."""
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_livez_endpoint(self, client):
        """Test /livez alias endpoint."""
        response = client.get("/livez")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_health_endpoints_no_auth_required(self, client):
        """Test that health endpoints don't require authentication."""
        # These should all work without auth headers
        endpoints = ["/healthz", "/readyz", "/livez"]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200


class TestMetaEndpoints:
    """Test meta/info endpoints."""

    def test_index_endpoint(self, client, auth_headers):
        """Test / index endpoint."""
        response = client.get("/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "PropVerify Workflow Service" in data["name"]

    def test_index_endpoint_without_auth(self, client):
        """Test / index endpoint without authentication."""
        response = client.get("/")

        # Should succeed in test mode
        assert response.status_code == 200

    def test_workflow_status_endpoint(self, client, auth_headers, mock_cortx_client):
        """Test /workflow-status integration endpoint."""
        # Mock gateway response
        mock_cortx_client.get_json.return_value = {
            "status": "operational",
            "services": ["workflow", "compiler"],
        }

        response = client.get("/workflow-status", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "workflow" in data

    def test_workflow_status_gateway_unavailable(self, client, auth_headers, mock_cortx_client):
        """Test /workflow-status when gateway is unavailable."""
        # Mock gateway failure
        mock_cortx_client.get_json.side_effect = Exception("Gateway down")

        response = client.get("/workflow-status", headers=auth_headers)

        assert response.status_code == 503
        data = response.json()
        assert "error" in data


class TestServiceInfo:
    """Test service information and metadata."""

    def test_service_name_and_version(self, client):
        """Test that service returns correct name and version."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "PropVerify Workflow Service"
        assert "version" in data
        assert len(data["version"]) > 0

    def test_service_message(self, client):
        """Test service informational message."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "CORTX" in data["message"]
