"""
Unit tests for database models
"""

import uuid
from datetime import datetime

import pytest
from app.hash_utils import GENESIS_HASH, compute_chain_hash, compute_content_hash
from app.models import LedgerEvent


class TestLedgerEventModel:
    """Tests for LedgerEvent model"""

    def test_create_ledger_event(self, db_session, tenant_id, sample_event_data):
        """Test creating a basic ledger event"""
        content_hash = compute_content_hash(sample_event_data)
        chain_hash = compute_chain_hash(content_hash, GENESIS_HASH)

        event = LedgerEvent(
            tenant_id=tenant_id,
            event_type="test_event",
            event_data=sample_event_data,
            content_hash=content_hash,
            previous_hash=GENESIS_HASH,
            chain_hash=chain_hash,
        )

        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        assert event.id is not None
        assert isinstance(event.id, uuid.UUID)
        assert event.tenant_id == tenant_id
        assert event.event_type == "test_event"
        assert event.event_data == sample_event_data
        assert event.content_hash == content_hash
        assert event.previous_hash == GENESIS_HASH
        assert event.chain_hash == chain_hash
        assert event.created_at is not None
        assert isinstance(event.created_at, datetime)

    def test_create_event_with_optional_fields(
        self, db_session, tenant_id, sample_event_data, user_id, correlation_id
    ):
        """Test creating event with optional fields"""
        content_hash = compute_content_hash(sample_event_data)
        chain_hash = compute_chain_hash(content_hash, GENESIS_HASH)

        event = LedgerEvent(
            tenant_id=tenant_id,
            event_type="test_event",
            event_data=sample_event_data,
            content_hash=content_hash,
            previous_hash=GENESIS_HASH,
            chain_hash=chain_hash,
            user_id=user_id,
            correlation_id=correlation_id,
            description="Test event description",
        )

        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        assert event.user_id == user_id
        assert event.correlation_id == correlation_id
        assert event.description == "Test event description"

    def test_create_event_without_optional_fields(self, db_session, tenant_id, sample_event_data):
        """Test creating event without optional fields"""
        content_hash = compute_content_hash(sample_event_data)
        chain_hash = compute_chain_hash(content_hash, GENESIS_HASH)

        event = LedgerEvent(
            tenant_id=tenant_id,
            event_type="test_event",
            event_data=sample_event_data,
            content_hash=content_hash,
            previous_hash=GENESIS_HASH,
            chain_hash=chain_hash,
        )

        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        assert event.user_id is None
        assert event.correlation_id is None
        assert event.description is None

    def test_event_id_auto_generated(self, db_session, tenant_id, sample_event_data):
        """Test that event ID is auto-generated"""
        content_hash = compute_content_hash(sample_event_data)
        chain_hash = compute_chain_hash(content_hash, GENESIS_HASH)

        event = LedgerEvent(
            tenant_id=tenant_id,
            event_type="test_event",
            event_data=sample_event_data,
            content_hash=content_hash,
            previous_hash=GENESIS_HASH,
            chain_hash=chain_hash,
        )

        # ID should be None before commit
        assert event.id is None or isinstance(event.id, uuid.UUID)

        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        # ID should be set after commit
        assert event.id is not None
        assert isinstance(event.id, uuid.UUID)

    def test_created_at_auto_generated(self, db_session, tenant_id, sample_event_data):
        """Test that created_at is auto-generated"""
        content_hash = compute_content_hash(sample_event_data)
        chain_hash = compute_chain_hash(content_hash, GENESIS_HASH)

        event = LedgerEvent(
            tenant_id=tenant_id,
            event_type="test_event",
            event_data=sample_event_data,
            content_hash=content_hash,
            previous_hash=GENESIS_HASH,
            chain_hash=chain_hash,
        )

        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        assert event.created_at is not None
        assert isinstance(event.created_at, datetime)

    def test_to_dict(self, ledger_event):
        """Test converting event to dictionary"""
        result = ledger_event.to_dict()

        assert isinstance(result, dict)
        assert "id" in result
        assert "tenant_id" in result
        assert "event_type" in result
        assert "event_data" in result
        assert "created_at" in result
        assert "content_hash" in result
        assert "previous_hash" in result
        assert "chain_hash" in result
        assert "user_id" in result
        assert "correlation_id" in result
        assert "description" in result

        # Verify types
        assert isinstance(result["id"], str)
        assert isinstance(result["tenant_id"], str)
        assert isinstance(result["event_type"], str)
        assert isinstance(result["event_data"], dict)
        assert isinstance(result["created_at"], str)
        assert isinstance(result["content_hash"], str)
        assert isinstance(result["previous_hash"], str)
        assert isinstance(result["chain_hash"], str)

    def test_to_dict_values(self, db_session, tenant_id, sample_event_data):
        """Test that to_dict returns correct values"""
        content_hash = compute_content_hash(sample_event_data)
        chain_hash = compute_chain_hash(content_hash, GENESIS_HASH)

        event = LedgerEvent(
            tenant_id=tenant_id,
            event_type="test_event",
            event_data=sample_event_data,
            content_hash=content_hash,
            previous_hash=GENESIS_HASH,
            chain_hash=chain_hash,
            user_id="test-user",
            correlation_id="test-correlation",
            description="Test description",
        )

        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        result = event.to_dict()

        assert result["id"] == str(event.id)
        assert result["tenant_id"] == tenant_id
        assert result["event_type"] == "test_event"
        assert result["event_data"] == sample_event_data
        assert result["content_hash"] == content_hash
        assert result["previous_hash"] == GENESIS_HASH
        assert result["chain_hash"] == chain_hash
        assert result["user_id"] == "test-user"
        assert result["correlation_id"] == "test-correlation"
        assert result["description"] == "Test description"

    def test_event_data_jsonb(self, db_session, tenant_id):
        """Test that event_data can store complex JSON"""
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

        content_hash = compute_content_hash(complex_data)
        chain_hash = compute_chain_hash(content_hash, GENESIS_HASH)

        event = LedgerEvent(
            tenant_id=tenant_id,
            event_type="test_event",
            event_data=complex_data,
            content_hash=content_hash,
            previous_hash=GENESIS_HASH,
            chain_hash=chain_hash,
        )

        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        assert event.event_data == complex_data

    def test_chain_hash_unique_constraint(self, db_session, tenant_id, sample_event_data):
        """Test that chain_hash must be unique"""
        content_hash = compute_content_hash(sample_event_data)
        chain_hash = compute_chain_hash(content_hash, GENESIS_HASH)

        # Create first event
        event1 = LedgerEvent(
            tenant_id=tenant_id,
            event_type="test_event",
            event_data=sample_event_data,
            content_hash=content_hash,
            previous_hash=GENESIS_HASH,
            chain_hash=chain_hash,
        )

        db_session.add(event1)
        db_session.commit()

        # Try to create second event with same chain_hash
        event2 = LedgerEvent(
            tenant_id=tenant_id,
            event_type="test_event",
            event_data=sample_event_data,
            content_hash=content_hash,
            previous_hash=GENESIS_HASH,
            chain_hash=chain_hash,  # Same chain hash!
        )

        db_session.add(event2)

        # Should raise integrity error
        with pytest.raises(Exception):  # SQLAlchemy raises different exceptions
            db_session.commit()

    def test_query_by_tenant(self, db_session, multi_tenant_events):
        """Test querying events by tenant ID"""
        # Query for tenant-a
        events = db_session.query(LedgerEvent).filter(LedgerEvent.tenant_id == "tenant-a").all()

        assert len(events) == 3
        assert all(e.tenant_id == "tenant-a" for e in events)

        # Query for tenant-b
        events = db_session.query(LedgerEvent).filter(LedgerEvent.tenant_id == "tenant-b").all()

        assert len(events) == 2
        assert all(e.tenant_id == "tenant-b" for e in events)

    def test_query_by_event_type(self, db_session, ledger_chain):
        """Test querying events by event type"""
        # Create events with different types
        events = (
            db_session.query(LedgerEvent).filter(LedgerEvent.event_type == "event_type_0").all()
        )

        assert len(events) == 1
        assert events[0].event_type == "event_type_0"

    def test_query_by_correlation_id(self, db_session, ledger_chain):
        """Test querying events by correlation ID"""
        events = db_session.query(LedgerEvent).filter(LedgerEvent.correlation_id == "corr_0").all()

        assert len(events) == 1
        assert events[0].correlation_id == "corr_0"

    def test_order_by_created_at(self, db_session, ledger_chain):
        """Test ordering events by created_at"""
        events = db_session.query(LedgerEvent).order_by(LedgerEvent.created_at).all()

        # Should be in chronological order
        for i in range(len(events) - 1):
            assert events[i].created_at <= events[i + 1].created_at

    def test_hash_field_lengths(self, ledger_event):
        """Test that hash fields have correct length (64 chars for SHA-256)"""
        assert len(ledger_event.content_hash) == 64
        assert len(ledger_event.previous_hash) == 64
        assert len(ledger_event.chain_hash) == 64

    def test_hash_fields_hex_format(self, ledger_event):
        """Test that hash fields are valid hex strings"""
        import re

        hex_pattern = re.compile(r"^[0-9a-f]{64}$")

        assert hex_pattern.match(ledger_event.content_hash)
        assert hex_pattern.match(ledger_event.previous_hash)
        assert hex_pattern.match(ledger_event.chain_hash)
