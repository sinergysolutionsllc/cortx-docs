"""Integration tests for health check endpoints"""

from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test suite for health check endpoints"""

    def test_healthz_endpoint(self, client: TestClient):
        """Test /healthz endpoint returns 200 OK"""
        response = client.get("/healthz")
        assert response.status_code == 200

    def test_healthz_response_format(self, client: TestClient):
        """Test /healthz endpoint response format"""
        response = client.get("/healthz")
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_healthz_content_type(self, client: TestClient):
        """Test /healthz endpoint returns JSON content type"""
        response = client.get("/healthz")
        assert response.headers["content-type"] == "application/json"

    def test_readyz_endpoint(self, client: TestClient):
        """Test /readyz endpoint returns 200 OK"""
        response = client.get("/readyz")
        assert response.status_code == 200

    def test_readyz_response_format(self, client: TestClient):
        """Test /readyz endpoint response format"""
        response = client.get("/readyz")
        data = response.json()

        # Check all required fields are present
        assert "status" in data
        assert "vertex_ai" in data
        assert "project_configured" in data

        # Validate field values
        assert data["status"] == "ready"
        assert data["vertex_ai"] in ["available", "unavailable"]
        assert isinstance(data["project_configured"], bool)

    def test_readyz_mock_mode(self, client: TestClient):
        """Test /readyz endpoint in mock mode (no Vertex AI configured)"""
        response = client.get("/readyz")
        data = response.json()

        # In test environment, Vertex AI should be unavailable
        # and project should not be configured
        assert data["project_configured"] is False

    def test_readyz_content_type(self, client: TestClient):
        """Test /readyz endpoint returns JSON content type"""
        response = client.get("/readyz")
        assert response.headers["content-type"] == "application/json"

    def test_health_endpoints_no_auth_required(self, client: TestClient):
        """Test that health endpoints don't require authentication"""
        # These should work without any auth headers
        healthz_response = client.get("/healthz")
        assert healthz_response.status_code == 200

        readyz_response = client.get("/readyz")
        assert readyz_response.status_code == 200

    def test_healthz_idempotent(self, client: TestClient):
        """Test that /healthz is idempotent (multiple calls same result)"""
        responses = [client.get("/healthz") for _ in range(3)]
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["status"] == "ok" for r in responses)

    def test_readyz_idempotent(self, client: TestClient):
        """Test that /readyz is idempotent (multiple calls same result)"""
        responses = [client.get("/readyz") for _ in range(3)]
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["status"] == "ready" for r in responses)


class TestRootEndpoint:
    """Test suite for root / endpoint"""

    def test_root_endpoint(self, client: TestClient):
        """Test / endpoint returns service information"""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_response_format(self, client: TestClient):
        """Test / endpoint response format"""
        response = client.get("/")
        data = response.json()

        # Check all required fields
        assert "name" in data
        assert "version" in data
        assert "message" in data
        assert "features" in data

        # Validate field values
        assert data["name"] == "PropVerify AI Broker Service"
        assert isinstance(data["version"], str)
        assert isinstance(data["message"], str)
        assert isinstance(data["features"], list)

    def test_root_features_list(self, client: TestClient):
        """Test / endpoint returns expected features"""
        response = client.get("/")
        data = response.json()

        expected_features = ["text-generation", "embeddings", "function-calling", "streaming"]

        assert all(feature in data["features"] for feature in expected_features)

    def test_root_content_type(self, client: TestClient):
        """Test / endpoint returns JSON content type"""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"
