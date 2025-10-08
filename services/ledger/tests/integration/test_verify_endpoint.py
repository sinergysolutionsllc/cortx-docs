"""
Integration tests for GET /verify endpoint
"""


from app.hash_utils import compute_chain_hash, compute_content_hash


class TestVerifyEndpoint:
    """Tests for GET /verify endpoint"""

    def test_verify_empty_chain(self, client, tenant_id):
        """Test verifying a tenant with no events"""
        response = client.get(f"/verify?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["total_events"] == 0
        assert data["error"] is None

    def test_verify_single_event(self, client, ledger_event):
        """Test verifying a chain with single event"""
        response = client.get(f"/verify?tenant_id={ledger_event.tenant_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["total_events"] == 1
        assert data["error"] is None

    def test_verify_valid_chain(self, client, ledger_chain, tenant_id):
        """Test verifying a valid chain of events"""
        response = client.get(f"/verify?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["total_events"] == 5
        assert data["error"] is None

    def test_verify_tampered_content(self, client, db_session, tampered_event):
        """Test detecting tampered event data"""
        response = client.get(f"/verify?tenant_id={tampered_event.tenant_id}")

        assert response.status_code == 200
        data = response.json()

        # Should detect tampering
        assert data["valid"] is False
        assert data["total_events"] == 5
        assert data["error"] is not None
        assert "Content hash mismatch" in data["error"]
        assert str(tampered_event.id) in data["error"]

    def test_verify_tampered_chain_hash(self, client, db_session, ledger_chain):
        """Test detecting tampered chain hash"""
        # Tamper with chain hash of middle event
        event = ledger_chain[2]
        event.chain_hash = "a" * 64  # Invalid chain hash

        db_session.commit()
        db_session.refresh(event)

        response = client.get(f"/verify?tenant_id={event.tenant_id}")

        assert response.status_code == 200
        data = response.json()

        # Should detect tampering
        assert data["valid"] is False
        assert "Chain hash mismatch" in data["error"]

    def test_verify_broken_chain_link(self, client, db_session, ledger_chain):
        """Test detecting broken chain link (previous_hash doesn't match)"""
        # Break the chain by modifying previous_hash of third event
        event = ledger_chain[2]
        event.previous_hash = "b" * 64  # Wrong previous hash

        db_session.commit()
        db_session.refresh(event)

        response = client.get(f"/verify?tenant_id={event.tenant_id}")

        assert response.status_code == 200
        data = response.json()

        # Should detect broken chain
        assert data["valid"] is False
        assert "Chain broken" in data["error"] or "Chain hash mismatch" in data["error"]

    def test_verify_invalid_genesis(self, client, db_session, ledger_chain):
        """Test detecting when first event doesn't point to genesis"""
        # Modify first event's previous_hash
        first_event = ledger_chain[0]
        first_event.previous_hash = "a" * 64  # Not GENESIS_HASH

        db_session.commit()
        db_session.refresh(first_event)

        response = client.get(f"/verify?tenant_id={first_event.tenant_id}")

        assert response.status_code == 200
        data = response.json()

        # Should detect invalid genesis
        assert data["valid"] is False
        assert "doesn't point to genesis" in data["error"] or "Chain hash mismatch" in data["error"]

    def test_verify_multi_tenant_isolation(self, client, multi_tenant_events):
        """Test that verification is isolated per tenant"""
        # Verify each tenant separately
        for tenant_id, events in multi_tenant_events.items():
            response = client.get(f"/verify?tenant_id={tenant_id}")

            assert response.status_code == 200
            data = response.json()

            assert data["valid"] is True
            assert data["total_events"] == len(events)

    def test_verify_after_append(self, client, tenant_id):
        """Test verifying chain after appending events"""
        # Append several events
        for i in range(3):
            request = {
                "tenant_id": tenant_id,
                "event_type": "test",
                "event_data": {"sequence": i},
            }
            append_response = client.post("/append", json=request)
            assert append_response.status_code == 200

        # Verify the chain
        response = client.get(f"/verify?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["total_events"] == 3

    def test_verify_missing_tenant_id(self, client):
        """Test verify endpoint without tenant_id parameter"""
        response = client.get("/verify")

        assert response.status_code == 422  # Validation error

    def test_verify_nonexistent_tenant(self, client):
        """Test verifying a tenant that doesn't exist"""
        response = client.get("/verify?tenant_id=nonexistent-tenant")

        assert response.status_code == 200
        data = response.json()

        # Should return valid=True with 0 events
        assert data["valid"] is True
        assert data["total_events"] == 0

    def test_verify_response_format(self, client, ledger_chain, tenant_id):
        """Test that verify response has correct format"""
        response = client.get(f"/verify?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()

        # Should have these fields
        assert "valid" in data
        assert "total_events" in data
        assert "error" in data

        # Verify types
        assert isinstance(data["valid"], bool)
        assert isinstance(data["total_events"], int)
        assert data["error"] is None or isinstance(data["error"], str)

    def test_verify_large_chain(self, client, db_session, tenant_id):
        """Test verifying a larger chain (performance test)"""
        from app.hash_utils import GENESIS_HASH
        from app.models import LedgerEvent

        # Create a chain of 50 events
        previous_hash = GENESIS_HASH
        for i in range(50):
            event_data = {"sequence": i}
            content_hash = compute_content_hash(event_data)
            chain_hash = compute_chain_hash(content_hash, previous_hash)

            event = LedgerEvent(
                tenant_id=tenant_id,
                event_type="test",
                event_data=event_data,
                content_hash=content_hash,
                previous_hash=previous_hash,
                chain_hash=chain_hash,
            )

            db_session.add(event)
            previous_hash = chain_hash

        db_session.commit()

        # Verify the chain
        response = client.get(f"/verify?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["total_events"] == 50

    def test_verify_detects_all_events_in_order(self, client, ledger_chain, tenant_id):
        """Test that verify checks all events in chronological order"""
        # The ledger_chain fixture creates 5 events
        # Verify processes them all
        response = client.get(f"/verify?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["total_events"] == 5

    def test_verify_tampered_middle_event(self, client, db_session, ledger_chain):
        """Test detecting tampering in middle of chain"""
        # Tamper with the middle event (index 2 out of 5)
        middle_event = ledger_chain[2]
        middle_event.event_data["tampered"] = True

        db_session.commit()

        response = client.get(f"/verify?tenant_id={middle_event.tenant_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert "Content hash mismatch" in data["error"]

    def test_verify_tampered_last_event(self, client, db_session, ledger_chain):
        """Test detecting tampering in last event"""
        # Tamper with the last event
        last_event = ledger_chain[-1]
        last_event.event_data["tampered"] = True

        db_session.commit()

        response = client.get(f"/verify?tenant_id={last_event.tenant_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert "Content hash mismatch" in data["error"]

    def test_verify_chain_consistency(self, client, tenant_id):
        """Test that verify maintains consistency after multiple operations"""
        # Append events
        for i in range(5):
            request = {
                "tenant_id": tenant_id,
                "event_type": "test",
                "event_data": {"sequence": i},
            }
            client.post("/append", json=request)

        # Verify multiple times - should always be valid
        for _ in range(3):
            response = client.get(f"/verify?tenant_id={tenant_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["total_events"] == 5
