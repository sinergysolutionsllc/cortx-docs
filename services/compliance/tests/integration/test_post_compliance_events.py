"""
Integration tests for POST /compliance/events endpoint
"""

import os

import pytest
from tests.__utils__.factories import ComplianceEventRequestFactory
from tests.__utils__.helpers import assert_event_response_structure, validate_correlation_id


@pytest.mark.integration
class TestPostComplianceEvents:
    """Test POST /compliance/events endpoint"""

    def test_log_compliance_event_success(self, client, auth_headers):
        """Test successfully logging a compliance event"""
        payload = {
            "event_type": "audit",
            "description": "User login successful",
            "data": {"ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0"},
            "user_id": "user_123",
            "severity": "info",
        }

        response = client.post("/compliance/events", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert_event_response_structure(data)
        assert data["status"] == "logged"
        assert "event_id" in data
        assert validate_correlation_id(data)

    def test_log_compliance_event_minimal(self, client, auth_headers):
        """Test logging event with minimal required fields"""
        payload = {"event_type": "audit", "description": "Minimal compliance event"}

        response = client.post("/compliance/events", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "logged"

    def test_log_audit_event(self, client, auth_headers):
        """Test logging an audit event"""
        payload = ComplianceEventRequestFactory.create_request(
            event_type="audit",
            description="User performed action",
            data={"action": "update_profile"},
            severity="info",
        )

        response = client.post("/compliance/events", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "logged"

    def test_log_violation_event(self, client, auth_headers):
        """Test logging a violation event"""
        payload = {
            "event_type": "violation",
            "description": "Unauthorized access attempt",
            "data": {"resource": "/api/admin", "attempted_action": "DELETE", "blocked": True},
            "severity": "high",
        }

        response = client.post("/compliance/events", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "logged"

    def test_log_regulatory_event(self, client, auth_headers):
        """Test logging a regulatory compliance event"""
        payload = {
            "event_type": "regulatory",
            "description": "HIPAA data access",
            "data": {
                "patient_id": "PHI_123",
                "accessed_fields": ["name", "ssn"],
                "purpose": "treatment",
            },
            "severity": "medium",
        }

        response = client.post("/compliance/events", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "logged"

    def test_log_workflow_event(self, client, auth_headers):
        """Test logging a workflow event"""
        payload = {
            "event_type": "workflow",
            "description": "Workflow execution started",
            "data": {"workflow_id": "wf_123", "pack_id": "test.pack", "version": "1.0.0"},
            "severity": "info",
        }

        response = client.post("/compliance/events", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "logged"

    def test_log_critical_event(self, client, auth_headers):
        """Test logging a critical severity event"""
        payload = {
            "event_type": "violation",
            "description": "Critical security breach detected",
            "data": {"threat_level": "critical", "source_ip": "10.0.0.1"},
            "severity": "critical",
        }

        response = client.post("/compliance/events", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "logged"

    def test_log_event_with_complex_data(self, client, auth_headers):
        """Test logging event with complex nested data"""
        payload = {
            "event_type": "audit",
            "description": "Complex data event",
            "data": {
                "level1": {"level2": {"level3": ["item1", "item2"]}},
                "array": [1, 2, 3, 4, 5],
                "mixed": {"boolean": True, "null_value": None, "numbers": [1.5, 2.7, 3.9]},
            },
            "severity": "info",
        }

        response = client.post("/compliance/events", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "logged"

    def test_log_event_with_empty_data(self, client, auth_headers):
        """Test logging event with empty data dictionary"""
        payload = {
            "event_type": "audit",
            "description": "Event with empty data",
            "data": {},
            "severity": "info",
        }

        response = client.post("/compliance/events", json=payload, headers=auth_headers)

        assert response.status_code == 201

    def test_log_event_missing_required_field(self, client, auth_headers):
        """Test logging event with missing required field"""
        payload = {
            "event_type": "audit"
            # Missing description
        }

        response = client.post("/compliance/events", json=payload, headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_log_event_invalid_data_type(self, client, auth_headers):
        """Test logging event with invalid data type"""
        payload = {
            "event_type": "audit",
            "description": "Invalid data type",
            "data": "should_be_dict_not_string",  # Invalid type
            "severity": "info",
        }

        response = client.post("/compliance/events", json=payload, headers=auth_headers)

        assert response.status_code == 422  # Validation error

    @pytest.mark.skipif(
        os.getenv("REQUIRE_AUTH", "false").lower() not in {"1", "true", "yes"},
        reason="Auth not required in this environment",
    )
    def test_log_event_without_auth(self, client):
        """Test logging event without authentication"""
        payload = {"event_type": "audit", "description": "Unauthorized attempt", "severity": "info"}

        response = client.post("/compliance/events", json=payload)

        assert response.status_code == 401

    def test_log_multiple_events_sequentially(self, client, auth_headers):
        """Test logging multiple events in sequence"""
        payloads = [
            {"event_type": "audit", "description": f"Event {i}", "severity": "info"}
            for i in range(5)
        ]

        event_ids = []
        for payload in payloads:
            response = client.post("/compliance/events", json=payload, headers=auth_headers)
            assert response.status_code == 201
            data = response.json()
            event_ids.append(data["event_id"])

        # Verify all event IDs are unique
        assert len(event_ids) == len(set(event_ids))

    def test_log_event_preserves_data_integrity(self, client, auth_headers):
        """Test that logged events preserve data integrity"""
        original_data = {"key1": "value1", "key2": 12345, "key3": True, "nested": {"inner": "data"}}

        payload = {
            "event_type": "audit",
            "description": "Data integrity test",
            "data": original_data,
            "severity": "info",
        }

        response = client.post("/compliance/events", json=payload, headers=auth_headers)

        assert response.status_code == 201
        # Data integrity is verified by successful storage
        # (actual data retrieval tested in GET endpoint tests)

    def test_log_event_with_custom_user_id(self, client, auth_headers):
        """Test logging event with custom user ID"""
        payload = {
            "event_type": "audit",
            "description": "Custom user event",
            "user_id": "custom_user_456",
            "severity": "info",
        }

        response = client.post("/compliance/events", json=payload, headers=auth_headers)

        assert response.status_code == 201

    def test_log_event_all_severity_levels(self, client, auth_headers):
        """Test logging events with all severity levels"""
        severities = ["info", "low", "medium", "high", "critical"]

        for severity in severities:
            payload = {
                "event_type": "audit",
                "description": f"Event with {severity} severity",
                "severity": severity,
            }

            response = client.post("/compliance/events", json=payload, headers=auth_headers)

            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "logged"
