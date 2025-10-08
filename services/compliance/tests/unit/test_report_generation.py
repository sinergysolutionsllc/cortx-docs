"""
Unit tests for compliance report generation logic
"""

import time

import pytest
from tests.__utils__.factories import (
    ComplianceEventFactory,
    ComplianceReportFactory,
    generate_time_series_events,
)
from tests.__utils__.helpers import (
    assert_compliance_report_structure,
    calculate_compliance_status,
    count_events_by_severity,
    count_events_by_type,
    filter_events_by_time_range,
)


@pytest.mark.unit
class TestReportGeneration:
    """Test compliance report generation"""

    def test_create_basic_report(self):
        """Test creating a basic compliance report"""
        report = ComplianceReportFactory.create_report()

        assert_compliance_report_structure(report)
        assert report["total_events"] == 10

    def test_report_has_time_range(self):
        """Test that reports include time range"""
        current_time = int(time.time())
        start_time = current_time - 86400
        end_time = current_time

        report = ComplianceReportFactory.create_report(start_time=start_time, end_time=end_time)

        assert report["time_range"]["start"] == start_time
        assert report["time_range"]["end"] == end_time

    def test_report_has_event_breakdown(self):
        """Test that reports include event type breakdown"""
        report = ComplianceReportFactory.create_report()

        assert "event_type_breakdown" in report
        assert isinstance(report["event_type_breakdown"], dict)
        assert len(report["event_type_breakdown"]) > 0

    def test_report_has_severity_breakdown(self):
        """Test that reports include severity breakdown"""
        report = ComplianceReportFactory.create_report()

        assert "severity_breakdown" in report
        assert isinstance(report["severity_breakdown"], dict)
        assert len(report["severity_breakdown"]) > 0

    def test_report_compliance_status_compliant(self):
        """Test compliant report status"""
        report = ComplianceReportFactory.create_compliant_report()

        assert report["compliance_status"] == "compliant"
        assert report["severity_breakdown"].get("critical", 0) == 0

    def test_report_compliance_status_needs_review(self):
        """Test non-compliant report status"""
        report = ComplianceReportFactory.create_non_compliant_report()

        assert report["compliance_status"] == "needs_review"
        assert report["severity_breakdown"].get("critical", 0) > 0

    def test_report_with_custom_breakdown(self):
        """Test report with custom event breakdown"""
        custom_breakdown = {"audit": 100, "violation": 5, "regulatory": 10}

        report = ComplianceReportFactory.create_report(
            total_events=115, event_type_breakdown=custom_breakdown
        )

        assert report["event_type_breakdown"]["audit"] == 100
        assert report["event_type_breakdown"]["violation"] == 5
        assert report["total_events"] == 115

    def test_report_generation_timestamp(self):
        """Test that reports have generation timestamp"""
        before = int(time.time())
        report = ComplianceReportFactory.create_report()
        after = int(time.time())

        assert before <= report["report_generated_at"] <= after + 1


@pytest.mark.unit
class TestEventAggregation:
    """Test event aggregation for reports"""

    def test_count_events_by_type(self):
        """Test counting events by type"""
        events = [
            ComplianceEventFactory.create_event(event_type="audit"),
            ComplianceEventFactory.create_event(event_type="audit"),
            ComplianceEventFactory.create_event(event_type="violation"),
            ComplianceEventFactory.create_event(event_type="regulatory"),
        ]

        counts = count_events_by_type(events)

        assert counts["audit"] == 2
        assert counts["violation"] == 1
        assert counts["regulatory"] == 1

    def test_count_events_by_severity(self):
        """Test counting events by severity"""
        events = [
            ComplianceEventFactory.create_event(severity="info"),
            ComplianceEventFactory.create_event(severity="info"),
            ComplianceEventFactory.create_event(severity="high"),
            ComplianceEventFactory.create_event(severity="critical"),
        ]

        counts = count_events_by_severity(events)

        assert counts["info"] == 2
        assert counts["high"] == 1
        assert counts["critical"] == 1

    def test_calculate_compliance_status_compliant(self):
        """Test compliance status calculation - compliant"""
        events = [
            ComplianceEventFactory.create_event(severity="info"),
            ComplianceEventFactory.create_event(severity="medium"),
            ComplianceEventFactory.create_event(severity="high"),
        ]

        status = calculate_compliance_status(events)
        assert status == "compliant"

    def test_calculate_compliance_status_needs_review(self):
        """Test compliance status calculation - needs review"""
        events = [
            ComplianceEventFactory.create_event(severity="info"),
            ComplianceEventFactory.create_event(severity="critical"),
        ]

        status = calculate_compliance_status(events)
        assert status == "needs_review"

    def test_aggregate_empty_event_list(self):
        """Test aggregation with empty event list"""
        counts = count_events_by_type([])
        assert counts == {}

        counts = count_events_by_severity([])
        assert counts == {}


@pytest.mark.unit
class TestTimeRangeFiltering:
    """Test time range filtering for reports"""

    def test_filter_events_by_time_range(self):
        """Test filtering events by time range"""
        current_time = int(time.time())
        events = [
            ComplianceEventFactory.create_event(timestamp=current_time - 7200),  # 2 hours ago
            ComplianceEventFactory.create_event(timestamp=current_time - 3600),  # 1 hour ago
            ComplianceEventFactory.create_event(timestamp=current_time - 1800),  # 30 min ago
            ComplianceEventFactory.create_event(timestamp=current_time - 900),  # 15 min ago
        ]

        # Filter for last hour
        start_time = current_time - 3600
        end_time = current_time

        filtered = filter_events_by_time_range(events, start_time, end_time)

        assert len(filtered) == 3  # Last 3 events
        for event in filtered:
            assert start_time <= event["timestamp"] <= end_time

    def test_filter_events_outside_range(self):
        """Test that events outside range are excluded"""
        current_time = int(time.time())
        events = [
            ComplianceEventFactory.create_event(timestamp=current_time - 10000),
            ComplianceEventFactory.create_event(timestamp=current_time - 8000),
        ]

        start_time = current_time - 3600
        end_time = current_time

        filtered = filter_events_by_time_range(events, start_time, end_time)

        assert len(filtered) == 0

    def test_filter_events_exact_boundaries(self):
        """Test filtering events at exact time boundaries"""
        current_time = int(time.time())
        start_time = current_time - 3600
        end_time = current_time

        events = [
            ComplianceEventFactory.create_event(timestamp=start_time),  # Exact start
            ComplianceEventFactory.create_event(timestamp=end_time),  # Exact end
            ComplianceEventFactory.create_event(timestamp=start_time - 1),  # Before start
            ComplianceEventFactory.create_event(timestamp=end_time + 1),  # After end
        ]

        filtered = filter_events_by_time_range(events, start_time, end_time)

        assert len(filtered) == 2  # Only the ones at exact boundaries


@pytest.mark.unit
class TestReportMetrics:
    """Test report metrics calculations"""

    def test_report_total_events_matches_breakdown(self):
        """Test that total events matches sum of breakdowns"""
        event_breakdown = {"audit": 50, "violation": 10, "regulatory": 20, "workflow": 5}
        total = sum(event_breakdown.values())

        report = ComplianceReportFactory.create_report(
            total_events=total, event_type_breakdown=event_breakdown
        )

        assert report["total_events"] == total
        assert sum(report["event_type_breakdown"].values()) == total

    def test_severity_distribution(self):
        """Test severity distribution in reports"""
        severity_breakdown = {"info": 60, "medium": 25, "high": 10, "critical": 5}

        report = ComplianceReportFactory.create_report(
            total_events=100, severity_breakdown=severity_breakdown
        )

        assert report["severity_breakdown"]["info"] == 60
        assert report["severity_breakdown"]["critical"] == 5

    def test_report_with_zero_events(self):
        """Test report with zero events"""
        report = ComplianceReportFactory.create_report(
            total_events=0, event_type_breakdown={}, severity_breakdown={}
        )

        assert report["total_events"] == 0
        assert report["event_type_breakdown"] == {}
        assert report["severity_breakdown"] == {}


@pytest.mark.unit
class TestTimeSeriesReporting:
    """Test time series event reporting"""

    def test_generate_time_series_events(self):
        """Test generating time series events"""
        events = generate_time_series_events(count=100)

        assert len(events) == 100

        # Verify timestamps are in order
        timestamps = [e["timestamp"] for e in events]
        assert timestamps == sorted(timestamps)

    def test_time_series_event_distribution(self):
        """Test that time series events are evenly distributed"""
        current_time = int(time.time())
        start_time = current_time - 3600
        end_time = current_time

        events = generate_time_series_events(count=60, start_time=start_time, end_time=end_time)

        # Check that events span the full range
        min_timestamp = min(e["timestamp"] for e in events)
        max_timestamp = max(e["timestamp"] for e in events)

        assert min_timestamp >= start_time
        assert max_timestamp <= end_time

    def test_time_series_event_types_vary(self):
        """Test that time series includes varied event types"""
        events = generate_time_series_events(count=100)

        event_types = set(e["event_type"] for e in events)
        assert len(event_types) > 1  # Multiple event types present
