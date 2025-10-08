"""
RulePack Base Classes

Abstract base class that all RulePacks must implement.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from cortx_rulepack_sdk.contracts import (
    ExplanationRequest,
    ExplanationResponse,
    RulePackInfo,
    RulePackMetadata,
    ValidationFailure,
    ValidationRequest,
    ValidationResponse,
)


class RulePackBase(ABC):
    """
    Abstract base class for all RulePacks.

    Each domain-specific RulePack (FedReconcile, Grants, etc.) must inherit from this
    and implement the required methods.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize the RulePack with configuration.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize the RulePack. Called once during startup.
        Override to load rules, connect to databases, etc.
        """
        self._initialized = True

    async def shutdown(self) -> None:
        """
        Cleanup resources. Called during shutdown.
        Override to close connections, cleanup temp files, etc.
        """
        pass

    @property
    def is_initialized(self) -> bool:
        """Check if RulePack has been initialized"""
        return self._initialized

    # Core contract methods (required)

    @abstractmethod
    async def validate(self, request: ValidationRequest) -> ValidationResponse:
        """
        Validate input data according to domain rules.

        This is the core method that performs validation using static JSON rules
        and optionally AI validation based on the request mode.

        Args:
            request: Validation request with data and options

        Returns:
            ValidationResponse with results and any failures
        """
        pass

    @abstractmethod
    async def get_info(self) -> RulePackInfo:
        """
        Get basic information about this RulePack.

        Returns:
            RulePackInfo with domain, version, capabilities, etc.
        """
        pass

    @abstractmethod
    async def get_metadata(self) -> RulePackMetadata:
        """
        Get detailed metadata about this RulePack including all rules.

        Returns:
            RulePackMetadata with full rule catalog
        """
        pass

    # Optional methods (default implementations provided)

    async def explain(self, request: ExplanationRequest) -> ExplanationResponse:
        """
        Provide explanation for a validation failure.

        Default implementation returns basic explanation. Override to provide
        domain-specific explanations or integrate with RAG.

        Args:
            request: Explanation request with failure details

        Returns:
            ExplanationResponse with explanation and recommendations
        """
        failure = request.failure
        return ExplanationResponse(
            failure_id=failure.failure_id or "unknown",
            explanation=f"{failure.rule_name}: {failure.failure_description}",
            recommendation="Review the failure and apply appropriate correction",
            confidence=0.5,
            source="static",
        )

    async def health_check(self) -> dict[str, Any]:
        """
        Perform health check of the RulePack.

        Returns:
            Dict with health status and metrics
        """
        return {
            "status": "healthy" if self._initialized else "initializing",
            "initialized": self._initialized,
            "timestamp": "2024-01-01T00:00:00Z",  # Will be updated by implementation
        }

    async def validate_stream(self, request: ValidationRequest) -> AsyncIterator[ValidationFailure]:
        """
        Stream validation failures as they are discovered.

        Default implementation runs full validation and yields all failures.
        Override for true streaming validation.

        Args:
            request: Validation request

        Yields:
            ValidationFailure objects as they are discovered
        """
        response = await self.validate(request)
        for failure in response.failures:
            yield failure

    # Context manager support for resource management

    @asynccontextmanager
    async def lifespan(self):
        """
        Context manager for RulePack lifecycle.

        Usage:
            async with rulepack.lifespan():
                # RulePack is initialized and ready
                result = await rulepack.validate(request)
        """
        await self.initialize()
        try:
            yield self
        finally:
            await self.shutdown()

    # Utility methods for subclasses

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value with default"""
        return self.config.get(key, default)

    def require_config(self, key: str) -> Any:
        """Get required configuration value, raise if missing"""
        if key not in self.config:
            raise ValueError(f"Required configuration key '{key}' not found")
        return self.config[key]


class StreamingRulePackBase(RulePackBase):
    """
    Base class for RulePacks that support true streaming validation.

    Use this as base class if your RulePack can validate records incrementally
    and emit failures as they are discovered.
    """

    @abstractmethod
    async def validate_stream(self, request: ValidationRequest) -> AsyncIterator[ValidationFailure]:
        """
        Stream validation failures as they are discovered.

        This method must be implemented by streaming RulePacks.
        """
        pass

    async def validate(self, request: ValidationRequest) -> ValidationResponse:
        """
        Default implementation that collects streaming results.

        Override if you need different behavior.
        """
        failures = []

        async for failure in self.validate_stream(request):
            failures.append(failure)

            # Respect max_failures limit
            if request.options.max_failures and len(failures) >= request.options.max_failures:
                break

        # Calculate stats
        from cortx_rulepack_sdk.contracts import ValidationStats

        stats = ValidationStats(
            total_failures=len(failures),
            fatal_count=sum(1 for f in failures if f.severity == "fatal"),
            error_count=sum(1 for f in failures if f.severity == "error"),
            warning_count=sum(1 for f in failures if f.severity == "warning"),
            info_count=sum(1 for f in failures if f.severity == "info"),
            mode_used=request.options.mode,
        )

        return ValidationResponse(
            request_id=request.request_id,
            domain=(await self.get_info()).domain,
            success=True,  # Validation completed, even if there are failures
            summary=stats,
            failures=failures,
            mode_requested=request.options.mode,
            mode_executed=request.options.mode,
        )
