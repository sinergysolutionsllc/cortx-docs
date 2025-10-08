"""
Test helper functions for compliance service testing
"""

import time
from typing import Any, Dict, List


def assert_compliance_event_structure(event: Dict[str, Any]) -> None:
    """Assert that an event has the expected structure"""
    required_fields = [
        "event_id",
        "event_type",
        "description",
        "data",
        "user_id",
        "severity",
        "correlation_id",
        "timestamp",
        "data_hash",
    ]

    for field in required_fields:
        assert field in event, f"Missing required field: {field}"

    assert isinstance(event["data"], dict), "data must be a dictionary"
    assert isinstance(event["timestamp"], int), "timestamp must be an integer"


def assert_compliance_report_structure(report: Dict[str, Any]) -> None:
    """Assert that a report has the expected structure"""
    required_fields = [
        "report_generated_at",
        "time_range",
        "total_events",
        "event_type_breakdown",
        "severity_breakdown",
        "compliance_status",
        "correlation_id",
    ]

    for field in required_fields:
        assert field in report, f"Missing required field: {field}"

    assert "start" in report["time_range"], "time_range must have start"
    assert "end" in report["time_range"], "time_range must have end"
    assert isinstance(
        report["event_type_breakdown"], dict
    ), "event_type_breakdown must be a dictionary"
    assert isinstance(report["severity_breakdown"], dict), "severity_breakdown must be a dictionary"


def assert_event_response_structure(response: Dict[str, Any]) -> None:
    """Assert that an event response has the expected structure"""
    required_fields = ["event_id", "status", "correlation_id"]

    for field in required_fields:
        assert field in response, f"Missing required field: {field}"


def count_events_by_type(events: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count events by type"""
    counts = {}
    for event in events:
        event_type = event.get("event_type", "unknown")
        counts[event_type] = counts.get(event_type, 0) + 1
    return counts


def count_events_by_severity(events: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count events by severity"""
    counts = {}
    for event in events:
        severity = event.get("severity", "unknown")
        counts[severity] = counts.get(severity, 0) + 1
    return counts


def filter_events_by_type(events: List[Dict[str, Any]], event_type: str) -> List[Dict[str, Any]]:
    """Filter events by type"""
    return [e for e in events if e.get("event_type") == event_type]


def filter_events_by_time_range(
    events: List[Dict[str, Any]], start_time: int, end_time: int
) -> List[Dict[str, Any]]:
    """Filter events by time range"""
    return [e for e in events if start_time <= e.get("timestamp", 0) <= end_time]


def filter_events_by_severity(events: List[Dict[str, Any]], severity: str) -> List[Dict[str, Any]]:
    """Filter events by severity"""
    return [e for e in events if e.get("severity") == severity]


def calculate_compliance_status(events: List[Dict[str, Any]]) -> str:
    """Calculate compliance status based on event severities"""
    severity_counts = count_events_by_severity(events)
    critical_count = severity_counts.get("critical", 0)

    if critical_count > 0:
        return "needs_review"
    return "compliant"


def sort_events_by_timestamp(
    events: List[Dict[str, Any]], reverse: bool = True
) -> List[Dict[str, Any]]:
    """Sort events by timestamp"""
    return sorted(events, key=lambda e: e.get("timestamp", 0), reverse=reverse)


def validate_event_hash(event: Dict[str, Any]) -> bool:
    """Validate that an event has a data hash"""
    return "data_hash" in event and len(event["data_hash"]) > 0


def validate_correlation_id(data: Dict[str, Any]) -> bool:
    """Validate that data has a correlation_id"""
    return "correlation_id" in data and len(data["correlation_id"]) > 0


def create_time_range_dict(hours_ago: int = 24) -> Dict[str, int]:
    """Create a time range dictionary for testing"""
    current_time = int(time.time())
    return {
        "start_time": current_time - (hours_ago * 3600),
        "end_time": current_time,
        "current_time": current_time,
    }


def is_within_time_range(timestamp: int, start_time: int, end_time: int) -> bool:
    """Check if timestamp is within time range"""
    return start_time <= timestamp <= end_time
