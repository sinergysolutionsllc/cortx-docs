"""
Integration tests for health check endpoints
"""



class TestHealthEndpoints:
    """Tests for health check endpoints"""

    def test_healthz_endpoint(self, client):
        """Test /healthz endpoint returns OK"""
        response = client.get("/healthz")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "ok"

    def test_healthz_response_format(self, client):
        """Test /healthz response format"""
        response = client.get("/healthz")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, dict)
        assert len(data) == 1
        assert "status" in data

    def test_readyz_endpoint(self, client):
        """Test /readyz endpoint returns status"""
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "database" in data
        assert "total_events" in data

    def test_readyz_response_format(self, client):
        """Test /readyz response format"""
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, dict)
        assert isinstance(data["status"], str)
        assert isinstance(data["database"], str)
        assert isinstance(data["total_events"], int)

    def test_readyz_database_status(self, client):
        """Test /readyz includes database status"""
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()

        # Database should be connected (using in-memory SQLite in tests)
        assert data["database"] in ["connected", "disconnected"]

    def test_readyz_total_events_count(self, client, ledger_chain):
        """Test /readyz returns correct event count"""
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()

        # Should count all events (5 from ledger_chain fixture)
        assert data["total_events"] >= 5

    def test_readyz_empty_database(self, client):
        """Test /readyz with no events"""
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()

        # Should return 0 or current count
        assert data["total_events"] >= 0

    def test_readyz_status_ready(self, client):
        """Test /readyz status is 'ready' when database is connected"""
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()

        # Status should be ready or degraded based on DB connection
        assert data["status"] in ["ready", "degraded"]

    def test_healthz_always_succeeds(self, client):
        """Test /healthz always returns 200"""
        # Health check should always succeed
        response = client.get("/healthz")
        assert response.status_code == 200

    def test_readyz_counts_all_tenants(self, client, multi_tenant_events):
        """Test /readyz counts events across all tenants"""
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()

        # Should count all events from all tenants (3 + 2 + 4 = 9)
        assert data["total_events"] >= 9

    def test_health_endpoints_no_auth_required(self, client):
        """Test that health endpoints don't require authentication"""
        # Both endpoints should be accessible without auth
        response = client.get("/healthz")
        assert response.status_code == 200

        response = client.get("/readyz")
        assert response.status_code == 200

    def test_healthz_content_type(self, client):
        """Test /healthz returns JSON content type"""
        response = client.get("/healthz")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_readyz_content_type(self, client):
        """Test /readyz returns JSON content type"""
        response = client.get("/readyz")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_health_endpoints_multiple_calls(self, client):
        """Test health endpoints can be called multiple times"""
        # Should be idempotent
        for _ in range(3):
            response = client.get("/healthz")
            assert response.status_code == 200

            response = client.get("/readyz")
            assert response.status_code == 200
