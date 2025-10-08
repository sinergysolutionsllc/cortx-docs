"""
Integration tests for GET /events endpoint
"""



class TestEventsEndpoint:
    """Tests for GET /events endpoint"""

    def test_list_events_empty(self, client, tenant_id):
        """Test listing events for tenant with no events"""
        response = client.get(f"/events?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["events"] == []
        assert data["total"] == 0
        assert data["limit"] == 100
        assert data["offset"] == 0

    def test_list_single_event(self, client, ledger_event):
        """Test listing single event"""
        response = client.get(f"/events?tenant_id={ledger_event.tenant_id}")

        assert response.status_code == 200
        data = response.json()

        assert len(data["events"]) == 1
        assert data["total"] == 1

        event = data["events"][0]
        assert event["id"] == str(ledger_event.id)
        assert event["tenant_id"] == ledger_event.tenant_id
        assert event["event_type"] == ledger_event.event_type

    def test_list_multiple_events(self, client, ledger_chain, tenant_id):
        """Test listing multiple events"""
        response = client.get(f"/events?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()

        assert len(data["events"]) == 5
        assert data["total"] == 5

    def test_list_events_reverse_chronological(self, client, ledger_chain, tenant_id):
        """Test that events are returned newest first"""
        response = client.get(f"/events?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()

        events = data["events"]
        assert len(events) == 5

        # Check that events are in reverse chronological order
        # The last event created should be first in the list
        for i in range(len(events) - 1):
            # created_at should be descending
            assert events[i]["created_at"] >= events[i + 1]["created_at"]

    def test_list_events_pagination_limit(self, client, ledger_chain, tenant_id):
        """Test pagination with custom limit"""
        response = client.get(f"/events?tenant_id={tenant_id}&limit=2")

        assert response.status_code == 200
        data = response.json()

        assert len(data["events"]) == 2
        assert data["total"] == 5  # Total is still 5
        assert data["limit"] == 2
        assert data["offset"] == 0

    def test_list_events_pagination_offset(self, client, ledger_chain, tenant_id):
        """Test pagination with offset"""
        response = client.get(f"/events?tenant_id={tenant_id}&limit=2&offset=2")

        assert response.status_code == 200
        data = response.json()

        assert len(data["events"]) == 2
        assert data["total"] == 5
        assert data["limit"] == 2
        assert data["offset"] == 2

    def test_list_events_pagination_last_page(self, client, ledger_chain, tenant_id):
        """Test pagination on last page with fewer items"""
        response = client.get(f"/events?tenant_id={tenant_id}&limit=3&offset=3")

        assert response.status_code == 200
        data = response.json()

        assert len(data["events"]) == 2  # Only 2 events left
        assert data["total"] == 5
        assert data["limit"] == 3
        assert data["offset"] == 3

    def test_list_events_pagination_beyond_end(self, client, ledger_chain, tenant_id):
        """Test pagination beyond available events"""
        response = client.get(f"/events?tenant_id={tenant_id}&limit=10&offset=10")

        assert response.status_code == 200
        data = response.json()

        assert len(data["events"]) == 0
        assert data["total"] == 5
        assert data["offset"] == 10

    def test_list_events_filter_by_type(self, client, ledger_chain, tenant_id):
        """Test filtering events by event_type"""
        response = client.get(f"/events?tenant_id={tenant_id}&event_type=event_type_0")

        assert response.status_code == 200
        data = response.json()

        assert len(data["events"]) == 1
        assert data["total"] == 1
        assert data["events"][0]["event_type"] == "event_type_0"

    def test_list_events_filter_by_correlation(self, client, ledger_chain, tenant_id):
        """Test filtering events by correlation_id"""
        response = client.get(f"/events?tenant_id={tenant_id}&correlation_id=corr_0")

        assert response.status_code == 200
        data = response.json()

        assert len(data["events"]) == 1
        assert data["total"] == 1
        assert data["events"][0]["correlation_id"] == "corr_0"

    def test_list_events_filter_no_matches(self, client, ledger_chain, tenant_id):
        """Test filtering with no matching events"""
        response = client.get(f"/events?tenant_id={tenant_id}&event_type=nonexistent")

        assert response.status_code == 200
        data = response.json()

        assert len(data["events"]) == 0
        assert data["total"] == 0

    def test_list_events_multi_tenant_isolation(self, client, multi_tenant_events):
        """Test that events are isolated by tenant"""
        # List events for tenant-a
        response = client.get("/events?tenant_id=tenant-a")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert all(e["tenant_id"] == "tenant-a" for e in data["events"])

        # List events for tenant-b
        response = client.get("/events?tenant_id=tenant-b")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(e["tenant_id"] == "tenant-b" for e in data["events"])

    def test_list_events_missing_tenant_id(self, client):
        """Test listing events without tenant_id parameter"""
        response = client.get("/events")

        assert response.status_code == 422  # Validation error

    def test_list_events_nonexistent_tenant(self, client):
        """Test listing events for nonexistent tenant"""
        response = client.get("/events?tenant_id=nonexistent")

        assert response.status_code == 200
        data = response.json()

        assert data["events"] == []
        assert data["total"] == 0

    def test_list_events_response_format(self, client, ledger_event):
        """Test that event response has correct format"""
        response = client.get(f"/events?tenant_id={ledger_event.tenant_id}")

        assert response.status_code == 200
        data = response.json()

        event = data["events"][0]

        # Check all required fields
        assert "id" in event
        assert "tenant_id" in event
        assert "event_type" in event
        assert "event_data" in event
        assert "created_at" in event
        assert "content_hash" in event
        assert "previous_hash" in event
        assert "chain_hash" in event
        assert "user_id" in event
        assert "correlation_id" in event
        assert "description" in event

        # Verify types
        assert isinstance(event["id"], str)
        assert isinstance(event["tenant_id"], str)
        assert isinstance(event["event_type"], str)
        assert isinstance(event["event_data"], dict)
        assert isinstance(event["created_at"], str)
        assert isinstance(event["content_hash"], str)
        assert isinstance(event["previous_hash"], str)
        assert isinstance(event["chain_hash"], str)

    def test_list_events_includes_event_data(self, client, ledger_event):
        """Test that event_data is included in response"""
        response = client.get(f"/events?tenant_id={ledger_event.tenant_id}")

        assert response.status_code == 200
        data = response.json()

        event = data["events"][0]
        assert event["event_data"] == ledger_event.event_data

    def test_list_events_limit_validation_min(self, client, tenant_id):
        """Test that limit has minimum value of 1"""
        response = client.get(f"/events?tenant_id={tenant_id}&limit=0")

        assert response.status_code == 422  # Validation error

    def test_list_events_limit_validation_max(self, client, tenant_id):
        """Test that limit has maximum value of 1000"""
        response = client.get(f"/events?tenant_id={tenant_id}&limit=1001")

        assert response.status_code == 422  # Validation error

    def test_list_events_offset_validation(self, client, tenant_id):
        """Test that offset must be >= 0"""
        response = client.get(f"/events?tenant_id={tenant_id}&offset=-1")

        assert response.status_code == 422  # Validation error

    def test_list_events_default_limit(self, client, tenant_id):
        """Test default limit is 100"""
        response = client.get(f"/events?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 100

    def test_list_events_default_offset(self, client, tenant_id):
        """Test default offset is 0"""
        response = client.get(f"/events?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["offset"] == 0

    def test_list_events_after_append(self, client, tenant_id):
        """Test listing events after appending"""
        # Append 3 events
        for i in range(3):
            request = {
                "tenant_id": tenant_id,
                "event_type": "test",
                "event_data": {"sequence": i},
            }
            client.post("/append", json=request)

        # List events
        response = client.get(f"/events?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 3
        assert len(data["events"]) == 3

    def test_list_events_pagination_consistency(self, client, ledger_chain, tenant_id):
        """Test that pagination returns consistent results"""
        # Get first page
        response1 = client.get(f"/events?tenant_id={tenant_id}&limit=2&offset=0")
        data1 = response1.json()

        # Get second page
        response2 = client.get(f"/events?tenant_id={tenant_id}&limit=2&offset=2")
        data2 = response2.json()

        # No overlap between pages
        ids_page1 = {e["id"] for e in data1["events"]}
        ids_page2 = {e["id"] for e in data2["events"]}
        assert len(ids_page1.intersection(ids_page2)) == 0

    def test_list_events_filter_combined(self, client, db_session, tenant_id):
        """Test filtering by multiple criteria"""
        from app.hash_utils import GENESIS_HASH, compute_chain_hash, compute_content_hash
        from app.models import LedgerEvent

        # Create events with specific correlation_id and event_type
        previous_hash = GENESIS_HASH
        for i in range(3):
            event_data = {"sequence": i}
            content_hash = compute_content_hash(event_data)
            chain_hash = compute_chain_hash(content_hash, previous_hash)

            event = LedgerEvent(
                tenant_id=tenant_id,
                event_type="test_type",
                event_data=event_data,
                content_hash=content_hash,
                previous_hash=previous_hash,
                chain_hash=chain_hash,
                correlation_id="test_correlation",
            )

            db_session.add(event)
            previous_hash = chain_hash

        db_session.commit()

        # Filter by both event_type and correlation_id
        response = client.get(
            f"/events?tenant_id={tenant_id}&event_type=test_type&correlation_id=test_correlation"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 3
        assert all(e["event_type"] == "test_type" for e in data["events"])
        assert all(e["correlation_id"] == "test_correlation" for e in data["events"])
