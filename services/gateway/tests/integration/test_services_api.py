"""
Integration tests for Services API

Tests service discovery endpoint
"""

import pytest


@pytest.mark.integration
class TestServicesDiscovery:
    """Test GET /v1/services endpoint"""

    def test_get_services_list(self, client):
        """Test getting services list"""
        response = client.get("/v1/services")

        assert response.status_code == 200
        data = response.json()

        # Verify expected services are present
        assert "gateway" in data
        assert "fedsuite" in data
        assert "identity" in data

    def test_get_services_structure(self, client):
        """Test services response structure"""
        response = client.get("/v1/services")

        assert response.status_code == 200
        data = response.json()

        # Check service structure
        gateway = data["gateway"]
        assert "name" in gateway
        assert "url" in gateway
        assert "port" in gateway
        assert "status" in gateway

    def test_get_services_includes_planned_services(self, client):
        """Test response includes planned services"""
        response = client.get("/v1/services")

        assert response.status_code == 200
        data = response.json()

        # Verify planned services are marked appropriately
        assert "claimsuite" in data
        assert "govsuite" in data
        assert "medsuite" in data

    def test_get_services_port_configuration(self, client):
        """Test services use correct port configuration"""
        response = client.get("/v1/services")

        assert response.status_code == 200
        data = response.json()

        # Verify default ports
        assert data["gateway"]["port"] == 8000
        assert data["fedsuite"]["port"] == 8081
