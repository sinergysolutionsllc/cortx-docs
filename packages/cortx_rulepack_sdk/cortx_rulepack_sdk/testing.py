"""
Test Utilities for RulePack Development

Utilities to help RulePack developers test their implementations.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from cortx_rulepack_sdk.base import RulePackBase
from cortx_rulepack_sdk.contracts import (
    ExplanationRequest,
    RulePackInfo,
    RulePackMetadata,
    SeverityLevel,
    ValidationFailure,
    ValidationMode,
    ValidationOptions,
    ValidationRequest,
    ValidationResponse,
)


class MockValidationFailure:
    """Builder for creating test validation failures"""

    @staticmethod
    def create(
        rule_id: str = "TEST_001",
        rule_name: str = "Test Rule",
        severity: SeverityLevel = SeverityLevel.ERROR,
        line_number: int | None = None,
        field: str | None = None,
        failure_description: str = "Test validation failure",
        **kwargs,
    ) -> ValidationFailure:
        """Create a mock validation failure for testing"""
        return ValidationFailure(
            rule_id=rule_id,
            rule_name=rule_name,
            severity=severity,
            line_number=line_number,
            field=field,
            failure_description=failure_description,
            failure_id=str(uuid.uuid4()),
            **kwargs,
        )


class MockRulePackData:
    """Mock data generators for testing RulePacks"""

    @staticmethod
    def validation_request(
        domain: str = "test",
        input_data: Any | None = None,
        mode: ValidationMode = ValidationMode.STATIC,
        **kwargs,
    ) -> ValidationRequest:
        """Create a mock validation request"""
        if input_data is None:
            input_data = {"test_field": "test_value"}

        options = ValidationOptions(mode=mode, **kwargs.get("options", {}))

        return ValidationRequest(
            domain=domain,
            input_data=input_data,
            request_id=str(uuid.uuid4()),
            options=options,
            **{k: v for k, v in kwargs.items() if k != "options"},
        )

    @staticmethod
    def explanation_request(
        failure: ValidationFailure | None = None, **kwargs
    ) -> ExplanationRequest:
        """Create a mock explanation request"""
        if failure is None:
            failure = MockValidationFailure.create()

        return ExplanationRequest(failure=failure, **kwargs)


class RulePackTestSuite:
    """
    Test suite for validating RulePack implementations.

    Use this to ensure your RulePack correctly implements the contract.
    """

    def __init__(self, rulepack_class: type[RulePackBase], config: dict[str, Any] | None = None):
        """
        Initialize test suite.

        Args:
            rulepack_class: The RulePack class to test
            config: Configuration for the RulePack instance
        """
        self.rulepack_class = rulepack_class
        self.config = config or {}
        self.test_results: list[dict[str, Any]] = []

    async def run_all_tests(self) -> dict[str, Any]:
        """
        Run all contract tests.

        Returns:
            Test results summary
        """
        self.test_results = []

        tests = [
            ("test_initialization", self._test_initialization),
            ("test_get_info", self._test_get_info),
            ("test_get_metadata", self._test_get_metadata),
            ("test_validate", self._test_validate),
            ("test_explain", self._test_explain),
            ("test_health_check", self._test_health_check),
            ("test_lifecycle", self._test_lifecycle),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                await test_func()
                self.test_results.append(
                    {
                        "test": test_name,
                        "status": "PASSED",
                        "message": "Test completed successfully",
                    }
                )
                passed += 1
            except Exception as e:
                self.test_results.append(
                    {
                        "test": test_name,
                        "status": "FAILED",
                        "message": str(e),
                        "error_type": type(e).__name__,
                    }
                )
                failed += 1

        return {
            "summary": {
                "total": len(tests),
                "passed": passed,
                "failed": failed,
                "success_rate": passed / len(tests) if tests else 0,
            },
            "results": self.test_results,
        }

    async def _test_initialization(self) -> None:
        """Test RulePack initialization"""
        rulepack = self.rulepack_class(self.config)

        assert (
            not rulepack.is_initialized
        ), "RulePack should not be initialized before calling initialize()"

        await rulepack.initialize()

        assert rulepack.is_initialized, "RulePack should be initialized after calling initialize()"

        await rulepack.shutdown()

    async def _test_get_info(self) -> None:
        """Test get_info method"""
        async with self._create_rulepack() as rulepack:
            info = await rulepack.get_info()

            assert isinstance(info, RulePackInfo), "get_info() must return RulePackInfo instance"
            assert info.domain, "RulePackInfo.domain must not be empty"
            assert info.name, "RulePackInfo.name must not be empty"
            assert info.version, "RulePackInfo.version must not be empty"
            assert info.rule_count >= 0, "RulePackInfo.rule_count must be non-negative"
            assert isinstance(info.categories, list), "RulePackInfo.categories must be a list"
            assert isinstance(
                info.supported_modes, list
            ), "RulePackInfo.supported_modes must be a list"

    async def _test_get_metadata(self) -> None:
        """Test get_metadata method"""
        async with self._create_rulepack() as rulepack:
            metadata = await rulepack.get_metadata()

            assert isinstance(
                metadata, RulePackMetadata
            ), "get_metadata() must return RulePackMetadata instance"
            assert isinstance(
                metadata.info, RulePackInfo
            ), "RulePackMetadata.info must be RulePackInfo"
            assert isinstance(metadata.rules, list), "RulePackMetadata.rules must be a list"
            assert isinstance(
                metadata.created_at, datetime
            ), "RulePackMetadata.created_at must be datetime"
            assert isinstance(
                metadata.updated_at, datetime
            ), "RulePackMetadata.updated_at must be datetime"

    async def _test_validate(self) -> None:
        """Test validate method"""
        async with self._create_rulepack() as rulepack:
            request = MockRulePackData.validation_request()

            response = await rulepack.validate(request)

            assert isinstance(
                response, ValidationResponse
            ), "validate() must return ValidationResponse instance"
            assert (
                response.request_id == request.request_id
            ), "Response must have matching request_id"
            assert response.domain, "Response.domain must not be empty"
            assert isinstance(response.success, bool), "Response.success must be boolean"
            assert hasattr(response, "summary"), "Response must have summary"
            assert isinstance(response.failures, list), "Response.failures must be a list"
            assert (
                response.mode_requested == request.options.mode
            ), "Response must track requested mode"
            assert hasattr(response.mode_executed, "value") or isinstance(
                response.mode_executed, str
            ), "Response must have mode_executed"

    async def _test_explain(self) -> None:
        """Test explain method"""
        async with self._create_rulepack() as rulepack:
            failure = MockValidationFailure.create()
            request = MockRulePackData.explanation_request(failure=failure)

            response = await rulepack.explain(request)

            assert hasattr(response, "explanation"), "ExplanationResponse must have explanation"
            assert hasattr(
                response, "recommendation"
            ), "ExplanationResponse must have recommendation"
            assert hasattr(response, "confidence"), "ExplanationResponse must have confidence"
            assert 0 <= response.confidence <= 1, "Confidence must be between 0 and 1"

    async def _test_health_check(self) -> None:
        """Test health_check method"""
        async with self._create_rulepack() as rulepack:
            health = await rulepack.health_check()

            assert isinstance(health, dict), "health_check() must return dict"
            assert "status" in health, "Health check must include status"

    async def _test_lifecycle(self) -> None:
        """Test RulePack lifecycle management"""
        rulepack = self.rulepack_class(self.config)

        # Test context manager
        async with rulepack.lifespan():
            assert rulepack.is_initialized, "RulePack should be initialized in lifespan context"

            # Should be able to perform operations
            info = await rulepack.get_info()
            assert info is not None

    async def _create_rulepack(self):
        """Create and initialize a RulePack instance for testing"""
        rulepack = self.rulepack_class(self.config)
        await rulepack.initialize()

        class RulePackContextManager:
            def __init__(self, rp):
                self.rulepack = rp

            async def __aenter__(self):
                return self.rulepack

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                await self.rulepack.shutdown()

        return RulePackContextManager(rulepack)


class RulePackBenchmark:
    """
    Performance benchmarking for RulePacks.
    """

    def __init__(self, rulepack: RulePackBase):
        """Initialize benchmark with RulePack instance"""
        self.rulepack = rulepack

    async def benchmark_validation(
        self, test_data: list[dict[str, Any]], iterations: int = 100
    ) -> dict[str, Any]:
        """
        Benchmark validation performance.

        Args:
            test_data: List of test data records
            iterations: Number of iterations to run

        Returns:
            Benchmark results
        """
        import time

        results = []

        for i in range(iterations):
            start_time = time.perf_counter()

            request = MockRulePackData.validation_request(input_data=test_data[i % len(test_data)])

            response = await self.rulepack.validate(request)

            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            results.append(
                {
                    "iteration": i + 1,
                    "duration_ms": duration_ms,
                    "failures_count": len(response.failures),
                    "success": response.success,
                }
            )

        durations = [r["duration_ms"] for r in results]

        return {
            "iterations": iterations,
            "total_duration_ms": sum(durations),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "throughput_per_second": 1000 / (sum(durations) / len(durations)),
            "results": results,
        }


def create_test_data_file(
    file_path: str | Path, data: list[dict[str, Any]], format: str = "json"
) -> None:
    """
    Create test data file for RulePack testing.

    Args:
        file_path: Path to create the test file
        data: Test data to write
        format: File format ("json" or "csv")
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if format.lower() == "json":
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    elif format.lower() == "csv":
        import csv

        if not data:
            return

        with open(file_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    else:
        raise ValueError(f"Unsupported format: {format}")


async def run_rulepack_tests(
    rulepack_class: type[RulePackBase], config: dict[str, Any] | None = None, verbose: bool = True
) -> dict[str, Any]:
    """
    Convenience function to run all tests for a RulePack.

    Args:
        rulepack_class: RulePack class to test
        config: Configuration for the RulePack
        verbose: Whether to print test progress

    Returns:
        Test results
    """
    if verbose:
        print(f"Running tests for {rulepack_class.__name__}...")

    test_suite = RulePackTestSuite(rulepack_class, config)
    results = await test_suite.run_all_tests()

    if verbose:
        summary = results["summary"]
        print(f"Tests completed: {summary['passed']}/{summary['total']} passed")

        for result in results["results"]:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            print(f"  {status_icon} {result['test']}: {result['message']}")

    return results
