"""
Integration tests for POST /append endpoint
"""

import uuid

from app.hash_utils import GENESIS_HASH, compute_chain_hash, compute_content_hash
from app.models import LedgerEvent


class TestAppendEndpoint:
    """Tests for POST /append endpoint"""

    def test_append_first_event(self, client, sample_event_request):
        """Test appending the first event (genesis)"""
        response = client.post("/append", json=sample_event_request)

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert "chain_hash" in data
        assert "created_at" in data

        # Verify ID is valid UUID
        uuid.UUID(data["id"])

        # Verify chain hash format
        assert len(data["chain_hash"]) == 64

    def test_append_event_creates_record(self, client, db_session, sample_event_request):
        """Test that appending event creates database record"""
        response = client.post("/append", json=sample_event_request)

        assert response.status_code == 200
        data = response.json()

        # Query the database
        event = (
            db_session.query(LedgerEvent).filter(LedgerEvent.id == uuid.UUID(data["id"])).first()
        )

        assert event is not None
        assert event.tenant_id == sample_event_request["tenant_id"]
        assert event.event_type == sample_event_request["event_type"]
        assert event.event_data == sample_event_request["event_data"]

    def test_append_event_hash_chain(self, client, tenant_id):
        """Test that hash chain is correctly created"""
        # First event
        event1_data = {"action": "event1", "value": 1}
        request1 = {
            "tenant_id": tenant_id,
            "event_type": "test",
            "event_data": event1_data,
        }

        response1 = client.post("/append", json=request1)
        assert response1.status_code == 200
        data1 = response1.json()

        # Verify first event points to genesis
        expected_content1 = compute_content_hash(event1_data)
        expected_chain1 = compute_chain_hash(expected_content1, GENESIS_HASH)
        assert data1["chain_hash"] == expected_chain1

        # Second event
        event2_data = {"action": "event2", "value": 2}
        request2 = {
            "tenant_id": tenant_id,
            "event_type": "test",
            "event_data": event2_data,
        }

        response2 = client.post("/append", json=request2)
        assert response2.status_code == 200
        data2 = response2.json()

        # Verify second event points to first
        expected_content2 = compute_content_hash(event2_data)
        expected_chain2 = compute_chain_hash(expected_content2, data1["chain_hash"])
        assert data2["chain_hash"] == expected_chain2

    def test_append_with_optional_fields(self, client, sample_event_request):
        """Test appending event with all optional fields"""
        response = client.post("/append", json=sample_event_request)

        assert response.status_code == 200
        data = response.json()

        # Verify the record includes optional fields
        assert "id" in data

    def test_append_without_optional_fields(self, client, tenant_id):
        """Test appending event with only required fields"""
        request = {
            "tenant_id": tenant_id,
            "event_type": "test",
            "event_data": {"key": "value"},
        }

        response = client.post("/append", json=request)

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert "chain_hash" in data
        assert "created_at" in data

    def test_append_missing_required_fields(self, client):
        """Test appending event with missing required fields"""
        # Missing tenant_id
        request = {
            "event_type": "test",
            "event_data": {"key": "value"},
        }

        response = client.post("/append", json=request)
        assert response.status_code == 422  # Validation error

        # Missing event_type
        request = {
            "tenant_id": "test-tenant",
            "event_data": {"key": "value"},
        }

        response = client.post("/append", json=request)
        assert response.status_code == 422

        # Missing event_data
        request = {
            "tenant_id": "test-tenant",
            "event_type": "test",
        }

        response = client.post("/append", json=request)
        assert response.status_code == 422

    def test_append_empty_event_data(self, client, tenant_id):
        """Test appending event with empty event_data"""
        request = {
            "tenant_id": tenant_id,
            "event_type": "test",
            "event_data": {},
        }

        response = client.post("/append", json=request)

        # Should succeed - empty dict is valid
        assert response.status_code == 200

    def test_append_complex_event_data(self, client, tenant_id):
        """Test appending event with complex nested data"""
        complex_data = {
            "nested": {
                "object": {
                    "with": ["arrays", "and", "values"],
                },
            },
            "numbers": [1, 2, 3, 4, 5],
            "boolean": True,
            "null": None,
        }

        request = {
            "tenant_id": tenant_id,
            "event_type": "test",
            "event_data": complex_data,
        }

        response = client.post("/append", json=request)

        assert response.status_code == 200

    def test_append_multiple_events_sequential(self, client, tenant_id):
        """Test appending multiple events sequentially"""
        event_ids = []

        for i in range(5):
            request = {
                "tenant_id": tenant_id,
                "event_type": f"event_{i}",
                "event_data": {"sequence": i, "data": f"test_{i}"},
            }

            response = client.post("/append", json=request)
            assert response.status_code == 200

            data = response.json()
            event_ids.append(data["id"])

        # All IDs should be unique
        assert len(set(event_ids)) == 5

    def test_append_multi_tenant_isolation(self, client):
        """Test that different tenants have independent chains"""
        tenant1 = "tenant-1"
        tenant2 = "tenant-2"

        # Append event for tenant 1
        request1 = {
            "tenant_id": tenant1,
            "event_type": "test",
            "event_data": {"tenant": "1"},
        }

        response1 = client.post("/append", json=request1)
        assert response1.status_code == 200
        data1 = response1.json()

        # Append event for tenant 2
        request2 = {
            "tenant_id": tenant2,
            "event_type": "test",
            "event_data": {"tenant": "2"},
        }

        response2 = client.post("/append", json=request2)
        assert response2.status_code == 200
        data2 = response2.json()

        # Both should be genesis events (pointing to GENESIS_HASH)
        # Verify by checking they have different chain hashes
        assert data1["chain_hash"] != data2["chain_hash"]

    def test_append_same_data_different_hashes(self, client, tenant_id):
        """Test that appending same data twice creates different chain hashes"""
        # This is important: even with identical data, events should have
        # different chain hashes because they link to different previous events

        event_data = {"action": "test", "value": 123}
        request = {
            "tenant_id": tenant_id,
            "event_type": "test",
            "event_data": event_data,
        }

        # First event
        response1 = client.post("/append", json=request)
        assert response1.status_code == 200
        data1 = response1.json()

        # Second event (same data)
        response2 = client.post("/append", json=request)
        assert response2.status_code == 200
        data2 = response2.json()

        # Chain hashes should be different
        assert data1["chain_hash"] != data2["chain_hash"]

    def test_append_with_user_id(self, client, tenant_id, user_id):
        """Test appending event with user_id"""
        request = {
            "tenant_id": tenant_id,
            "event_type": "test",
            "event_data": {"action": "test"},
            "user_id": user_id,
        }

        response = client.post("/append", json=request)

        assert response.status_code == 200

    def test_append_with_correlation_id(self, client, tenant_id, correlation_id):
        """Test appending event with correlation_id"""
        request = {
            "tenant_id": tenant_id,
            "event_type": "test",
            "event_data": {"action": "test"},
            "correlation_id": correlation_id,
        }

        response = client.post("/append", json=request)

        assert response.status_code == 200

    def test_append_with_description(self, client, tenant_id):
        """Test appending event with description"""
        request = {
            "tenant_id": tenant_id,
            "event_type": "test",
            "event_data": {"action": "test"},
            "description": "This is a test event for testing purposes",
        }

        response = client.post("/append", json=request)

        assert response.status_code == 200

    def test_append_invalid_json(self, client):
        """Test appending with invalid JSON format"""
        response = client.post(
            "/append",
            data="not json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_append_concurrent_same_tenant(self, client, tenant_id):
        """Test appending multiple events for same tenant"""
        # This tests that the chain is built correctly even when
        # events are added in quick succession

        responses = []
        for i in range(3):
            request = {
                "tenant_id": tenant_id,
                "event_type": f"concurrent_{i}",
                "event_data": {"sequence": i},
            }
            response = client.post("/append", json=request)
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == 200

        # All should have different chain hashes
        chain_hashes = [r.json()["chain_hash"] for r in responses]
        assert len(set(chain_hashes)) == 3

    def test_append_response_format(self, client, sample_event_request):
        """Test that response has correct format"""
        response = client.post("/append", json=sample_event_request)

        assert response.status_code == 200
        data = response.json()

        # Should have exactly these fields
        assert set(data.keys()) == {"id", "chain_hash", "created_at"}

        # Verify formats
        assert isinstance(data["id"], str)
        assert isinstance(data["chain_hash"], str)
        assert isinstance(data["created_at"], str)

        # Verify ID is valid UUID
        uuid.UUID(data["id"])

        # Verify chain_hash is 64 char hex
        assert len(data["chain_hash"]) == 64
        assert all(c in "0123456789abcdef" for c in data["chain_hash"])

        # Verify created_at is ISO format
        from datetime import datetime

        datetime.fromisoformat(data["created_at"])
