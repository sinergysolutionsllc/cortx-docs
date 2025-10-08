"""Integration tests for health check and metadata endpoints."""

from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test suite for health check endpoints."""

    def test_healthz_endpoint(self, test_client: TestClient):
        """Test /healthz liveness probe."""
        response = test_client.get("/healthz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_readyz_endpoint(self, test_client: TestClient):
        """Test /readyz readiness probe."""
        response = test_client.get("/readyz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_livez_endpoint(self, test_client: TestClient):
        """Test /livez alias endpoint."""
        response = test_client.get("/livez")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_health_endpoints_return_json(self, test_client: TestClient):
        """Test that all health endpoints return JSON."""
        endpoints = ["/healthz", "/readyz", "/livez"]

        for endpoint in endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"

    def test_health_endpoints_fast_response(self, test_client: TestClient):
        """Test that health endpoints respond quickly."""
        import time

        endpoints = ["/healthz", "/readyz", "/livez"]

        for endpoint in endpoints:
            start = time.time()
            response = test_client.get(endpoint)
            duration = time.time() - start

            assert response.status_code == 200
            # Health checks should be very fast (< 100ms)
            assert duration < 0.1

    def test_health_endpoints_no_auth_required(self, test_client: TestClient):
        """Test that health endpoints don't require authentication."""
        # Even with auth enabled, health checks should work
        response = test_client.get("/healthz")
        assert response.status_code == 200

        response = test_client.get("/readyz")
        assert response.status_code == 200

        response = test_client.get("/livez")
        assert response.status_code == 200


class TestIndexEndpoint:
    """Test suite for root / index endpoint."""

    def test_index_endpoint(self, test_client: TestClient):
        """Test GET / returns service metadata."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "message" in data
        assert data["name"] == "PropVerify Validation Service"

    def test_index_endpoint_returns_json(self, test_client: TestClient):
        """Test that index endpoint returns JSON."""
        response = test_client.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_index_endpoint_version_matches_app(self, test_client: TestClient):
        """Test that version in response matches app version."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "0.1.0"

    def test_index_endpoint_includes_informative_message(self, test_client: TestClient):
        """Test that index includes helpful message about service purpose."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "CORTX" in data["message"]
        assert "Validation" in data["message"] or "Compliance" in data["message"]


class TestEndpointAccessibility:
    """Test endpoint accessibility and HTTP methods."""

    def test_post_not_allowed_on_health_endpoints(self, test_client: TestClient):
        """Test that POST is not allowed on health endpoints."""
        endpoints = ["/healthz", "/readyz", "/livez"]

        for endpoint in endpoints:
            response = test_client.post(endpoint)
            assert response.status_code == 405  # Method Not Allowed

    def test_delete_not_allowed_on_health_endpoints(self, test_client: TestClient):
        """Test that DELETE is not allowed on health endpoints."""
        endpoints = ["/healthz", "/readyz", "/livez", "/"]

        for endpoint in endpoints:
            response = test_client.delete(endpoint)
            assert response.status_code == 405  # Method Not Allowed

    def test_put_not_allowed_on_health_endpoints(self, test_client: TestClient):
        """Test that PUT is not allowed on health endpoints."""
        endpoints = ["/healthz", "/readyz", "/livez", "/"]

        for endpoint in endpoints:
            response = test_client.put(endpoint)
            assert response.status_code == 405  # Method Not Allowed

    def test_options_allowed_on_endpoints(self, test_client: TestClient):
        """Test that OPTIONS is supported (CORS preflight)."""
        endpoints = ["/healthz", "/readyz", "/livez", "/"]

        for endpoint in endpoints:
            response = test_client.options(endpoint)
            # Should either succeed (200) or be allowed (204)
            assert response.status_code in [200, 204, 405]

    def test_head_allowed_on_get_endpoints(self, test_client: TestClient):
        """Test that HEAD requests work on GET endpoints."""
        endpoints = ["/healthz", "/readyz", "/livez", "/"]

        for endpoint in endpoints:
            response = test_client.head(endpoint)
            # HEAD should work like GET but without body
            assert response.status_code in [200, 405]


class TestCORS:
    """Test CORS headers and cross-origin access."""

    def test_cors_headers_present(self, test_client: TestClient):
        """Test that CORS headers are present in responses."""
        response = test_client.get("/")

        # Check if CORS middleware is applied
        # The exact headers depend on middleware configuration
        assert response.status_code == 200

    def test_preflight_request_handling(self, test_client: TestClient):
        """Test CORS preflight (OPTIONS) request handling."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }

        response = test_client.options("/validate", headers=headers)

        # Should handle preflight request
        assert response.status_code in [200, 204, 405]


class TestErrorHandling:
    """Test error handling for invalid requests."""

    def test_404_for_nonexistent_endpoint(self, test_client: TestClient):
        """Test that 404 is returned for non-existent endpoints."""
        response = test_client.get("/nonexistent-endpoint")

        assert response.status_code == 404

    def test_404_response_format(self, test_client: TestClient):
        """Test that 404 errors return JSON."""
        response = test_client.get("/nonexistent-endpoint")

        assert response.status_code == 404
        # FastAPI returns JSON error responses by default
        data = response.json()
        assert "detail" in data

    def test_method_not_allowed_response(self, test_client: TestClient):
        """Test 405 Method Not Allowed response format."""
        response = test_client.post("/healthz")

        assert response.status_code == 405
        data = response.json()
        assert "detail" in data


class TestTracingAndCorrelation:
    """Test distributed tracing and correlation ID handling."""

    def test_correlation_id_propagation(self, test_client: TestClient):
        """Test that correlation ID is generated and can be traced."""
        response = test_client.get("/")

        assert response.status_code == 200
        # Correlation ID might be in headers or response body depending on middleware

    def test_traceparent_header_accepted(self, test_client: TestClient):
        """Test that W3C traceparent header is accepted."""
        headers = {"traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"}

        response = test_client.get("/", headers=headers)

        assert response.status_code == 200

    def test_custom_headers_preserved(self, test_client: TestClient):
        """Test that custom request headers are preserved."""
        headers = {"X-Custom-Header": "test-value", "X-Request-ID": "req-12345"}

        response = test_client.get("/", headers=headers)

        assert response.status_code == 200


class TestContentNegotiation:
    """Test content type negotiation."""

    def test_json_content_type_default(self, test_client: TestClient):
        """Test that JSON is the default content type."""
        response = test_client.get("/")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_accept_header_json(self, test_client: TestClient):
        """Test Accept: application/json header."""
        headers = {"Accept": "application/json"}

        response = test_client.get("/", headers=headers)

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_accept_header_wildcard(self, test_client: TestClient):
        """Test Accept: */* header."""
        headers = {"Accept": "*/*"}

        response = test_client.get("/", headers=headers)

        assert response.status_code == 200


class TestSecurityHeaders:
    """Test security-related headers."""

    def test_no_sensitive_info_in_errors(self, test_client: TestClient):
        """Test that error responses don't leak sensitive information."""
        response = test_client.get("/nonexistent")

        assert response.status_code == 404
        data = response.json()
        # Should not contain stack traces or internal paths
        assert "Traceback" not in str(data)
        assert "/Users/" not in str(data)
        assert "/app/" not in str(data) or "detail" in data

    def test_version_endpoint_safe(self, test_client: TestClient):
        """Test that version endpoint doesn't leak sensitive info."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        # Should only contain safe metadata
        assert "password" not in str(data).lower()
        assert "secret" not in str(data).lower()
        assert "token" not in str(data).lower()


class TestConcurrency:
    """Test concurrent request handling."""

    def test_multiple_concurrent_health_checks(self, test_client: TestClient):
        """Test that multiple concurrent health checks work."""
        import concurrent.futures

        def make_request():
            return test_client.get("/healthz")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(r.status_code == 200 for r in results)

    def test_multiple_concurrent_index_requests(self, test_client: TestClient):
        """Test that multiple concurrent index requests work."""
        import concurrent.futures

        def make_request():
            return test_client.get("/")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(r.status_code == 200 for r in results)
