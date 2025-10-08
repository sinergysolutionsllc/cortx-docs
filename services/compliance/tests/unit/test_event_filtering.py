"""
Unit tests for event filtering and querying logic
"""

import time

import pytest
from tests.__utils__.factories import ComplianceEventFactory
from tests.__utils__.helpers import (
    filter_events_by_severity,
    filter_events_by_time_range,
    filter_events_by_type,
    sort_events_by_timestamp,
)


@pytest.mark.unit
class TestEventFiltering:
    """Test event filtering functionality"""

    def test_filter_by_event_type(self):
        """Test filtering events by type"""
        events = [
            ComplianceEventFactory.create_event(event_type="audit"),
            ComplianceEventFactory.create_event(event_type="violation"),
            ComplianceEventFactory.create_event(event_type="audit"),
            ComplianceEventFactory.create_event(event_type="regulatory"),
        ]

        filtered = filter_events_by_type(events, "audit")

        assert len(filtered) == 2
        for event in filtered:
            assert event["event_type"] == "audit"

    def test_filter_by_nonexistent_type(self):
        """Test filtering by non-existent event type"""
        events = ComplianceEventFactory.create_batch(count=5, event_type="audit")

        filtered = filter_events_by_type(events, "nonexistent")

        assert len(filtered) == 0

    def test_filter_empty_list(self):
        """Test filtering empty event list"""
        filtered = filter_events_by_type([], "audit")
        assert filtered == []

    def test_filter_by_severity(self):
        """Test filtering events by severity"""
        events = [
            ComplianceEventFactory.create_event(severity="info"),
            ComplianceEventFactory.create_event(severity="critical"),
            ComplianceEventFactory.create_event(severity="info"),
            ComplianceEventFactory.create_event(severity="high"),
        ]

        filtered = filter_events_by_severity(events, "info")

        assert len(filtered) == 2
        for event in filtered:
            assert event["severity"] == "info"

    def test_filter_critical_events_only(self):
        """Test filtering only critical events"""
        events = [
            ComplianceEventFactory.create_event(severity="info"),
            ComplianceEventFactory.create_critical_event(),
            ComplianceEventFactory.create_event(severity="medium"),
            ComplianceEventFactory.create_critical_event(),
        ]

        filtered = filter_events_by_severity(events, "critical")

        assert len(filtered) == 2
        for event in filtered:
            assert event["severity"] == "critical"


@pytest.mark.unit
class TestEventSorting:
    """Test event sorting functionality"""

    def test_sort_by_timestamp_descending(self):
        """Test sorting events by timestamp (newest first)"""
        current_time = int(time.time())
        events = [
            ComplianceEventFactory.create_event(timestamp=current_time - 3600),
            ComplianceEventFactory.create_event(timestamp=current_time - 7200),
            ComplianceEventFactory.create_event(timestamp=current_time - 1800),
        ]

        sorted_events = sort_events_by_timestamp(events, reverse=True)

        timestamps = [e["timestamp"] for e in sorted_events]
        assert timestamps == sorted(timestamps, reverse=True)
        assert sorted_events[0]["timestamp"] == current_time - 1800  # Most recent first

    def test_sort_by_timestamp_ascending(self):
        """Test sorting events by timestamp (oldest first)"""
        current_time = int(time.time())
        events = [
            ComplianceEventFactory.create_event(timestamp=current_time - 3600),
            ComplianceEventFactory.create_event(timestamp=current_time - 7200),
            ComplianceEventFactory.create_event(timestamp=current_time - 1800),
        ]

        sorted_events = sort_events_by_timestamp(events, reverse=False)

        timestamps = [e["timestamp"] for e in sorted_events]
        assert timestamps == sorted(timestamps)
        assert sorted_events[0]["timestamp"] == current_time - 7200  # Oldest first

    def test_sort_empty_list(self):
        """Test sorting empty event list"""
        sorted_events = sort_events_by_timestamp([])
        assert sorted_events == []

    def test_sort_single_event(self):
        """Test sorting list with single event"""
        events = [ComplianceEventFactory.create_event()]
        sorted_events = sort_events_by_timestamp(events)
        assert len(sorted_events) == 1


@pytest.mark.unit
class TestEventQueryCombinations:
    """Test combining multiple filter criteria"""

    def test_filter_by_type_and_severity(self):
        """Test filtering by both type and severity"""
        events = [
            ComplianceEventFactory.create_audit_event(severity="info"),
            ComplianceEventFactory.create_violation_event(severity="critical"),
            ComplianceEventFactory.create_audit_event(severity="critical"),
            ComplianceEventFactory.create_regulatory_event(severity="info"),
        ]

        # Filter by type first
        audit_events = filter_events_by_type(events, "audit")
        # Then filter by severity
        critical_audit = filter_events_by_severity(audit_events, "critical")

        assert len(critical_audit) == 1
        assert critical_audit[0]["event_type"] == "audit"
        assert critical_audit[0]["severity"] == "critical"

    def test_filter_by_type_and_time_range(self):
        """Test filtering by type and time range"""
        current_time = int(time.time())
        events = [
            ComplianceEventFactory.create_audit_event(timestamp=current_time - 7200),
            ComplianceEventFactory.create_audit_event(timestamp=current_time - 3600),
            ComplianceEventFactory.create_violation_event(timestamp=current_time - 1800),
            ComplianceEventFactory.create_audit_event(timestamp=current_time - 900),
        ]

        # Filter by type
        audit_events = filter_events_by_type(events, "audit")
        # Then filter by time range (last hour)
        recent_audits = filter_events_by_time_range(audit_events, current_time - 3600, current_time)

        assert len(recent_audits) == 2
        for event in recent_audits:
            assert event["event_type"] == "audit"
            assert event["timestamp"] >= current_time - 3600

    def test_filter_sort_and_limit(self):
        """Test filter, sort, and limit operations"""
        current_time = int(time.time())
        events = [
            ComplianceEventFactory.create_violation_event(timestamp=current_time - i * 600)
            for i in range(10)
        ]

        # Filter by type
        violations = filter_events_by_type(events, "violation")
        # Sort by timestamp
        sorted_violations = sort_events_by_timestamp(violations, reverse=True)
        # Limit to 5
        limited = sorted_violations[:5]

        assert len(limited) == 5
        assert limited[0]["timestamp"] > limited[-1]["timestamp"]  # Newest first


@pytest.mark.unit
class TestEventPagination:
    """Test event pagination logic"""

    def test_paginate_events_first_page(self):
        """Test getting first page of events"""
        events = ComplianceEventFactory.create_batch(count=100)
        page_size = 10
        page = 0

        paginated = events[page * page_size : (page + 1) * page_size]

        assert len(paginated) == page_size

    def test_paginate_events_middle_page(self):
        """Test getting middle page of events"""
        events = ComplianceEventFactory.create_batch(count=100)
        page_size = 10
        page = 5

        paginated = events[page * page_size : (page + 1) * page_size]

        assert len(paginated) == page_size

    def test_paginate_events_last_page(self):
        """Test getting last page with fewer items"""
        events = ComplianceEventFactory.create_batch(count=95)
        page_size = 10
        page = 9  # Last page

        paginated = events[page * page_size : (page + 1) * page_size]

        assert len(paginated) == 5  # Remaining items

    def test_paginate_beyond_available(self):
        """Test pagination beyond available events"""
        events = ComplianceEventFactory.create_batch(count=10)
        page_size = 10
        page = 5  # Beyond available

        paginated = events[page * page_size : (page + 1) * page_size]

        assert len(paginated) == 0


@pytest.mark.unit
class TestEventLimiting:
    """Test event limiting functionality"""

    def test_limit_events(self):
        """Test limiting number of returned events"""
        events = ComplianceEventFactory.create_batch(count=100)
        limit = 20

        limited = events[:limit]

        assert len(limited) == limit

    def test_limit_greater_than_available(self):
        """Test limit greater than available events"""
        events = ComplianceEventFactory.create_batch(count=10)
        limit = 100

        limited = events[:limit]

        assert len(limited) == 10  # All available events

    def test_limit_zero(self):
        """Test limit of zero"""
        events = ComplianceEventFactory.create_batch(count=10)
        limit = 0

        limited = events[:limit]

        assert len(limited) == 0

    def test_default_limit(self):
        """Test default limit behavior"""
        events = ComplianceEventFactory.create_batch(count=150)
        default_limit = 100

        limited = events[:default_limit]

        assert len(limited) == default_limit


@pytest.mark.unit
class TestComplexQueryScenarios:
    """Test complex query scenarios"""

    def test_recent_critical_violations(self):
        """Test finding recent critical violations"""
        current_time = int(time.time())
        events = [
            ComplianceEventFactory.create_violation_event(
                severity="critical", timestamp=current_time - 1800
            ),
            ComplianceEventFactory.create_audit_event(
                severity="info", timestamp=current_time - 1500
            ),
            ComplianceEventFactory.create_violation_event(
                severity="high", timestamp=current_time - 1200
            ),
            ComplianceEventFactory.create_violation_event(
                severity="critical", timestamp=current_time - 900
            ),
        ]

        # Filter violations
        violations = filter_events_by_type(events, "violation")
        # Filter critical
        critical = filter_events_by_severity(violations, "critical")
        # Filter recent (last hour)
        recent = filter_events_by_time_range(critical, current_time - 3600, current_time)
        # Sort by timestamp
        sorted_recent = sort_events_by_timestamp(recent, reverse=True)

        assert len(sorted_recent) == 2
        assert all(e["event_type"] == "violation" for e in sorted_recent)
        assert all(e["severity"] == "critical" for e in sorted_recent)

    def test_audit_trail_by_user(self):
        """Test filtering audit trail by user ID"""
        events = [
            ComplianceEventFactory.create_audit_event(user_id="user_123"),
            ComplianceEventFactory.create_audit_event(user_id="user_456"),
            ComplianceEventFactory.create_audit_event(user_id="user_123"),
            ComplianceEventFactory.create_violation_event(user_id="user_123"),
        ]

        # Filter by type
        audit_events = filter_events_by_type(events, "audit")
        # Filter by user_id
        user_audits = [e for e in audit_events if e["user_id"] == "user_123"]

        assert len(user_audits) == 2
        for event in user_audits:
            assert event["event_type"] == "audit"
            assert event["user_id"] == "user_123"
