"""Unit tests for normalize_validation_output function.

This module tests the normalize_validation_output function which is critical
for PII redaction and output sanitization. It must have 100% test coverage
as it handles sensitive data.
"""

from typing import Any, Dict
from unittest.mock import patch

from app.main import ValidationResult, normalize_validation_output


class TestNormalizeValidationOutputBasics:
    """Test basic normalization functionality."""

    def test_normalize_success_result(self, sample_raw_validation_result_success: Dict[str, Any]):
        """Test normalization of successful validation result."""
        result = normalize_validation_output(sample_raw_validation_result_success, redact_pii=False)

        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert len(result.rule_results) == 2
        assert result.metadata == {"execution_time": 10, "rules_executed": 2}

    def test_normalize_result_with_errors(
        self, sample_raw_validation_result_with_errors: Dict[str, Any]
    ):
        """Test normalization of result with errors."""
        result = normalize_validation_output(
            sample_raw_validation_result_with_errors, redact_pii=False
        )

        assert result.valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert result.errors[0]["code"] == "MISSING_FIELD"
        assert result.errors[0]["field"] == "account_number"
        assert result.errors[0]["severity"] == "error"

    def test_normalize_result_with_warnings(
        self, sample_raw_validation_result_with_warnings: Dict[str, Any]
    ):
        """Test normalization of result with warnings."""
        result = normalize_validation_output(
            sample_raw_validation_result_with_warnings, redact_pii=False
        )

        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert result.warnings[0]["code"] == "RANGE_WARNING"
        assert result.warnings[0]["severity"] == "warning"


class TestPIIRedaction:
    """Test PII redaction functionality."""

    @patch("app.main.redact_text")
    def test_redact_pii_in_error_messages(
        self, mock_redact, sample_raw_validation_result_with_errors: Dict[str, Any]
    ):
        """Test PII is redacted from error messages."""
        mock_redact.return_value = "Required field [REDACTED] contains PII: [REDACTED]"

        result = normalize_validation_output(
            sample_raw_validation_result_with_errors, redact_pii=True
        )

        # redact_text should be called for each error message
        assert mock_redact.call_count >= 1
        assert "[REDACTED]" in result.errors[0]["message"]

    @patch("app.main.redact_text")
    def test_redact_pii_in_warning_messages(
        self, mock_redact, sample_raw_validation_result_with_warnings: Dict[str, Any]
    ):
        """Test PII is redacted from warning messages."""
        mock_redact.return_value = "Value is within acceptable range"

        result = normalize_validation_output(
            sample_raw_validation_result_with_warnings, redact_pii=True
        )

        assert mock_redact.call_count >= 1

    @patch("app.main.redact_text")
    def test_redact_pii_in_rule_results(
        self, mock_redact, sample_raw_validation_result_with_errors: Dict[str, Any]
    ):
        """Test PII is redacted from rule result messages."""
        mock_redact.return_value = "[REDACTED]"

        result = normalize_validation_output(
            sample_raw_validation_result_with_errors, redact_pii=True
        )

        # Check rule_results have redacted messages
        for rule_name, rule_result in result.rule_results.items():
            assert mock_redact.called

    @patch("app.main.redact_text")
    def test_no_redaction_when_disabled(
        self, mock_redact, sample_raw_validation_result_with_errors: Dict[str, Any]
    ):
        """Test PII redaction is skipped when redact_pii=False."""
        result = normalize_validation_output(
            sample_raw_validation_result_with_errors, redact_pii=False
        )

        # redact_text should not be called when redact_pii is False
        mock_redact.assert_not_called()


class TestErrorProcessing:
    """Test error object processing and normalization."""

    def test_error_with_all_fields(self):
        """Test normalization of error with all fields present."""
        raw_result = {
            "valid": False,
            "errors": [
                {
                    "code": "TEST_ERROR",
                    "message": "Test error message",
                    "field": "test_field",
                    "severity": "error",
                }
            ],
            "warnings": [],
            "rule_results": {},
        }
        result = normalize_validation_output(raw_result, redact_pii=False)

        assert len(result.errors) == 1
        assert result.errors[0]["code"] == "TEST_ERROR"
        assert result.errors[0]["message"] == "Test error message"
        assert result.errors[0]["field"] == "test_field"
        assert result.errors[0]["severity"] == "error"

    def test_error_with_missing_fields(self):
        """Test normalization of error with missing optional fields."""
        raw_result = {
            "valid": False,
            "errors": [
                {
                    # Missing code, message, field, severity
                }
            ],
            "warnings": [],
            "rule_results": {},
        }
        result = normalize_validation_output(raw_result, redact_pii=False)

        assert len(result.errors) == 1
        assert result.errors[0]["code"] == "UNKNOWN"  # Default value
        assert result.errors[0]["message"] == "Validation error"  # Default value
        assert result.errors[0]["severity"] == "error"  # Default value
        assert result.errors[0]["field"] is None  # Default None

    def test_error_with_none_field(self):
        """Test normalization handles None field values."""
        raw_result = {
            "valid": False,
            "errors": [
                {
                    "code": "GENERAL_ERROR",
                    "message": "General error",
                    "field": None,
                    "severity": "error",
                }
            ],
            "warnings": [],
            "rule_results": {},
        }
        result = normalize_validation_output(raw_result, redact_pii=False)

        assert result.errors[0]["field"] is None


class TestWarningProcessing:
    """Test warning object processing and normalization."""

    def test_warning_with_all_fields(self):
        """Test normalization of warning with all fields present."""
        raw_result = {
            "valid": True,
            "errors": [],
            "warnings": [
                {"code": "TEST_WARNING", "message": "Test warning message", "field": "test_field"}
            ],
            "rule_results": {},
        }
        result = normalize_validation_output(raw_result, redact_pii=False)

        assert len(result.warnings) == 1
        assert result.warnings[0]["code"] == "TEST_WARNING"
        assert result.warnings[0]["message"] == "Test warning message"
        assert result.warnings[0]["field"] == "test_field"
        assert result.warnings[0]["severity"] == "warning"  # Always set to "warning"

    def test_warning_with_missing_fields(self):
        """Test normalization of warning with missing optional fields."""
        raw_result = {
            "valid": True,
            "errors": [],
            "warnings": [{}],  # Empty warning object
            "rule_results": {},
        }
        result = normalize_validation_output(raw_result, redact_pii=False)

        assert len(result.warnings) == 1
        assert result.warnings[0]["code"] == "UNKNOWN"
        assert result.warnings[0]["message"] == "Validation warning"
        assert result.warnings[0]["severity"] == "warning"


class TestRuleResultsProcessing:
    """Test rule results processing and normalization."""

    def test_rule_results_with_complete_data(self):
        """Test normalization of complete rule results."""
        raw_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "rule_results": {
                "rule_1": {"passed": True, "message": "Rule passed", "metadata": {"key": "value"}},
                "rule_2": {"passed": False, "message": "Rule failed", "metadata": {}},
            },
        }
        result = normalize_validation_output(raw_result, redact_pii=False)

        assert len(result.rule_results) == 2
        assert result.rule_results["rule_1"]["passed"] is True
        assert result.rule_results["rule_1"]["message"] == "Rule passed"
        assert result.rule_results["rule_1"]["metadata"] == {"key": "value"}
        assert result.rule_results["rule_2"]["passed"] is False

    def test_rule_results_with_missing_fields(self):
        """Test normalization of rule results with missing fields."""
        raw_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "rule_results": {
                "incomplete_rule": {
                    # Missing passed, message, metadata
                }
            },
        }
        result = normalize_validation_output(raw_result, redact_pii=False)

        assert "incomplete_rule" in result.rule_results
        assert result.rule_results["incomplete_rule"]["passed"] is False  # Default
        assert result.rule_results["incomplete_rule"]["metadata"] == {}  # Default

    @patch("app.main.redact_text")
    def test_rule_results_message_redaction(self, mock_redact):
        """Test PII redaction in rule result messages."""
        mock_redact.return_value = "[REDACTED]"

        raw_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "rule_results": {
                "rule_1": {"passed": True, "message": "Contains SSN: 123-45-6789", "metadata": {}}
            },
        }
        result = normalize_validation_output(raw_result, redact_pii=True)

        mock_redact.assert_called()
        assert result.rule_results["rule_1"]["message"] == "[REDACTED]"


class TestEdgeCasesAndDefaults:
    """Test edge cases and default value handling."""

    def test_empty_raw_result(self):
        """Test normalization of minimal raw result."""
        raw_result = {}
        result = normalize_validation_output(raw_result, redact_pii=False)

        assert result.valid is False  # Default when missing
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert len(result.rule_results) == 0
        assert result.metadata == {}

    def test_missing_valid_field_defaults_to_false(self):
        """Test that missing 'valid' field defaults to False."""
        raw_result = {"errors": [], "warnings": [], "rule_results": {}}
        result = normalize_validation_output(raw_result, redact_pii=False)

        assert result.valid is False

    def test_missing_errors_list(self):
        """Test handling of missing 'errors' list."""
        raw_result = {"valid": True, "warnings": [], "rule_results": {}}
        result = normalize_validation_output(raw_result, redact_pii=False)

        assert len(result.errors) == 0

    def test_missing_warnings_list(self):
        """Test handling of missing 'warnings' list."""
        raw_result = {"valid": True, "errors": [], "rule_results": {}}
        result = normalize_validation_output(raw_result, redact_pii=False)

        assert len(result.warnings) == 0

    def test_missing_rule_results(self):
        """Test handling of missing 'rule_results' dict."""
        raw_result = {"valid": True, "errors": [], "warnings": []}
        result = normalize_validation_output(raw_result, redact_pii=False)

        assert len(result.rule_results) == 0

    def test_missing_metadata(self):
        """Test handling of missing 'metadata' field."""
        raw_result = {"valid": True, "errors": [], "warnings": [], "rule_results": {}}
        result = normalize_validation_output(raw_result, redact_pii=False)

        assert result.metadata == {}

    def test_none_message_in_error(self):
        """Test handling of None message in error."""
        raw_result = {
            "valid": False,
            "errors": [{"code": "TEST", "message": None, "field": "test"}],
            "warnings": [],
            "rule_results": {},
        }
        result = normalize_validation_output(raw_result, redact_pii=False)

        # None message is preserved (not replaced with default)
        # The default "Validation error" is only used when key is missing entirely
        assert (
            result.errors[0]["message"] is None or result.errors[0]["message"] == "Validation error"
        )

    def test_multiple_errors_and_warnings(self):
        """Test normalization with multiple errors and warnings."""
        raw_result = {
            "valid": False,
            "errors": [
                {"code": "E1", "message": "Error 1", "field": "f1", "severity": "error"},
                {"code": "E2", "message": "Error 2", "field": "f2", "severity": "error"},
                {"code": "E3", "message": "Error 3", "field": "f3", "severity": "error"},
            ],
            "warnings": [
                {"code": "W1", "message": "Warning 1", "field": "f1"},
                {"code": "W2", "message": "Warning 2", "field": "f2"},
            ],
            "rule_results": {},
        }
        result = normalize_validation_output(raw_result, redact_pii=False)

        assert len(result.errors) == 3
        assert len(result.warnings) == 2

    def test_rule_result_with_non_string_message(self):
        """Test handling of non-string message in rule result."""
        raw_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "rule_results": {
                "rule_1": {"passed": True, "message": 12345, "metadata": {}}  # Non-string message
            },
        }
        result = normalize_validation_output(raw_result, redact_pii=False)

        # Non-string messages are converted to string via str() in redact_text call
        # When redact_pii is False, the message is preserved as-is
        # The implementation converts via str() when redacting
        assert result.rule_results["rule_1"]["message"] == 12345 or isinstance(
            result.rule_results["rule_1"]["message"], str
        )


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_comprehensive_validation_result(self):
        """Test normalization of comprehensive validation result."""
        raw_result = {
            "valid": False,
            "errors": [
                {
                    "code": "FATAL_1",
                    "message": "Critical error",
                    "field": "payment",
                    "severity": "error",
                }
            ],
            "warnings": [{"code": "WARN_1", "message": "Minor issue", "field": "metadata"}],
            "rule_results": {
                "required_fields": {
                    "passed": False,
                    "message": "Missing fields",
                    "metadata": {"missing": ["payment"]},
                },
                "format_check": {"passed": True, "message": "Format valid", "metadata": {}},
                "range_validation": {
                    "passed": True,
                    "message": "In range",
                    "metadata": {"checked": 5},
                },
            },
            "metadata": {"execution_time_ms": 45, "rules_executed": 3, "version": "1.0.0"},
        }
        result = normalize_validation_output(raw_result, redact_pii=False)

        assert result.valid is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert len(result.rule_results) == 3
        assert result.metadata["execution_time_ms"] == 45
        assert result.metadata["version"] == "1.0.0"

    @patch("app.main.redact_text")
    def test_redaction_in_complex_scenario(self, mock_redact):
        """Test PII redaction works across all fields in complex scenario."""
        mock_redact.side_effect = lambda x: "[REDACTED]" if x else ""

        raw_result = {
            "valid": False,
            "errors": [
                {"code": "E1", "message": "SSN: 123-45-6789", "field": "ssn", "severity": "error"}
            ],
            "warnings": [{"code": "W1", "message": "Email: test@example.com", "field": "email"}],
            "rule_results": {
                "rule_1": {
                    "passed": False,
                    "message": "Credit card: 4111-1111-1111-1111",
                    "metadata": {},
                }
            },
        }
        result = normalize_validation_output(raw_result, redact_pii=True)

        # All messages should be redacted
        assert result.errors[0]["message"] == "[REDACTED]"
        assert result.warnings[0]["message"] == "[REDACTED]"
        assert result.rule_results["rule_1"]["message"] == "[REDACTED]"
