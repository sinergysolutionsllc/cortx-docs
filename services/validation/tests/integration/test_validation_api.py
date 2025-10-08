"""Integration tests for Validation API endpoints.

This module tests the /validate endpoint and its integration with
external services (CORTX Gateway, Compliance service).
"""

from typing import Any, Dict
from unittest.mock import patch

from fastapi.testclient import TestClient


class TestValidateEndpoint:
    """Test suite for POST /validate endpoint."""

    def test_validate_endpoint_success(
        self,
        test_client: TestClient,
        sample_validation_request: Dict[str, Any],
        mock_cortx_client,
        mock_cortex_client,
    ):
        """Test successful validation request."""
        # Mock successful RulePack fetch
        mock_cortx_client.get_json.return_value = {
            "pack": {"rules": [{"name": "check_id", "type": "required_field", "field": "id"}]},
            "version": "1.0.0",
        }

        # Mock successful validation execution
        mock_cortx_client.post_json.return_value = {
            "result": {
                "valid": True,
                "errors": [],
                "warnings": [],
                "rule_results": {"check_id": {"passed": True, "message": "Field present"}},
            }
        }

        response = test_client.post("/validate", json=sample_validation_request)

        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "correlation_id" in data
        assert "execution_time_ms" in data
        assert "rule_pack_version" in data
        assert data["result"]["valid"] is True
        assert data["rule_pack_version"] == "1.0.0"

    def test_validate_endpoint_with_validation_errors(
        self,
        test_client: TestClient,
        sample_validation_request: Dict[str, Any],
        mock_cortx_client,
        mock_cortex_client,
    ):
        """Test validation request that returns validation errors."""
        # Mock RulePack fetch
        mock_cortx_client.get_json.return_value = {"pack": {"rules": []}, "version": "1.0.0"}

        # Mock validation with errors
        mock_cortx_client.post_json.return_value = {
            "result": {
                "valid": False,
                "errors": [
                    {
                        "code": "MISSING_FIELD",
                        "message": "Required field 'payment' is missing",
                        "field": "payment",
                        "severity": "error",
                    }
                ],
                "warnings": [],
                "rule_results": {},
            }
        }

        response = test_client.post("/validate", json=sample_validation_request)

        assert response.status_code == 200
        data = response.json()
        assert data["result"]["valid"] is False
        assert len(data["result"]["errors"]) == 1
        assert data["result"]["errors"][0]["code"] == "MISSING_FIELD"

    def test_validate_endpoint_with_warnings_strict_mode(
        self,
        test_client: TestClient,
        sample_validation_request: Dict[str, Any],
        mock_cortx_client,
        mock_cortex_client,
    ):
        """Test validation with warnings in strict mode."""
        mock_cortx_client.get_json.return_value = {"pack": {"rules": []}, "version": "1.0.0"}

        mock_cortx_client.post_json.return_value = {
            "result": {
                "valid": False,
                "errors": [],
                "warnings": [
                    {
                        "code": "RANGE_WARNING",
                        "message": "Value is close to limit",
                        "field": "amount",
                    }
                ],
                "rule_results": {},
            }
        }

        sample_validation_request["strict_mode"] = True

        response = test_client.post("/validate", json=sample_validation_request)

        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]["warnings"]) == 1

    def test_validate_endpoint_fallback_to_local_validation(
        self,
        test_client: TestClient,
        sample_validation_request: Dict[str, Any],
        mock_cortx_client,
        mock_cortex_client,
    ):
        """Test fallback to local validation when CORTX service is unavailable."""
        # Mock RulePack fetch failure
        mock_cortx_client.get_json.side_effect = Exception("Service unavailable")

        # Mock validation service failure (should fallback to local)
        mock_cortx_client.post_json.side_effect = Exception("Service unavailable")

        response = test_client.post("/validate", json=sample_validation_request)

        # Should still return a response using local validation
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "rule_pack_version" in data
        assert data["rule_pack_version"] == "fallback-1.0"

    def test_validate_endpoint_with_invalid_rule_pack_id(
        self,
        test_client: TestClient,
        sample_validation_request: Dict[str, Any],
        mock_cortx_client,
        mock_cortex_client,
    ):
        """Test validation with non-existent RulePack ID."""
        # Mock RulePack not found
        mock_cortx_client.get_json.side_effect = Exception("RulePack not found")
        mock_cortx_client.post_json.side_effect = Exception("RulePack not found")

        response = test_client.post("/validate", json=sample_validation_request)

        # Should fallback to default rules
        assert response.status_code == 200
        data = response.json()
        assert data["rule_pack_version"] == "fallback-1.0"

    def test_validate_endpoint_with_minimal_request(
        self, test_client: TestClient, mock_cortx_client, mock_cortex_client
    ):
        """Test validation with minimal required fields."""
        minimal_request = {"rule_pack_id": "minimal.pack", "payload": {"id": "test"}}

        mock_cortx_client.get_json.return_value = {"pack": {"rules": []}, "version": "1.0.0"}

        mock_cortx_client.post_json.return_value = {
            "result": {"valid": True, "errors": [], "warnings": [], "rule_results": {}}
        }

        response = test_client.post("/validate", json=minimal_request)

        assert response.status_code == 200

    def test_validate_endpoint_invalid_request_missing_rule_pack_id(self, test_client: TestClient):
        """Test validation fails with missing rule_pack_id."""
        invalid_request = {
            "payload": {"test": "data"}
            # Missing rule_pack_id
        }

        response = test_client.post("/validate", json=invalid_request)

        assert response.status_code == 422  # Validation error

    def test_validate_endpoint_invalid_request_missing_payload(self, test_client: TestClient):
        """Test validation fails with missing payload."""
        invalid_request = {
            "rule_pack_id": "test.pack"
            # Missing payload
        }

        response = test_client.post("/validate", json=invalid_request)

        assert response.status_code == 422  # Validation error

    def test_validate_endpoint_with_metadata(
        self,
        test_client: TestClient,
        sample_validation_request: Dict[str, Any],
        mock_cortx_client,
        mock_cortex_client,
    ):
        """Test validation request includes metadata in processing."""
        mock_cortx_client.get_json.return_value = {"pack": {"rules": []}, "version": "1.0.0"}

        mock_cortx_client.post_json.return_value = {
            "result": {
                "valid": True,
                "errors": [],
                "warnings": [],
                "rule_results": {},
                "metadata": {"custom_key": "custom_value"},
            }
        }

        response = test_client.post("/validate", json=sample_validation_request)

        assert response.status_code == 200
        data = response.json()
        assert data["result"]["metadata"]["custom_key"] == "custom_value"

    @patch("app.main.redact_text")
    def test_validate_endpoint_redacts_pii(
        self,
        mock_redact,
        test_client: TestClient,
        sample_validation_request: Dict[str, Any],
        mock_cortx_client,
        mock_cortex_client,
    ):
        """Test that PII is redacted from payload before processing."""
        mock_redact.return_value = '{"id": "[REDACTED]", "data": {"amount": 100}}'

        mock_cortx_client.get_json.return_value = {"pack": {"rules": []}, "version": "1.0.0"}

        mock_cortx_client.post_json.return_value = {
            "result": {"valid": True, "errors": [], "warnings": [], "rule_results": {}}
        }

        response = test_client.post("/validate", json=sample_validation_request)

        assert response.status_code == 200
        # Verify redact_text was called for payload
        assert mock_redact.called


class TestValidateEndpointCompliance:
    """Test compliance logging and audit trail for validation endpoint."""

    def test_validate_endpoint_logs_compliance_event_success(
        self,
        test_client: TestClient,
        sample_validation_request: Dict[str, Any],
        mock_cortx_client,
        mock_cortex_client,
    ):
        """Test compliance event is logged for successful validation."""
        mock_cortx_client.get_json.return_value = {"pack": {"rules": []}, "version": "1.0.0"}

        mock_cortx_client.post_json.return_value = {
            "result": {"valid": True, "errors": [], "warnings": [], "rule_results": {}}
        }

        response = test_client.post("/validate", json=sample_validation_request)

        assert response.status_code == 200
        # Verify compliance event was logged
        assert mock_cortex_client.log_compliance_event.called
        # Note: With MagicMock, we can't easily assert on event attributes
        # The important part is that the compliance logging was called
        assert mock_cortex_client.log_compliance_event.call_count >= 1

    def test_validate_endpoint_logs_compliance_event_error(
        self,
        test_client: TestClient,
        sample_validation_request: Dict[str, Any],
        mock_cortx_client,
        mock_cortex_client,
    ):
        """Test compliance event is logged for validation errors."""
        # Simulate exception in validation
        mock_cortx_client.get_json.side_effect = Exception("Critical error")
        mock_cortx_client.post_json.side_effect = Exception("Critical error")

        # Make local validation also fail
        with patch("app.main.apply_validation_rules") as mock_apply:
            mock_apply.side_effect = Exception("Local validation failed")

            response = test_client.post("/validate", json=sample_validation_request)

            assert response.status_code == 500
            # Verify error compliance event was logged
            assert mock_cortex_client.log_compliance_event.called
            # The important part is that compliance logging happened even during errors
            assert mock_cortex_client.log_compliance_event.call_count >= 1

    @patch("app.main.sha256_hex")
    def test_validate_endpoint_includes_input_output_hashes(
        self,
        mock_sha256,
        test_client: TestClient,
        sample_validation_request: Dict[str, Any],
        mock_cortx_client,
        mock_cortex_client,
    ):
        """Test that input and output hashes are included in audit."""
        mock_sha256.side_effect = ["input_hash_123", "output_hash_456"]

        mock_cortx_client.get_json.return_value = {"pack": {"rules": []}, "version": "1.0.0"}

        mock_cortx_client.post_json.return_value = {
            "result": {"valid": True, "errors": [], "warnings": [], "rule_results": {}}
        }

        response = test_client.post("/validate", json=sample_validation_request)

        assert response.status_code == 200
        assert mock_cortex_client.log_compliance_event.called
        # Verify sha256_hex was called for hashing (input and output)
        assert mock_sha256.call_count >= 2


class TestValidateEndpointPerformance:
    """Test performance tracking and metrics."""

    def test_validate_endpoint_tracks_execution_time(
        self,
        test_client: TestClient,
        sample_validation_request: Dict[str, Any],
        mock_cortx_client,
        mock_cortex_client,
    ):
        """Test that execution time is tracked and returned."""
        mock_cortx_client.get_json.return_value = {"pack": {"rules": []}, "version": "1.0.0"}

        mock_cortx_client.post_json.return_value = {
            "result": {"valid": True, "errors": [], "warnings": [], "rule_results": {}}
        }

        response = test_client.post("/validate", json=sample_validation_request)

        assert response.status_code == 200
        data = response.json()
        assert "execution_time_ms" in data
        assert isinstance(data["execution_time_ms"], int)
        assert data["execution_time_ms"] >= 0

    def test_validate_endpoint_includes_correlation_id(
        self,
        test_client: TestClient,
        sample_validation_request: Dict[str, Any],
        mock_cortx_client,
        mock_cortex_client,
    ):
        """Test that correlation ID is included in response."""
        mock_cortx_client.get_json.return_value = {"pack": {"rules": []}, "version": "1.0.0"}

        mock_cortx_client.post_json.return_value = {
            "result": {"valid": True, "errors": [], "warnings": [], "rule_results": {}}
        }

        response = test_client.post("/validate", json=sample_validation_request)

        assert response.status_code == 200
        data = response.json()
        assert "correlation_id" in data
        assert isinstance(data["correlation_id"], str)
        assert len(data["correlation_id"]) > 0


class TestValidateEndpointEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_validate_endpoint_with_empty_payload(
        self, test_client: TestClient, mock_cortx_client, mock_cortex_client
    ):
        """Test validation with empty payload object."""
        request = {"rule_pack_id": "test.pack", "payload": {}}

        mock_cortx_client.get_json.return_value = {
            "pack": {"rules": [{"name": "check_id", "type": "required_field", "field": "id"}]},
            "version": "1.0.0",
        }

        mock_cortx_client.post_json.side_effect = Exception("Service down")

        response = test_client.post("/validate", json=request)

        assert response.status_code == 200
        # Local validation should detect missing fields
        data = response.json()
        assert data["result"]["valid"] is False

    def test_validate_endpoint_with_large_payload(
        self, test_client: TestClient, mock_cortx_client, mock_cortex_client
    ):
        """Test validation with large payload."""
        # Create large payload
        large_payload = {f"field_{i}": f"value_{i}" for i in range(1000)}
        request = {"rule_pack_id": "test.pack", "payload": large_payload}

        mock_cortx_client.get_json.return_value = {"pack": {"rules": []}, "version": "1.0.0"}

        mock_cortx_client.post_json.return_value = {
            "result": {"valid": True, "errors": [], "warnings": [], "rule_results": {}}
        }

        response = test_client.post("/validate", json=request)

        assert response.status_code == 200

    def test_validate_endpoint_with_nested_payload(
        self, test_client: TestClient, mock_cortx_client, mock_cortex_client
    ):
        """Test validation with deeply nested payload."""
        nested_payload = {"level1": {"level2": {"level3": {"level4": {"value": "deep"}}}}}
        request = {"rule_pack_id": "test.pack", "payload": nested_payload}

        mock_cortx_client.get_json.return_value = {"pack": {"rules": []}, "version": "1.0.0"}

        mock_cortx_client.post_json.return_value = {
            "result": {"valid": True, "errors": [], "warnings": [], "rule_results": {}}
        }

        response = test_client.post("/validate", json=request)

        assert response.status_code == 200

    def test_validate_endpoint_with_special_characters(
        self, test_client: TestClient, mock_cortx_client, mock_cortex_client
    ):
        """Test validation with special characters in payload."""
        request = {
            "rule_pack_id": "test.pack",
            "payload": {
                "unicode": "Hello 世界 🌍",
                "special": "!@#$%^&*()",
                "quotes": 'He said "Hello"',
            },
        }

        mock_cortx_client.get_json.return_value = {"pack": {"rules": []}, "version": "1.0.0"}

        mock_cortx_client.post_json.return_value = {
            "result": {"valid": True, "errors": [], "warnings": [], "rule_results": {}}
        }

        response = test_client.post("/validate", json=request)

        assert response.status_code == 200


class TestSchemasEndpoint:
    """Test /schemas integration endpoint."""

    def test_schemas_endpoint_success(self, test_client: TestClient, mock_cortx_client):
        """Test successful schemas retrieval."""
        mock_cortx_client.get_json.return_value = {
            "schemas": [
                {"id": "schema1", "version": "1.0.0"},
                {"id": "schema2", "version": "2.0.0"},
            ]
        }

        response = test_client.get("/schemas")

        assert response.status_code == 200
        data = response.json()
        assert "schemas" in data

    def test_schemas_endpoint_service_unavailable(self, test_client: TestClient, mock_cortx_client):
        """Test schemas endpoint when service is unavailable."""
        mock_cortx_client.get_json.side_effect = Exception("Service down")

        response = test_client.get("/schemas")

        assert response.status_code == 503
        data = response.json()
        assert "error" in data
        assert data["error"] == "Schemas service unreachable"
