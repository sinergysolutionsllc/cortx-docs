"""Unit tests for core validation logic and rule execution.

This module tests the apply_validation_rules function which is the core
validation engine. It must have 100% test coverage as specified in the
quality-assurance-lead guidelines.
"""

from typing import Any, Dict

from app.main import apply_validation_rules


class TestRequiredFieldValidation:
    """Test suite for required_field rule type."""

    def test_required_field_present(self, sample_rule_pack: Dict[str, Any]):
        """Test validation passes when required field is present."""
        payload = {"id": "test-123", "data": {"key": "value"}}
        result = apply_validation_rules(payload, sample_rule_pack, strict_mode=True)

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert "check_id" in result["rule_results"]
        assert result["rule_results"]["check_id"]["passed"] is True

    def test_required_field_missing(self, sample_rule_pack: Dict[str, Any]):
        """Test validation fails when required field is missing."""
        payload = {"data": {"key": "value"}}  # Missing 'id'
        result = apply_validation_rules(payload, sample_rule_pack, strict_mode=True)

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["code"] == "MISSING_REQUIRED_FIELD"
        assert result["errors"][0]["field"] == "id"
        assert "check_id" in result["rule_results"]
        assert result["rule_results"]["check_id"]["passed"] is False

    def test_multiple_required_fields_missing(self, sample_rule_pack: Dict[str, Any]):
        """Test validation fails when multiple required fields are missing."""
        payload = {}  # Both 'id' and 'data' missing
        result = apply_validation_rules(payload, sample_rule_pack, strict_mode=True)

        assert result["valid"] is False
        assert len(result["errors"]) == 2
        error_codes = [e["code"] for e in result["errors"]]
        assert all(code == "MISSING_REQUIRED_FIELD" for code in error_codes)

    def test_required_field_with_none_value(self, sample_rule_pack: Dict[str, Any]):
        """Test that None value is different from missing field."""
        # None value should still be considered "present" (field exists)
        payload = {"id": None, "data": {"key": "value"}}
        result = apply_validation_rules(payload, sample_rule_pack, strict_mode=True)

        # Field 'id' is present (even if None), so required_field check passes
        assert result["valid"] is True


class TestFormatValidation:
    """Test suite for format_validation rule type."""

    def test_format_validation_valid_email(
        self, sample_rule_pack_with_format_validation: Dict[str, Any]
    ):
        """Test format validation passes for valid email."""
        payload = {"email": "test@example.com", "phone": "1234567890"}
        result = apply_validation_rules(
            payload, sample_rule_pack_with_format_validation, strict_mode=True
        )

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["rule_results"]["email_format"]["passed"] is True

    def test_format_validation_invalid_email(
        self, sample_rule_pack_with_format_validation: Dict[str, Any]
    ):
        """Test format validation fails for invalid email."""
        payload = {"email": "not-an-email", "phone": "1234567890"}
        result = apply_validation_rules(
            payload, sample_rule_pack_with_format_validation, strict_mode=True
        )

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["code"] == "FORMAT_VALIDATION_FAILED"
        assert result["errors"][0]["field"] == "email"
        assert result["rule_results"]["email_format"]["passed"] is False

    def test_format_validation_warning_for_optional_field(
        self, sample_rule_pack_with_format_validation: Dict[str, Any]
    ):
        """Test format validation creates warning for optional field mismatch."""
        payload = {"email": "valid@example.com", "phone": "123"}  # Invalid phone
        result = apply_validation_rules(
            payload, sample_rule_pack_with_format_validation, strict_mode=True
        )

        assert result["valid"] is False  # Strict mode treats warnings as failures
        assert len(result["warnings"]) == 1
        assert result["warnings"][0]["code"] == "FORMAT_VALIDATION_FAILED"
        assert result["warnings"][0]["field"] == "phone"
        assert result["warnings"][0]["severity"] == "warning"

    def test_format_validation_warning_non_strict_mode(
        self, sample_rule_pack_with_format_validation: Dict[str, Any]
    ):
        """Test warnings don't fail validation in non-strict mode."""
        payload = {"email": "valid@example.com", "phone": "123"}  # Invalid phone
        result = apply_validation_rules(
            payload, sample_rule_pack_with_format_validation, strict_mode=False
        )

        assert result["valid"] is True  # Non-strict mode allows warnings
        assert len(result["warnings"]) == 1

    def test_format_validation_missing_field(
        self, sample_rule_pack_with_format_validation: Dict[str, Any]
    ):
        """Test format validation is skipped if field is missing."""
        payload = {"phone": "1234567890"}  # Missing email
        result = apply_validation_rules(
            payload, sample_rule_pack_with_format_validation, strict_mode=True
        )

        # Format validation only runs on present fields
        assert result["valid"] is True
        assert len(result["errors"]) == 0


class TestRangeCheckValidation:
    """Test suite for range_check rule type."""

    def test_range_check_within_bounds(self, sample_rule_pack: Dict[str, Any]):
        """Test range check passes for value within bounds."""
        payload = {"id": "test", "data": {}, "amount": 500}
        result = apply_validation_rules(payload, sample_rule_pack, strict_mode=True)

        assert result["valid"] is True
        assert result["rule_results"]["check_amount_positive"]["passed"] is True

    def test_range_check_below_minimum(self, sample_rule_pack: Dict[str, Any]):
        """Test range check fails for value below minimum."""
        payload = {"id": "test", "data": {}, "amount": -100}
        result = apply_validation_rules(payload, sample_rule_pack, strict_mode=True)

        assert result["valid"] is False  # Strict mode
        assert len(result["warnings"]) == 1
        assert result["warnings"][0]["code"] == "RANGE_CHECK_FAILED"
        assert result["warnings"][0]["field"] == "amount"
        assert result["rule_results"]["check_amount_positive"]["passed"] is False

    def test_range_check_above_maximum(self, sample_rule_pack: Dict[str, Any]):
        """Test range check fails for value above maximum."""
        payload = {"id": "test", "data": {}, "amount": 2000000}
        result = apply_validation_rules(payload, sample_rule_pack, strict_mode=True)

        assert result["valid"] is False
        assert len(result["warnings"]) == 1
        assert result["warnings"][0]["code"] == "RANGE_CHECK_FAILED"

    def test_range_check_at_minimum_boundary(self, sample_rule_pack: Dict[str, Any]):
        """Test range check passes for value exactly at minimum."""
        payload = {"id": "test", "data": {}, "amount": 0}
        result = apply_validation_rules(payload, sample_rule_pack, strict_mode=True)

        assert result["valid"] is True
        assert result["rule_results"]["check_amount_positive"]["passed"] is True

    def test_range_check_at_maximum_boundary(self, sample_rule_pack: Dict[str, Any]):
        """Test range check passes for value exactly at maximum."""
        payload = {"id": "test", "data": {}, "amount": 1000000}
        result = apply_validation_rules(payload, sample_rule_pack, strict_mode=True)

        assert result["valid"] is True
        assert result["rule_results"]["check_amount_positive"]["passed"] is True

    def test_range_check_non_numeric_value(self, sample_rule_pack: Dict[str, Any]):
        """Test range check handles non-numeric values gracefully."""
        payload = {"id": "test", "data": {}, "amount": "not-a-number"}
        result = apply_validation_rules(payload, sample_rule_pack, strict_mode=True)

        # Non-numeric values are silently skipped in range checks
        assert result["valid"] is True

    def test_range_check_missing_field(self, sample_rule_pack: Dict[str, Any]):
        """Test range check is skipped if field is missing."""
        payload = {"id": "test", "data": {}}  # Missing amount
        result = apply_validation_rules(payload, sample_rule_pack, strict_mode=True)

        assert result["valid"] is True

    def test_range_check_strict_vs_non_strict(self, sample_rule_pack: Dict[str, Any]):
        """Test strict mode affects range check warnings."""
        payload = {"id": "test", "data": {}, "amount": -50}

        # Strict mode
        result_strict = apply_validation_rules(payload, sample_rule_pack, strict_mode=True)
        assert result_strict["valid"] is False

        # Non-strict mode
        result_non_strict = apply_validation_rules(payload, sample_rule_pack, strict_mode=False)
        assert result_non_strict["valid"] is True
        assert len(result_non_strict["warnings"]) == 1


class TestCustomRuleType:
    """Test suite for custom rule type."""

    def test_custom_rule_execution(self):
        """Test custom rule type executes successfully."""
        rule_pack = {
            "rules": [{"name": "custom_validation", "type": "custom", "field": "custom_field"}]
        }
        payload = {"custom_field": "test"}
        result = apply_validation_rules(payload, rule_pack, strict_mode=True)

        assert result["valid"] is True
        assert "custom_validation" in result["rule_results"]
        assert result["rule_results"]["custom_validation"]["passed"] is True
        assert result["rule_results"]["custom_validation"]["metadata"]["rule_type"] == "custom"


class TestMultiRuleValidation:
    """Test suite for multiple rules in a single RulePack."""

    def test_all_rules_pass(
        self,
        sample_rule_pack_with_all_operators: Dict[str, Any],
        valid_payload_for_comprehensive_pack: Dict[str, Any],
    ):
        """Test validation when all rules pass."""
        result = apply_validation_rules(
            valid_payload_for_comprehensive_pack,
            sample_rule_pack_with_all_operators,
            strict_mode=True,
        )

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0
        assert len(result["rule_results"]) == 4
        assert all(r["passed"] for r in result["rule_results"].values())

    def test_some_rules_fail(self, sample_rule_pack_with_all_operators: Dict[str, Any]):
        """Test validation when some rules fail."""
        payload = {
            "id": "test-123",
            "amount": 5,  # Below minimum (10)
            "status": "invalid",  # Invalid format
            "custom_field": "test",
        }
        result = apply_validation_rules(
            payload, sample_rule_pack_with_all_operators, strict_mode=True
        )

        assert result["valid"] is False
        assert len(result["warnings"]) >= 1  # Range check warning
        assert len(result["errors"]) >= 1  # Format validation error

    def test_early_vs_complete_validation(
        self, sample_rule_pack_with_all_operators: Dict[str, Any]
    ):
        """Test that all rules are executed (no early termination)."""
        payload = {
            # Missing id
            "amount": 2000,  # Out of range
            "status": "invalid",  # Invalid format
            "custom_field": "test",
        }
        result = apply_validation_rules(
            payload, sample_rule_pack_with_all_operators, strict_mode=True
        )

        # All rules should be executed, collecting all errors
        assert result["valid"] is False
        assert len(result["rule_results"]) == 4  # All 4 rules executed


class TestRuleExecutionErrors:
    """Test suite for error handling during rule execution."""

    def test_rule_execution_exception_handling(self):
        """Test graceful handling of exceptions during rule execution."""
        # Create a rule that will cause an exception
        rule_pack = {
            "rules": [
                {
                    "name": "problematic_rule",
                    "type": "format_validation",
                    "field": "test_field",
                    "pattern": r"(invalid[regex",  # Invalid regex pattern
                }
            ]
        }
        payload = {"test_field": "test"}
        result = apply_validation_rules(payload, rule_pack, strict_mode=True)

        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["code"] == "RULE_EXECUTION_ERROR"
        assert "problematic_rule" in result["errors"][0]["message"]
        assert result["rule_results"]["problematic_rule"]["passed"] is False

    def test_empty_rule_pack(self):
        """Test validation with empty rule pack."""
        rule_pack = {"rules": []}
        payload = {"test": "data"}
        result = apply_validation_rules(payload, rule_pack, strict_mode=True)

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0
        assert len(result["rule_results"]) == 0

    def test_rule_pack_without_rules_key(self):
        """Test validation with malformed rule pack (missing rules key)."""
        rule_pack = {}  # No 'rules' key
        payload = {"test": "data"}
        result = apply_validation_rules(payload, rule_pack, strict_mode=True)

        assert result["valid"] is True  # No rules means validation passes
        assert len(result["rule_results"]) == 0


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_empty_payload(self, sample_rule_pack: Dict[str, Any]):
        """Test validation with empty payload."""
        payload = {}
        result = apply_validation_rules(payload, sample_rule_pack, strict_mode=True)

        assert result["valid"] is False  # Required fields are missing
        assert len(result["errors"]) >= 2  # At least 'id' and 'data' missing

    def test_payload_with_extra_fields(self, sample_rule_pack: Dict[str, Any]):
        """Test validation allows extra fields not in rules."""
        payload = {"id": "test", "data": {}, "extra_field_1": "value1", "extra_field_2": "value2"}
        result = apply_validation_rules(payload, sample_rule_pack, strict_mode=True)

        assert result["valid"] is True  # Extra fields don't cause failures

    def test_nested_field_values(self):
        """Test validation handles nested objects gracefully."""
        rule_pack = {
            "rules": [{"name": "check_nested", "type": "required_field", "field": "nested"}]
        }
        payload = {"nested": {"level1": {"level2": "value"}}}
        result = apply_validation_rules(payload, rule_pack, strict_mode=True)

        assert result["valid"] is True

    def test_unicode_and_special_characters(self):
        """Test validation handles unicode and special characters."""
        rule_pack = {
            "rules": [{"name": "check_field", "type": "required_field", "field": "unicode_field"}]
        }
        payload = {"unicode_field": "Hello 世界 🌍 café"}
        result = apply_validation_rules(payload, rule_pack, strict_mode=True)

        assert result["valid"] is True

    def test_very_large_payload(self):
        """Test validation handles large payloads."""
        rule_pack = {"rules": [{"name": "check_id", "type": "required_field", "field": "id"}]}
        # Create payload with 1000 fields
        payload = {"id": "test"}
        payload.update({f"field_{i}": f"value_{i}" for i in range(1000)})

        result = apply_validation_rules(payload, rule_pack, strict_mode=True)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_rule_without_name(self):
        """Test handling of rule without name field."""
        rule_pack = {
            "rules": [
                {
                    "type": "required_field",
                    "field": "id",
                    # Missing 'name'
                }
            ]
        }
        payload = {"id": "test"}
        result = apply_validation_rules(payload, rule_pack, strict_mode=True)

        assert result["valid"] is True
        assert "unknown_rule" in result["rule_results"]

    def test_float_values_in_range_check(self):
        """Test range check with float values."""
        rule_pack = {
            "rules": [
                {
                    "name": "decimal_check",
                    "type": "range_check",
                    "field": "price",
                    "min": 0.01,
                    "max": 99.99,
                }
            ]
        }
        payload = {"price": 49.99}
        result = apply_validation_rules(payload, rule_pack, strict_mode=True)

        assert result["valid"] is True
        assert result["rule_results"]["decimal_check"]["passed"] is True
