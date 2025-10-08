"""
Test data factories for generating compliance events and reports
"""

import time
import uuid
from typing import Any, Dict, List, Optional


class ComplianceEventFactory:
    """Factory for creating compliance event test data"""

    @staticmethod
    def create_event(
        event_type: str = "audit",
        description: str = "Test compliance event",
        data: Optional[Dict[str, Any]] = None,
        user_id: str = "test_user",
        severity: str = "info",
        event_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a compliance event with default or custom values"""
        if data is None:
            data = {"test_key": "test_value"}

        return {
            "event_id": event_id or str(uuid.uuid4()),
            "event_type": event_type,
            "description": description,
            "data": data,
            "user_id": user_id,
            "severity": severity,
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "timestamp": timestamp or int(time.time()),
            "data_hash": f"hash_{uuid.uuid4().hex[:8]}",
        }

    @staticmethod
    def create_audit_event(
        description: str = "Audit event", success: bool = True, **kwargs
    ) -> Dict[str, Any]:
        """Create an audit event"""
        data = {"success": success, "action": "test_action", **kwargs.get("data", {})}
        kwargs["data"] = data
        return ComplianceEventFactory.create_event(
            event_type="audit", description=description, severity="info", **kwargs
        )

    @staticmethod
    def create_violation_event(
        description: str = "Security violation", blocked: bool = True, **kwargs
    ) -> Dict[str, Any]:
        """Create a violation event"""
        data = {"blocked": blocked, "resource": "/api/sensitive", **kwargs.get("data", {})}
        kwargs["data"] = data
        return ComplianceEventFactory.create_event(
            event_type="violation", description=description, severity="high", **kwargs
        )

    @staticmethod
    def create_regulatory_event(
        description: str = "Regulatory compliance event", regulation: str = "HIPAA", **kwargs
    ) -> Dict[str, Any]:
        """Create a regulatory compliance event"""
        data = {
            "regulation": regulation,
            "compliance_status": "compliant",
            **kwargs.get("data", {}),
        }
        kwargs["data"] = data
        return ComplianceEventFactory.create_event(
            event_type="regulatory", description=description, severity="medium", **kwargs
        )

    @staticmethod
    def create_workflow_event(
        description: str = "Workflow event", workflow_id: str = "wf_123", **kwargs
    ) -> Dict[str, Any]:
        """Create a workflow event"""
        data = {
            "workflow_id": workflow_id,
            "pack_id": "test.pack",
            "version": "1.0.0",
            **kwargs.get("data", {}),
        }
        kwargs["data"] = data
        return ComplianceEventFactory.create_event(
            event_type="workflow", description=description, severity="info", **kwargs
        )

    @staticmethod
    def create_critical_event(
        description: str = "Critical compliance event", **kwargs
    ) -> Dict[str, Any]:
        """Create a critical severity event"""
        return ComplianceEventFactory.create_event(
            event_type="violation", description=description, severity="critical", **kwargs
        )

    @staticmethod
    def create_batch(
        count: int = 10, event_type: Optional[str] = None, time_spread_seconds: int = 3600
    ) -> List[Dict[str, Any]]:
        """Create a batch of compliance events"""
        events = []
        current_time = int(time.time())
        time_step = time_spread_seconds // count if count > 0 else 0

        for i in range(count):
            event = ComplianceEventFactory.create_event(
                event_type=event_type or "audit",
                description=f"Batch event {i + 1}",
                timestamp=current_time - (time_step * i),
            )
            events.append(event)

        return events


class ComplianceReportFactory:
    """Factory for creating compliance report test data"""

    @staticmethod
    def create_report(
        total_events: int = 10,
        event_type_breakdown: Optional[Dict[str, int]] = None,
        severity_breakdown: Optional[Dict[str, int]] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a compliance report with default or custom values"""
        current_time = int(time.time())
        start = start_time or (current_time - 86400)
        end = end_time or current_time

        if event_type_breakdown is None:
            event_type_breakdown = {"audit": 5, "violation": 2, "regulatory": 2, "workflow": 1}

        if severity_breakdown is None:
            severity_breakdown = {"info": 6, "medium": 2, "high": 1, "critical": 1}

        return {
            "report_generated_at": current_time,
            "time_range": {"start": start, "end": end},
            "total_events": total_events,
            "event_type_breakdown": event_type_breakdown,
            "severity_breakdown": severity_breakdown,
            "compliance_status": (
                "compliant" if severity_breakdown.get("critical", 0) == 0 else "needs_review"
            ),
            "correlation_id": str(uuid.uuid4()),
        }

    @staticmethod
    def create_compliant_report(**kwargs) -> Dict[str, Any]:
        """Create a report with no critical issues"""
        severity_breakdown = {"info": 8, "medium": 2, "high": 0, "critical": 0}
        kwargs["severity_breakdown"] = severity_breakdown
        kwargs.setdefault("total_events", 10)
        return ComplianceReportFactory.create_report(**kwargs)

    @staticmethod
    def create_non_compliant_report(**kwargs) -> Dict[str, Any]:
        """Create a report with critical issues"""
        severity_breakdown = {"info": 5, "medium": 3, "high": 2, "critical": 5}
        kwargs["severity_breakdown"] = severity_breakdown
        kwargs.setdefault("total_events", 15)
        return ComplianceReportFactory.create_report(**kwargs)


class ComplianceEventRequestFactory:
    """Factory for creating compliance event request payloads"""

    @staticmethod
    def create_request(
        event_type: str = "audit",
        description: str = "Test event",
        data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = "test_user",
        severity: str = "info",
    ) -> Dict[str, Any]:
        """Create a compliance event request payload"""
        if data is None:
            data = {"test_key": "test_value"}

        return {
            "event_type": event_type,
            "description": description,
            "data": data,
            "user_id": user_id,
            "severity": severity,
        }

    @staticmethod
    def create_minimal_request() -> Dict[str, Any]:
        """Create a minimal valid request"""
        return {"event_type": "audit", "description": "Minimal test event"}

    @staticmethod
    def create_invalid_request() -> Dict[str, Any]:
        """Create an invalid request (missing required fields)"""
        return {
            "data": {"test": "value"}
            # Missing event_type and description
        }


def generate_time_series_events(
    count: int = 100, start_time: Optional[int] = None, end_time: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Generate a time series of compliance events for testing"""
    current_time = int(time.time())
    start = start_time or (current_time - 86400)
    end = end_time or current_time

    time_step = (end - start) // count if count > 0 else 0
    events = []

    event_types = ["audit", "violation", "regulatory", "workflow"]
    severities = ["info", "medium", "high", "critical"]

    for i in range(count):
        event = ComplianceEventFactory.create_event(
            event_type=event_types[i % len(event_types)],
            severity=severities[i % len(severities)],
            description=f"Time series event {i + 1}",
            timestamp=start + (time_step * i),
        )
        events.append(event)

    return events
