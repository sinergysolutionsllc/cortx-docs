"""
Unit tests for compliance event logging logic
"""

import time

import pytest
from tests.__utils__.factories import ComplianceEventFactory, ComplianceEventRequestFactory
from tests.__utils__.helpers import (
    assert_compliance_event_structure,
    validate_correlation_id,
    validate_event_hash,
)


@pytest.mark.unit
class TestEventLogging:
    """Test compliance event logging functionality"""

    def test_create_event_with_all_fields(self):
        """Test creating an event with all fields populated"""
        event = ComplianceEventFactory.create_event(
            event_type="audit",
            description="Test audit event",
            data={"test": "data"},
            user_id="user_123",
            severity="info",
        )

        assert_compliance_event_structure(event)
        assert event["event_type"] == "audit"
        assert event["description"] == "Test audit event"
        assert event["user_id"] == "user_123"
        assert event["severity"] == "info"

    def test_create_event_with_minimal_fields(self):
        """Test creating an event with minimal required fields"""
        event = ComplianceEventFactory.create_event()

        assert_compliance_event_structure(event)
        assert event["event_type"] is not None
        assert event["description"] is not None

    def test_event_has_unique_id(self):
        """Test that each event gets a unique ID"""
        event1 = ComplianceEventFactory.create_event()
        event2 = ComplianceEventFactory.create_event()

        assert event1["event_id"] != event2["event_id"]

    def test_event_has_timestamp(self):
        """Test that events have timestamps"""
        before = int(time.time())
        event = ComplianceEventFactory.create_event()
        after = int(time.time())

        assert "timestamp" in event
        assert before <= event["timestamp"] <= after + 1

    def test_event_has_data_hash(self):
        """Test that events have data hash for integrity"""
        event = ComplianceEventFactory.create_event(data={"sensitive": "data"})

        assert validate_event_hash(event)
        assert len(event["data_hash"]) > 0

    def test_event_has_correlation_id(self):
        """Test that events have correlation IDs"""
        event = ComplianceEventFactory.create_event()

        assert validate_correlation_id(event)

    def test_audit_event_creation(self):
        """Test creating an audit event"""
        event = ComplianceEventFactory.create_audit_event(description="User login", success=True)

        assert event["event_type"] == "audit"
        assert event["severity"] == "info"
        assert event["data"]["success"] is True

    def test_violation_event_creation(self):
        """Test creating a violation event"""
        event = ComplianceEventFactory.create_violation_event(
            description="Unauthorized access attempt", blocked=True
        )

        assert event["event_type"] == "violation"
        assert event["severity"] == "high"
        assert event["data"]["blocked"] is True

    def test_regulatory_event_creation(self):
        """Test creating a regulatory event"""
        event = ComplianceEventFactory.create_regulatory_event(
            description="HIPAA compliance check", regulation="HIPAA"
        )

        assert event["event_type"] == "regulatory"
        assert event["severity"] == "medium"
        assert event["data"]["regulation"] == "HIPAA"

    def test_workflow_event_creation(self):
        """Test creating a workflow event"""
        event = ComplianceEventFactory.create_workflow_event(
            description="Workflow started", workflow_id="wf_123"
        )

        assert event["event_type"] == "workflow"
        assert event["data"]["workflow_id"] == "wf_123"

    def test_critical_event_creation(self):
        """Test creating a critical severity event"""
        event = ComplianceEventFactory.create_critical_event(
            description="Critical security violation"
        )

        assert event["severity"] == "critical"

    def test_event_request_payload_creation(self):
        """Test creating event request payloads"""
        request = ComplianceEventRequestFactory.create_request(
            event_type="audit",
            description="Test event",
            data={"key": "value"},
            user_id="user_123",
            severity="info",
        )

        assert request["event_type"] == "audit"
        assert request["description"] == "Test event"
        assert request["data"]["key"] == "value"
        assert request["user_id"] == "user_123"
        assert request["severity"] == "info"

    def test_minimal_event_request(self):
        """Test creating minimal event request"""
        request = ComplianceEventRequestFactory.create_minimal_request()

        assert "event_type" in request
        assert "description" in request
        assert request["event_type"] == "audit"

    def test_event_batch_creation(self):
        """Test creating a batch of events"""
        events = ComplianceEventFactory.create_batch(count=10)

        assert len(events) == 10
        event_ids = [e["event_id"] for e in events]
        assert len(event_ids) == len(set(event_ids))  # All unique

    def test_event_batch_with_type(self):
        """Test creating a batch of events with specific type"""
        events = ComplianceEventFactory.create_batch(count=5, event_type="violation")

        assert len(events) == 5
        for event in events:
            assert event["event_type"] == "violation"

    def test_event_batch_time_spread(self):
        """Test that batched events have spread timestamps"""
        events = ComplianceEventFactory.create_batch(count=10, time_spread_seconds=1000)

        timestamps = [e["timestamp"] for e in events]
        assert len(set(timestamps)) >= 5  # At least some variation


@pytest.mark.unit
class TestEventSeverityMapping:
    """Test severity level mapping"""

    def test_severity_levels(self):
        """Test all severity levels"""
        severities = ["info", "low", "medium", "high", "critical"]

        for severity in severities:
            event = ComplianceEventFactory.create_event(severity=severity)
            assert event["severity"] == severity

    def test_default_severity(self):
        """Test default severity level"""
        event = ComplianceEventFactory.create_event()
        assert event["severity"] in ["info", "low", "medium", "high", "critical"]


@pytest.mark.unit
class TestEventTypeMapping:
    """Test event type mapping"""

    def test_event_types(self):
        """Test all event types"""
        event_types = ["audit", "violation", "regulatory", "workflow", "access"]

        for event_type in event_types:
            event = ComplianceEventFactory.create_event(event_type=event_type)
            assert event["event_type"] == event_type

    def test_custom_event_type(self):
        """Test custom event type"""
        event = ComplianceEventFactory.create_event(event_type="custom_type")
        assert event["event_type"] == "custom_type"


@pytest.mark.unit
class TestEventDataIntegrity:
    """Test event data integrity features"""

    def test_event_data_immutability(self):
        """Test that event data is properly stored"""
        original_data = {"key": "value", "nested": {"inner": "data"}}
        event = ComplianceEventFactory.create_event(data=original_data)

        assert event["data"]["key"] == "value"
        assert event["data"]["nested"]["inner"] == "data"

    def test_event_with_empty_data(self):
        """Test event with empty data dictionary"""
        event = ComplianceEventFactory.create_event(data={})

        assert event["data"] == {}
        assert validate_event_hash(event)

    def test_event_with_complex_data(self):
        """Test event with complex nested data"""
        complex_data = {
            "level1": {"level2": {"level3": ["item1", "item2", "item3"]}},
            "array": [1, 2, 3, 4, 5],
            "mixed": {"type": "test", "values": [True, False, None]},
        }

        event = ComplianceEventFactory.create_event(data=complex_data)

        assert event["data"]["level1"]["level2"]["level3"] == ["item1", "item2", "item3"]
        assert event["data"]["array"] == [1, 2, 3, 4, 5]
