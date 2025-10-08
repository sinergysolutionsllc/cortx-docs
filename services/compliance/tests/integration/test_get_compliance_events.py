"""
Integration tests for GET /compliance/events endpoint
"""

import os

import pytest
from tests.__utils__.helpers import validate_correlation_id


@pytest.mark.integration
class TestGetComplianceEvents:
    """Test GET /compliance/events endpoint"""

    def test_get_all_events(self, client, auth_headers, populated_compliance_events):
        """Test retrieving all compliance events"""
        response = client.get("/compliance/events", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "count" in data
        assert "total" in data
        assert validate_correlation_id(data)
        assert isinstance(data["events"], list)
        assert data["count"] == len(data["events"])

    def test_get_events_empty_list(self, client, auth_headers):
        """Test retrieving events when none exist"""
        response = client.get("/compliance/events", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []
        assert data["count"] == 0
        assert data["total"] == 0

    def test_get_events_after_posting(self, client, auth_headers):
        """Test retrieving events after posting some"""
        # Post events
        for i in range(3):
            payload = {"event_type": "audit", "description": f"Test event {i}", "severity": "info"}
            post_response = client.post("/compliance/events", json=payload, headers=auth_headers)
            assert post_response.status_code == 201

        # Get events
        response = client.get("/compliance/events", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert len(data["events"]) == 3

    def test_get_events_sorted_by_timestamp(
        self, client, auth_headers, populated_compliance_events
    ):
        """Test that events are sorted by timestamp (newest first)"""
        response = client.get("/compliance/events", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        events = data["events"]

        if len(events) > 1:
            timestamps = [e["timestamp"] for e in events]
            assert timestamps == sorted(timestamps, reverse=True)

    def test_filter_events_by_type(self, client, auth_headers, populated_compliance_events):
        """Test filtering events by type"""
        response = client.get("/compliance/events?type=audit", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "events" in data

        # Verify all returned events are audit type
        for event in data["events"]:
            assert event["event_type"] == "audit"

    def test_filter_events_by_violation_type(
        self, client, auth_headers, populated_compliance_events
    ):
        """Test filtering events by violation type"""
        response = client.get("/compliance/events?type=violation", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        for event in data["events"]:
            assert event["event_type"] == "violation"

    def test_filter_events_by_nonexistent_type(
        self, client, auth_headers, populated_compliance_events
    ):
        """Test filtering by non-existent event type"""
        response = client.get("/compliance/events?type=nonexistent", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []
        assert data["count"] == 0

    def test_get_events_with_limit(self, client, auth_headers, populated_compliance_events):
        """Test limiting number of returned events"""
        limit = 2
        response = client.get(f"/compliance/events?limit={limit}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) <= limit

    def test_get_events_default_limit(self, client, auth_headers):
        """Test default limit behavior"""
        # Post more than default limit
        for i in range(10):
            payload = {"event_type": "audit", "description": f"Event {i}", "severity": "info"}
            client.post("/compliance/events", json=payload, headers=auth_headers)

        response = client.get("/compliance/events", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 10  # Should return all

    def test_get_events_large_limit(self, client, auth_headers, populated_compliance_events):
        """Test with very large limit"""
        response = client.get("/compliance/events?limit=1000", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        # Should return all available events

    def test_get_events_zero_limit(self, client, auth_headers, populated_compliance_events):
        """Test with zero limit"""
        response = client.get("/compliance/events?limit=0", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert len(data["events"]) == 0

    def test_get_events_invalid_limit(self, client, auth_headers):
        """Test with invalid limit parameter"""
        response = client.get("/compliance/events?limit=invalid", headers=auth_headers)

        # Should handle gracefully (422 validation error or use default)
        assert response.status_code in [200, 422]

    @pytest.mark.skipif(
        os.getenv("REQUIRE_AUTH", "false").lower() not in {"1", "true", "yes"},
        reason="Auth not required in this environment",
    )
    def test_get_events_without_auth(self, client):
        """Test retrieving events without authentication"""
        response = client.get("/compliance/events")
        assert response.status_code == 401

    def test_get_events_response_structure(self, client, auth_headers, populated_compliance_events):
        """Test response structure contains required fields"""
        response = client.get("/compliance/events", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Check top-level structure
        assert "events" in data
        assert "count" in data
        assert "total" in data
        assert "correlation_id" in data

        # Check event structure
        if len(data["events"]) > 0:
            event = data["events"][0]
            assert "event_id" in event
            assert "event_type" in event
            assert "description" in event
            assert "data" in event
            assert "user_id" in event
            assert "severity" in event
            assert "correlation_id" in event
            assert "timestamp" in event
            assert "data_hash" in event

    def test_get_events_count_matches_length(
        self, client, auth_headers, populated_compliance_events
    ):
        """Test that count field matches actual event list length"""
        response = client.get("/compliance/events", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == len(data["events"])

    def test_get_events_combined_filters(self, client, auth_headers):
        """Test combining type filter and limit"""
        # Post mixed events
        for i in range(5):
            client.post(
                "/compliance/events",
                json={"event_type": "audit", "description": f"Audit {i}", "severity": "info"},
                headers=auth_headers,
            )
        for i in range(3):
            client.post(
                "/compliance/events",
                json={
                    "event_type": "violation",
                    "description": f"Violation {i}",
                    "severity": "high",
                },
                headers=auth_headers,
            )

        response = client.get("/compliance/events?type=audit&limit=3", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) <= 3
        for event in data["events"]:
            assert event["event_type"] == "audit"

    def test_get_events_preserves_data(self, client, auth_headers):
        """Test that retrieved events preserve original data"""
        original_data = {"key1": "value1", "nested": {"inner": "data"}, "array": [1, 2, 3]}

        # Post event
        post_response = client.post(
            "/compliance/events",
            json={
                "event_type": "audit",
                "description": "Data preservation test",
                "data": original_data,
                "severity": "info",
            },
            headers=auth_headers,
        )
        event_id = post_response.json()["event_id"]

        # Get events
        get_response = client.get("/compliance/events", headers=auth_headers)

        assert get_response.status_code == 200
        data = get_response.json()

        # Find the posted event
        posted_event = next((e for e in data["events"] if e["event_id"] == event_id), None)
        assert posted_event is not None
        assert posted_event["data"] == original_data
