"""
Integration tests for Main API endpoints

Tests core application endpoints (health, root, info)
"""

import pytest


@pytest.mark.integration
class TestMainEndpoints:
    """Test main application endpoints"""

    def test_health_endpoint(self, client):
        """Test GET /health"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["ok"] is True

    def test_root_endpoint(self, client):
        """Test GET /"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "cortx-gateway"
        assert data["status"] == "ok"
        assert "env" in data

    def test_info_endpoint(self, client):
        """Test GET /_info"""
        response = client.get("/_info")

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "CORTX Gateway"
        assert data["version"] == "0.1.0"
        assert "routers" in data
        assert "features" in data

    def test_info_endpoint_routers(self, client):
        """Test info endpoint lists routers"""
        response = client.get("/_info")

        assert response.status_code == 200
        data = response.json()

        routers = data["routers"]
        assert "/orchestrator" in routers
        assert "/v1/rag" in routers
        assert "/v1/ocr" in routers
        assert "/v1/ledger" in routers
        assert "/v1/validation" in routers

    def test_info_endpoint_features(self, client):
        """Test info endpoint lists features"""
        response = client.get("/_info")

        assert response.status_code == 200
        data = response.json()

        features = data["features"]
        assert "RulePack orchestration" in features
        assert "Policy-based routing" in features
        assert "Multi-mode validation" in features
