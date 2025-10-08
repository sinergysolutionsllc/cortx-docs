"""
Example RulePack Implementation

This demonstrates how to implement a RulePack using the CORTX RulePack SDK.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from cortx_rulepack_sdk.base import RulePackBase
from cortx_rulepack_sdk.contracts import (
    ExplanationRequest,
    ExplanationResponse,
    RuleInfo,
    RulePackInfo,
    RulePackMetadata,
    SeverityLevel,
    ValidationFailure,
    ValidationMode,
    ValidationRequest,
    ValidationResponse,
    ValidationStats,
)


class ExampleRulePack(RulePackBase):
    """
    Example RulePack that demonstrates basic validation patterns.

    This RulePack validates simple financial records with rules like:
    - Required fields validation
    - Numeric range validation
    - Date format validation
    - Cross-field consistency validation
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.rules: list[dict[str, Any]] = []
        self.domain = "example"
        self.name = "ExampleRulePack"
        self.version = "1.0.0"

    async def initialize(self) -> None:
        """Initialize the RulePack and load rules"""
        await super().initialize()

        # Load rules from config or use defaults
        rules_path = self.get_config("rules_path")
        if rules_path and Path(rules_path).exists():
            with open(rules_path) as f:
                self.rules = json.load(f)
        else:
            # Default rules for demonstration
            self.rules = [
                {
                    "rule_id": "REQ_001",
                    "rule_name": "Required Fields",
                    "category": "structure",
                    "severity": "error",
                    "description": "Ensure all required fields are present",
                    "required_fields": ["account", "amount", "date"],
                    "version": "1.0",
                },
                {
                    "rule_id": "AMT_001",
                    "rule_name": "Amount Range Validation",
                    "category": "business",
                    "severity": "warning",
                    "description": "Amount must be within reasonable range",
                    "min_amount": -1000000,
                    "max_amount": 1000000,
                    "version": "1.0",
                },
                {
                    "rule_id": "DATE_001",
                    "rule_name": "Date Format Validation",
                    "category": "format",
                    "severity": "error",
                    "description": "Date must be in YYYY-MM-DD format",
                    "date_format": "%Y-%m-%d",
                    "version": "1.0",
                },
                {
                    "rule_id": "ACC_001",
                    "rule_name": "Account Code Format",
                    "category": "format",
                    "severity": "error",
                    "description": "Account code must be 6-digit numeric",
                    "pattern": r"^\d{6}$",
                    "version": "1.0",
                },
            ]

        print(f"ExampleRulePack initialized with {len(self.rules)} rules")

    async def validate(self, request: ValidationRequest) -> ValidationResponse:
        """
        Perform validation according to the request mode.
        """
        start_time = datetime.utcnow()
        failures: list[ValidationFailure] = []

        # Handle different input types
        if request.input_type == "records":
            records = (
                request.input_data if isinstance(request.input_data, list) else [request.input_data]
            )
        else:
            # For other input types, assume single record for this example
            records = [request.input_data] if request.input_data else []

        # Validate each record
        for i, record in enumerate(records):
            if not isinstance(record, dict):
                failures.append(
                    ValidationFailure(
                        rule_id="STRUCT_001",
                        rule_name="Record Structure",
                        severity=SeverityLevel.FATAL,
                        line_number=i + 1,
                        failure_description=f"Record must be a dictionary, got {type(record).__name__}",
                        failure_id=str(uuid.uuid4()),
                    )
                )
                continue

            # Run validation rules
            record_failures = await self._validate_record(record, i + 1, request.options.mode)
            failures.extend(record_failures)

            # Respect max_failures limit
            if request.options.max_failures and len(failures) >= request.options.max_failures:
                break

        # Calculate statistics
        end_time = datetime.utcnow()
        processing_time = int((end_time - start_time).total_seconds() * 1000)

        stats = ValidationStats(
            total_records=len(records),
            records_processed=len(records),
            records_failed=len(set(f.line_number for f in failures if f.line_number)),
            total_failures=len(failures),
            fatal_count=sum(1 for f in failures if f.severity == SeverityLevel.FATAL),
            error_count=sum(1 for f in failures if f.severity == SeverityLevel.ERROR),
            warning_count=sum(1 for f in failures if f.severity == SeverityLevel.WARNING),
            info_count=sum(1 for f in failures if f.severity == SeverityLevel.INFO),
            processing_time_ms=processing_time,
            mode_used=request.options.mode,
        )

        return ValidationResponse(
            request_id=request.request_id,
            domain=self.domain,
            success=True,  # Validation completed successfully
            summary=stats,
            failures=failures,
            mode_requested=request.options.mode,
            mode_executed=request.options.mode,
            completed_at=end_time,
        )

    async def _validate_record(
        self, record: dict[str, Any], line_number: int, mode: ValidationMode
    ) -> list[ValidationFailure]:
        """Validate a single record against all rules"""
        failures: list[ValidationFailure] = []

        for rule in self.rules:
            rule_failures = await self._apply_rule(rule, record, line_number)
            failures.extend(rule_failures)

        return failures

    async def _apply_rule(
        self, rule: dict[str, Any], record: dict[str, Any], line_number: int
    ) -> list[ValidationFailure]:
        """Apply a specific rule to a record"""
        failures: list[ValidationFailure] = []
        rule_id = rule["rule_id"]

        try:
            if rule_id == "REQ_001":
                # Required fields validation
                required_fields = rule.get("required_fields", [])
                for field in required_fields:
                    if field not in record or record[field] is None or record[field] == "":
                        failures.append(
                            ValidationFailure(
                                rule_id=rule_id,
                                rule_name=rule["rule_name"],
                                severity=SeverityLevel(rule["severity"]),
                                line_number=line_number,
                                field=field,
                                failure_description=f"Missing required field: {field}",
                                expected_value="non-empty value",
                                actual_value=record.get(field),
                                failure_id=str(uuid.uuid4()),
                            )
                        )

            elif rule_id == "AMT_001":
                # Amount range validation
                if "amount" in record:
                    try:
                        amount = float(record["amount"])
                        min_amount = rule.get("min_amount", float("-inf"))
                        max_amount = rule.get("max_amount", float("inf"))

                        if amount < min_amount or amount > max_amount:
                            failures.append(
                                ValidationFailure(
                                    rule_id=rule_id,
                                    rule_name=rule["rule_name"],
                                    severity=SeverityLevel(rule["severity"]),
                                    line_number=line_number,
                                    field="amount",
                                    failure_description=f"Amount {amount} outside valid range [{min_amount}, {max_amount}]",
                                    expected_value=f"value between {min_amount} and {max_amount}",
                                    actual_value=amount,
                                    failure_id=str(uuid.uuid4()),
                                )
                            )
                    except (ValueError, TypeError):
                        failures.append(
                            ValidationFailure(
                                rule_id=rule_id,
                                rule_name=rule["rule_name"],
                                severity=SeverityLevel.ERROR,
                                line_number=line_number,
                                field="amount",
                                failure_description=f"Amount must be numeric, got: {record['amount']}",
                                expected_value="numeric value",
                                actual_value=record["amount"],
                                failure_id=str(uuid.uuid4()),
                            )
                        )

            elif rule_id == "DATE_001":
                # Date format validation
                if "date" in record:
                    try:
                        datetime.strptime(record["date"], rule.get("date_format", "%Y-%m-%d"))
                    except ValueError:
                        failures.append(
                            ValidationFailure(
                                rule_id=rule_id,
                                rule_name=rule["rule_name"],
                                severity=SeverityLevel(rule["severity"]),
                                line_number=line_number,
                                field="date",
                                failure_description=f"Invalid date format: {record['date']}",
                                expected_value=rule.get("date_format", "YYYY-MM-DD"),
                                actual_value=record["date"],
                                failure_id=str(uuid.uuid4()),
                            )
                        )

            elif rule_id == "ACC_001":
                # Account code format validation
                if "account" in record:
                    import re

                    pattern = rule.get("pattern", r"^\d{6}$")
                    if not re.match(pattern, str(record["account"])):
                        failures.append(
                            ValidationFailure(
                                rule_id=rule_id,
                                rule_name=rule["rule_name"],
                                severity=SeverityLevel(rule["severity"]),
                                line_number=line_number,
                                field="account",
                                failure_description=f"Account code format invalid: {record['account']}",
                                expected_value="6-digit numeric code",
                                actual_value=record["account"],
                                failure_id=str(uuid.uuid4()),
                            )
                        )

        except Exception as e:
            # Rule execution error
            failures.append(
                ValidationFailure(
                    rule_id=rule_id,
                    rule_name=rule["rule_name"],
                    severity=SeverityLevel.FATAL,
                    line_number=line_number,
                    failure_description=f"Rule execution error: {str(e)}",
                    failure_id=str(uuid.uuid4()),
                )
            )

        return failures

    async def explain(self, request: ExplanationRequest) -> ExplanationResponse:
        """Provide detailed explanation for a validation failure"""
        failure = request.failure

        # Find the rule for this failure
        rule = next((r for r in self.rules if r["rule_id"] == failure.rule_id), None)

        if not rule:
            return ExplanationResponse(
                failure_id=failure.failure_id or "unknown",
                explanation=f"Unknown rule: {failure.rule_id}",
                recommendation="Contact system administrator",
                confidence=0.1,
                source="static",
            )

        # Generate explanation based on rule type
        explanation = f"{rule['description']}. "
        recommendation = "Please correct the identified issue."
        suggested_actions = ["Review the data", "Apply correction"]

        if failure.rule_id == "REQ_001":
            explanation += f"The field '{failure.field}' is required for processing."
            recommendation = f"Provide a valid value for the '{failure.field}' field."
            suggested_actions = [f"Add value for {failure.field}", "Verify data completeness"]

        elif failure.rule_id == "AMT_001":
            explanation += "Large amounts may indicate data entry errors or unusual transactions."
            recommendation = "Verify the amount is correct and within expected business ranges."
            suggested_actions = [
                "Verify amount accuracy",
                "Check for data entry errors",
                "Review transaction source",
            ]

        elif failure.rule_id == "DATE_001":
            explanation += (
                "Consistent date formatting is required for proper processing and reporting."
            )
            recommendation = f"Format the date as {rule.get('date_format', 'YYYY-MM-DD')}."
            suggested_actions = [
                "Reformat date",
                "Verify date accuracy",
                "Check date parsing logic",
            ]

        elif failure.rule_id == "ACC_001":
            explanation += (
                "Account codes must follow the standard 6-digit format for system compatibility."
            )
            recommendation = "Use a valid 6-digit numeric account code."
            suggested_actions = [
                "Verify account code",
                "Check chart of accounts",
                "Confirm account exists",
            ]

        return ExplanationResponse(
            failure_id=failure.failure_id or "unknown",
            explanation=explanation,
            recommendation=recommendation,
            confidence=0.85,
            suggested_actions=suggested_actions,
            policy_references=[f"Rule {failure.rule_id}: {rule['description']}"],
            source="static",
        )

    async def get_info(self) -> RulePackInfo:
        """Get basic RulePack information"""
        return RulePackInfo(
            domain=self.domain,
            name=self.name,
            version=self.version,
            rule_count=len(self.rules),
            categories=list(set(rule.get("category", "general") for rule in self.rules)),
            supported_modes=[ValidationMode.STATIC, ValidationMode.HYBRID],
            capabilities=["validate", "explain"],
            metadata={
                "description": "Example RulePack for demonstration purposes",
                "author": "CORTX SDK",
                "supports_streaming": False,
            },
        )

    async def get_metadata(self) -> RulePackMetadata:
        """Get detailed RulePack metadata"""
        info = await self.get_info()

        rules = [
            RuleInfo(
                rule_id=rule["rule_id"],
                rule_name=rule["rule_name"],
                category=rule.get("category", "general"),
                severity=SeverityLevel(rule["severity"]),
                description=rule["description"],
                version=rule.get("version", "1.0"),
                tags=rule.get("tags", []),
            )
            for rule in self.rules
        ]

        return RulePackMetadata(
            info=info,
            rules=rules,
            created_at=datetime(2024, 1, 1),  # Example date
            updated_at=datetime.utcnow(),
            author="CORTX SDK Team",
            description="Comprehensive example RulePack demonstrating SDK usage patterns",
            compliance_frameworks=["Example-Framework-1.0"],
        )

    async def health_check(self) -> dict[str, Any]:
        """Perform health check"""
        return {
            "status": "healthy",
            "initialized": self.is_initialized,
            "rules_loaded": len(self.rules),
            "timestamp": datetime.utcnow().isoformat(),
            "version": self.version,
            "domain": self.domain,
        }
