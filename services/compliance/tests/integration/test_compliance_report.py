"""
Integration tests for GET /compliance/report endpoint
"""

import os
import time

import pytest
from tests.__utils__.helpers import assert_compliance_report_structure, validate_correlation_id


@pytest.mark.integration
class TestComplianceReport:
    """Test GET /compliance/report endpoint"""

    def test_generate_basic_report(self, client, admin_auth_headers, populated_compliance_events):
        """Test generating a basic compliance report"""
        response = client.get("/compliance/report", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert_compliance_report_structure(data)

    def test_report_with_no_events(self, client, admin_auth_headers):
        """Test generating report when no events exist"""
        response = client.get("/compliance/report", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 0
        assert data["event_type_breakdown"] == {}
        assert data["severity_breakdown"] == {}

    def test_report_default_time_range(
        self, client, admin_auth_headers, populated_compliance_events
    ):
        """Test report uses default time range (last 24 hours)"""
        response = client.get("/compliance/report", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()

        current_time = int(time.time())
        time_range = data["time_range"]

        # Should be approximately 24 hours
        duration = time_range["end"] - time_range["start"]
        assert 86000 <= duration <= 87000  # Allow some variance

    def test_report_with_custom_time_range(
        self, client, admin_auth_headers, populated_compliance_events
    ):
        """Test report with custom time range"""
        current_time = int(time.time())
        start_time = current_time - 3600  # 1 hour ago
        end_time = current_time

        response = client.get(
            f"/compliance/report?start_time={start_time}&end_time={end_time}",
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["time_range"]["start"] == start_time
        assert data["time_range"]["end"] == end_time

    def test_report_event_type_breakdown(self, client, admin_auth_headers):
        """Test report event type breakdown"""
        # Post events of different types
        event_types = {"audit": 5, "violation": 2, "regulatory": 3}

        for event_type, count in event_types.items():
            for i in range(count):
                client.post(
                    "/compliance/events",
                    json={
                        "event_type": event_type,
                        "description": f"{event_type} event {i}",
                        "severity": "info",
                    },
                    headers=admin_auth_headers,
                )

        response = client.get("/compliance/report", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()
        breakdown = data["event_type_breakdown"]

        assert breakdown.get("audit", 0) == 5
        assert breakdown.get("violation", 0) == 2
        assert breakdown.get("regulatory", 0) == 3

    def test_report_severity_breakdown(self, client, admin_auth_headers):
        """Test report severity breakdown"""
        # Post events of different severities
        severities = {"info": 4, "high": 2, "critical": 1}

        for severity, count in severities.items():
            for i in range(count):
                client.post(
                    "/compliance/events",
                    json={
                        "event_type": "audit",
                        "description": f"Event with {severity} severity",
                        "severity": severity,
                    },
                    headers=admin_auth_headers,
                )

        response = client.get("/compliance/report", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()
        breakdown = data["severity_breakdown"]

        assert breakdown.get("info", 0) == 4
        assert breakdown.get("high", 0) == 2
        assert breakdown.get("critical", 0) == 1

    def test_report_compliance_status_compliant(self, client, admin_auth_headers):
        """Test compliance status when no critical events"""
        # Post non-critical events
        for i in range(5):
            client.post(
                "/compliance/events",
                json={"event_type": "audit", "description": f"Event {i}", "severity": "info"},
                headers=admin_auth_headers,
            )

        response = client.get("/compliance/report", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["compliance_status"] == "compliant"

    def test_report_compliance_status_needs_review(self, client, admin_auth_headers):
        """Test compliance status when critical events exist"""
        # Post critical event
        client.post(
            "/compliance/events",
            json={
                "event_type": "violation",
                "description": "Critical violation",
                "severity": "critical",
            },
            headers=admin_auth_headers,
        )

        response = client.get("/compliance/report", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["compliance_status"] == "needs_review"

    def test_report_total_events_count(self, client, admin_auth_headers):
        """Test that total events count is accurate"""
        # Post known number of events
        event_count = 10
        for i in range(event_count):
            client.post(
                "/compliance/events",
                json={"event_type": "audit", "description": f"Event {i}", "severity": "info"},
                headers=admin_auth_headers,
            )

        response = client.get("/compliance/report", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == event_count

    def test_report_filters_by_time_range(self, client, admin_auth_headers):
        """Test that report correctly filters events by time range"""
        current_time = int(time.time())

        # Post event outside range (2 hours ago)
        # Note: Can't control timestamp in POST, so this tests default filtering

        # Post events within range
        for i in range(3):
            client.post(
                "/compliance/events",
                json={
                    "event_type": "audit",
                    "description": f"Recent event {i}",
                    "severity": "info",
                },
                headers=admin_auth_headers,
            )

        # Get report for last hour (should include all recent events)
        start_time = current_time - 3600
        response = client.get(
            f"/compliance/report?start_time={start_time}&end_time={current_time}",
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] >= 3

    @pytest.mark.skipif(
        os.getenv("REQUIRE_AUTH", "false").lower() not in {"1", "true", "yes"},
        reason="Auth not required in this environment",
    )
    def test_report_requires_admin_role(self, client, auth_headers):
        """Test that report endpoint requires admin role"""
        response = client.get("/compliance/report", headers=auth_headers)  # Non-admin user

        # Should require admin role
        assert response.status_code in [401, 403]

    @pytest.mark.skipif(
        os.getenv("REQUIRE_AUTH", "false").lower() not in {"1", "true", "yes"},
        reason="Auth not required in this environment",
    )
    def test_report_without_auth(self, client):
        """Test accessing report without authentication"""
        response = client.get("/compliance/report")
        assert response.status_code == 401

    def test_report_has_correlation_id(self, client, admin_auth_headers):
        """Test that report includes correlation ID"""
        response = client.get("/compliance/report", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert validate_correlation_id(data)

    def test_report_generation_timestamp(self, client, admin_auth_headers):
        """Test that report has generation timestamp"""
        before = int(time.time())
        response = client.get("/compliance/report", headers=admin_auth_headers)
        after = int(time.time())

        assert response.status_code == 200
        data = response.json()
        assert "report_generated_at" in data
        assert before <= data["report_generated_at"] <= after + 1

    def test_report_with_multiple_event_types(self, client, admin_auth_headers):
        """Test report with multiple event types"""
        event_configs = [
            ("audit", "info"),
            ("audit", "medium"),
            ("violation", "high"),
            ("violation", "critical"),
            ("regulatory", "medium"),
            ("workflow", "info"),
        ]

        for event_type, severity in event_configs:
            client.post(
                "/compliance/events",
                json={
                    "event_type": event_type,
                    "description": f"{event_type} event",
                    "severity": severity,
                },
                headers=admin_auth_headers,
            )

        response = client.get("/compliance/report", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify multiple types in breakdown
        assert len(data["event_type_breakdown"]) >= 3
        assert len(data["severity_breakdown"]) >= 3

    def test_report_breakdown_sum_matches_total(self, client, admin_auth_headers):
        """Test that breakdown sums match total events"""
        # Post various events
        for i in range(10):
            client.post(
                "/compliance/events",
                json={
                    "event_type": "audit" if i % 2 == 0 else "violation",
                    "description": f"Event {i}",
                    "severity": "info",
                },
                headers=admin_auth_headers,
            )

        response = client.get("/compliance/report", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Sum of event type breakdown should equal total
        type_sum = sum(data["event_type_breakdown"].values())
        assert type_sum == data["total_events"]

        # Sum of severity breakdown should equal total
        severity_sum = sum(data["severity_breakdown"].values())
        assert severity_sum == data["total_events"]
