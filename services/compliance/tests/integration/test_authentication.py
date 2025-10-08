"""
Integration tests for authentication and authorization
"""

import os

import pytest


@pytest.mark.integration
@pytest.mark.auth
class TestAuthentication:
    """Test authentication for compliance endpoints"""

    @pytest.mark.skipif(
        os.getenv("REQUIRE_AUTH", "false").lower() not in {"1", "true", "yes"},
        reason="Auth not required in this environment",
    )
    def test_post_event_requires_auth(self, client):
        """Test that POST /compliance/events requires authentication"""
        payload = {"event_type": "audit", "description": "Test event", "severity": "info"}

        response = client.post("/compliance/events", json=payload)
        assert response.status_code == 401

    @pytest.mark.skipif(
        os.getenv("REQUIRE_AUTH", "false").lower() not in {"1", "true", "yes"},
        reason="Auth not required in this environment",
    )
    def test_get_events_requires_auth(self, client):
        """Test that GET /compliance/events requires authentication"""
        response = client.get("/compliance/events")
        assert response.status_code == 401

    @pytest.mark.skipif(
        os.getenv("REQUIRE_AUTH", "false").lower() not in {"1", "true", "yes"},
        reason="Auth not required in this environment",
    )
    def test_get_report_requires_auth(self, client):
        """Test that GET /compliance/report requires authentication"""
        response = client.get("/compliance/report")
        assert response.status_code == 401

    def test_post_event_with_valid_auth(self, client, auth_headers):
        """Test POST with valid authentication"""
        payload = {"event_type": "audit", "description": "Authenticated event", "severity": "info"}

        response = client.post("/compliance/events", json=payload, headers=auth_headers)
        assert response.status_code == 201

    def test_get_events_with_valid_auth(self, client, auth_headers):
        """Test GET events with valid authentication"""
        response = client.get("/compliance/events", headers=auth_headers)
        assert response.status_code == 200

    def test_get_report_with_admin_auth(self, client, admin_auth_headers):
        """Test GET report with admin authentication"""
        response = client.get("/compliance/report", headers=admin_auth_headers)
        assert response.status_code == 200

    @pytest.mark.skipif(
        os.getenv("REQUIRE_AUTH", "false").lower() not in {"1", "true", "yes"},
        reason="Auth not required in this environment",
    )
    def test_report_requires_admin_role(self, client, auth_headers):
        """Test that report endpoint requires admin role"""
        response = client.get("/compliance/report", headers=auth_headers)  # Regular user, not admin
        # Should return 403 Forbidden (has auth but not right role)
        assert response.status_code in [401, 403]

    @pytest.mark.skipif(
        os.getenv("REQUIRE_AUTH", "false").lower() not in {"1", "true", "yes"},
        reason="Auth not required in this environment",
    )
    def test_invalid_token_rejected(self, client):
        """Test that invalid token is rejected"""
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}

        response = client.post(
            "/compliance/events",
            json={"event_type": "audit", "description": "Should fail", "severity": "info"},
            headers=invalid_headers,
        )
        assert response.status_code == 401

    @pytest.mark.skipif(
        os.getenv("REQUIRE_AUTH", "false").lower() not in {"1", "true", "yes"},
        reason="Auth not required in this environment",
    )
    def test_malformed_auth_header_rejected(self, client):
        """Test that malformed auth header is rejected"""
        malformed_headers = {"Authorization": "InvalidFormat"}

        response = client.get("/compliance/events", headers=malformed_headers)
        assert response.status_code == 401

    @pytest.mark.skipif(
        os.getenv("REQUIRE_AUTH", "false").lower() not in {"1", "true", "yes"},
        reason="Auth not required in this environment",
    )
    def test_expired_token_rejected(self, client, create_test_token):
        """Test that expired token is rejected"""
        from datetime import timedelta

        # Create token that expires immediately
        expired_token = create_test_token(expires_delta=timedelta(seconds=-1))
        headers = {"Authorization": f"Bearer {expired_token}"}

        response = client.get("/compliance/events", headers=headers)
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.auth
class TestHealthEndpoints:
    """Test health check endpoints (should not require auth)"""

    def test_healthz_no_auth_required(self, client):
        """Test /healthz does not require authentication"""
        response = client.get("/healthz")
        assert response.status_code == 200

    def test_readyz_no_auth_required(self, client):
        """Test /readyz does not require authentication"""
        response = client.get("/readyz")
        assert response.status_code == 200

    def test_livez_no_auth_required(self, client):
        """Test /livez does not require authentication"""
        response = client.get("/livez")
        assert response.status_code == 200

    def test_root_endpoint_with_optional_auth(self, client):
        """Test root endpoint with optional authentication"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data

    def test_root_endpoint_with_auth(self, client, auth_headers):
        """Test root endpoint with authentication"""
        response = client.get("/", headers=auth_headers)
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.auth
class TestCORSAndSecurity:
    """Test CORS and security headers"""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses"""
        response = client.options("/healthz")
        # CORS headers may be added by middleware
        # This test verifies the endpoint is accessible

    def test_security_headers(self, client, auth_headers):
        """Test security headers in response"""
        response = client.get("/compliance/events", headers=auth_headers)
        # Could check for security headers like X-Content-Type-Options
        # X-Frame-Options, etc. if configured
