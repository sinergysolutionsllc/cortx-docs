"""
Policy Router

Routes validation requests to appropriate RulePacks based on domain and mode settings.
Implements the three-mode validation strategy from CORTX architecture.
"""

import asyncio
import logging
from enum import Enum
from typing import Any

from cortx_rulepack_sdk.client import RulePackClient
from cortx_rulepack_sdk.contracts import (
    ExplanationRequest,
    ExplanationResponse,
    ValidationMode,
    ValidationRequest,
    ValidationResponse,
)
from cortx_rulepack_sdk.registry import RegistryClient


class PolicyDecision(str, Enum):
    """Policy routing decisions"""

    CONSERVATIVE = "conservative"  # JSON rules + RAG explanations (Mode 1)
    HYBRID = "hybrid"  # JSON + RAG validation comparison (Mode 2)
    AGENTIC = "agentic"  # RAG primary + JSON fallback (Mode 3)


class PolicyRouter:
    """
    Routes validation requests based on policy and configuration.

    Implements the core CORTX principle of progressive AI adoption:
    - Conservative mode: Static JSON rules only
    - Hybrid mode: Both static and AI, compare results
    - Agentic mode: AI primary with static fallback
    """

    def __init__(self, registry_client: RegistryClient):
        """
        Initialize policy router.

        Args:
            registry_client: Client for RulePack registry
        """
        self.registry = registry_client
        self._rulepack_clients: dict[str, RulePackClient] = {}
        self.logger = logging.getLogger(__name__)

    async def route_validation(self, request: ValidationRequest) -> ValidationResponse:
        """
        Route validation request to appropriate RulePack(s) based on policy.

        Args:
            request: Validation request

        Returns:
            Validation response (may be merged from multiple sources)
        """
        # Determine routing policy
        policy = await self._determine_policy(request)

        self.logger.info(
            f"Routing validation request for domain '{request.domain}' "
            f"with policy '{policy}' and mode '{request.options.mode}'"
        )

        # Route based on policy decision
        if policy == PolicyDecision.CONSERVATIVE:
            return await self._route_conservative_mode(request)

        elif policy == PolicyDecision.HYBRID:
            return await self._route_hybrid_mode(request)

        elif policy == PolicyDecision.AGENTIC:
            return await self._route_agentic_mode(request)

        else:
            # Fallback to conservative
            return await self._route_conservative_mode(request)

    async def route_explanation(
        self, request: ExplanationRequest, domain: str
    ) -> ExplanationResponse:
        """
        Route explanation request to appropriate RulePack.

        Args:
            request: Explanation request
            domain: Domain to route to

        Returns:
            Explanation response
        """
        client = await self._get_rulepack_client(domain)
        if not client:
            raise ValueError(f"No RulePack found for domain: {domain}")

        return await client.explain(request)

    async def _determine_policy(self, request: ValidationRequest) -> PolicyDecision:
        """
        Determine routing policy based on request and configuration.

        This is where business logic for AI adoption lives.
        Can be configured per domain, rule category, confidence levels, etc.
        """
        # For now, simple mapping based on requested mode
        # In production, this would consider:
        # - Domain-specific policies
        # - Historical accuracy metrics
        # - Confidence thresholds
        # - Regulatory requirements
        # - A/B testing configurations

        if request.options.mode == ValidationMode.STATIC:
            return PolicyDecision.CONSERVATIVE

        elif request.options.mode == ValidationMode.HYBRID:
            return PolicyDecision.HYBRID

        elif request.options.mode == ValidationMode.AGENTIC:
            # Check if domain supports agentic mode
            rulepack_info = await self._get_rulepack_info(request.domain)
            if rulepack_info and ValidationMode.AGENTIC in rulepack_info.supported_modes:
                return PolicyDecision.AGENTIC
            else:
                # Fallback to hybrid if agentic not supported
                return PolicyDecision.HYBRID

        return PolicyDecision.CONSERVATIVE

    async def _route_conservative_mode(self, request: ValidationRequest) -> ValidationResponse:
        """
        Mode 1: Conservative (JSON Rules + RAG Explanations)

        - JSON rules are authoritative for validation
        - RAG provides policy-based explanations for failures
        - Requires vector store for policy documents
        """
        client = await self._get_rulepack_client(request.domain)
        if not client:
            raise ValueError(f"No RulePack found for domain: {request.domain}")

        # Run JSON validation
        static_request = request.model_copy()
        static_request.options.mode = ValidationMode.STATIC

        response = await client.validate(static_request)

        # Enhance failures with RAG explanations
        if response.failures:
            await self._enhance_failures_with_rag_explanations(response.failures, request.domain)

        response.mode_executed = ValidationMode.STATIC

        self.logger.info(
            f"Conservative mode validation completed: {len(response.failures)} failures "
            f"with RAG explanations"
        )

        return response

    async def _route_hybrid_mode(self, request: ValidationRequest) -> ValidationResponse:
        """
        Mode 2: Hybrid (JSON + RAG Validation Comparison)

        - Both JSON and RAG perform validation independently
        - Compare outputs for confidence building and training
        - JSON rules remain authoritative for compliance
        - Generate comparative analysis for dashboard
        """
        client = await self._get_rulepack_client(request.domain)
        if not client:
            raise ValueError(f"No RulePack found for domain: {request.domain}")

        try:
            # Run both validations in parallel
            static_request = request.model_copy()
            static_request.options.mode = ValidationMode.STATIC

            # For hybrid mode, we need to also run AI validation
            # This requires the RulePack to support RAG validation
            static_response, rag_validation_data = await asyncio.gather(
                client.validate(static_request),
                self._run_rag_validation(request, client),
                return_exceptions=True,
            )

            # Handle RAG validation failure
            if isinstance(rag_validation_data, Exception):
                self.logger.warning(f"RAG validation failed in hybrid mode: {rag_validation_data}")
                static_response.mode_executed = ValidationMode.STATIC
                static_response.fallback_reason = (
                    f"RAG validation error: {str(rag_validation_data)}"
                )
                return static_response

            # Merge results with comparison analysis
            merged_response = self._merge_hybrid_results(
                static_response, rag_validation_data, request
            )

            merged_response.mode_executed = ValidationMode.HYBRID

            self.logger.info(
                f"Hybrid mode validation completed: JSON={len(static_response.failures)} failures, "
                f"RAG={len(rag_validation_data.get('failures', []))} failures"
            )

            return merged_response

        except Exception as e:
            self.logger.error(f"Hybrid validation failed: {e}")
            # Fallback to conservative mode
            return await self._route_conservative_mode(request)

    async def _route_agentic_mode(self, request: ValidationRequest) -> ValidationResponse:
        """
        Mode 3: Agentic (RAG Primary + JSON Fallback)

        - RAG performs primary validation
        - JSON rules as safety net on low confidence or errors
        - Can operate in human-in-the-loop or fully autonomous
        """
        client = await self._get_rulepack_client(request.domain)
        if not client:
            raise ValueError(f"No RulePack found for domain: {request.domain}")

        try:
            # Try RAG validation first
            rag_validation_data = await self._run_rag_validation(request, client)

            # Check average confidence of RAG results
            avg_confidence = self._calculate_average_confidence(
                rag_validation_data.get("failures", [])
            )

            if avg_confidence < request.options.confidence_threshold:
                self.logger.info(
                    f"RAG confidence {avg_confidence:.3f} below threshold "
                    f"{request.options.confidence_threshold:.3f}, falling back to JSON"
                )

                # Fallback to conservative mode (JSON + RAG explanations)
                fallback_response = await self._route_conservative_mode(request)
                fallback_response.fallback_reason = f"Low RAG confidence: {avg_confidence:.3f}"
                return fallback_response

            # Convert RAG validation data to response format
            response = self._convert_rag_data_to_response(rag_validation_data, request)
            response.mode_executed = ValidationMode.AGENTIC

            self.logger.info(
                f"Agentic mode validation completed: {len(response.failures)} failures "
                f"with avg confidence {avg_confidence:.3f}"
            )

            return response

        except Exception as e:
            self.logger.warning(f"Agentic validation failed, falling back to conservative: {e}")

            # Fallback to conservative mode
            fallback_response = await self._route_conservative_mode(request)
            fallback_response.fallback_reason = f"RAG validation error: {str(e)}"
            return fallback_response

    def _merge_hybrid_results(
        self,
        static_response: ValidationResponse,
        rag_data: dict[str, Any],
        original_request: ValidationRequest,
    ) -> ValidationResponse:
        """
        Merge results from JSON and RAG validation.

        Uses JSON results as authoritative but includes RAG insights.
        Tracks differences for accuracy measurement and training.
        """
        # Use static response as base
        merged = static_response.model_copy()

        rag_failures = rag_data.get("failures", [])

        # Calculate comparison delta for training dashboard
        static_failure_ids = {f.rule_id for f in static_response.failures}
        rag_failure_ids = {f.get("rule_id", "") for f in rag_failures}

        comparison_delta = {
            "json_only_failures": list(static_failure_ids - rag_failure_ids),
            "rag_only_failures": list(rag_failure_ids - static_failure_ids),
            "common_failures": list(static_failure_ids & rag_failure_ids),
            "agreement_rate": len(static_failure_ids & rag_failure_ids)
            / max(len(static_failure_ids | rag_failure_ids), 1),
            "json_failure_count": len(static_response.failures),
            "rag_failure_count": len(rag_failures),
            "avg_rag_confidence": self._calculate_average_confidence(rag_failures),
            "validation_mode": "hybrid_comparison",
            "analysis_timestamp": "2024-01-01T00:00:00Z",  # Would be actual timestamp
        }

        # Add RAG insights to JSON failures where available
        rag_failures_by_rule = {f.get("rule_id", ""): f for f in rag_failures}

        for failure in merged.failures:
            rag_failure = rag_failures_by_rule.get(failure.rule_id)
            if rag_failure:
                # Enhance JSON failure with RAG insights
                if not failure.ai_explanation:
                    failure.ai_explanation = rag_failure.get("ai_explanation", "")
                if not failure.ai_recommendation:
                    failure.ai_recommendation = rag_failure.get("ai_recommendation", "")
                if not failure.ai_confidence:
                    failure.ai_confidence = rag_failure.get("ai_confidence", 0.8)

                # Add policy references from RAG
                rag_refs = rag_failure.get("policy_references", [])
                if rag_refs:
                    failure.policy_references.extend(rag_refs)

                rag_actions = rag_failure.get("suggested_actions", [])
                if rag_actions:
                    failure.suggested_actions.extend(rag_actions)

        # Store comparison data for training dashboard
        merged.comparison_delta = comparison_delta

        return merged

    async def _enhance_failures_with_rag_explanations(self, failures: list, domain: str) -> None:
        """
        Enhance validation failures with RAG-powered explanations.
        Used in Conservative Mode to add policy context to JSON rule failures.
        """
        try:
            # This would typically call a RAG service or the RulePack's explain endpoint
            client = await self._get_rulepack_client(domain)
            if not client:
                return

            for failure in failures:
                if not hasattr(failure, "ai_explanation") or not failure.ai_explanation:
                    try:
                        from cortx_rulepack_sdk.contracts import ExplanationRequest

                        explain_request = ExplanationRequest(failure=failure)
                        explanation = await client.explain(explain_request)

                        # Add RAG enhancements to the failure
                        failure.ai_explanation = explanation.explanation
                        failure.ai_recommendation = explanation.recommendation
                        failure.ai_confidence = explanation.confidence
                        if explanation.policy_references:
                            failure.policy_references.extend(explanation.policy_references)
                        if explanation.suggested_actions:
                            failure.suggested_actions.extend(explanation.suggested_actions)

                    except Exception as e:
                        self.logger.warning(
                            f"Failed to get RAG explanation for failure {failure.rule_id}: {e}"
                        )

        except Exception as e:
            self.logger.error(f"Failed to enhance failures with RAG explanations: {e}")

    async def _run_rag_validation(
        self, request: ValidationRequest, client: RulePackClient
    ) -> dict[str, Any]:
        """
        Run RAG-based validation independently.
        Used in Hybrid and Agentic modes.
        """
        # This would call a special RAG validation endpoint on the RulePack
        # For now, we'll simulate this by calling a hypothetical endpoint
        try:
            # In a full implementation, this would be a separate endpoint like:
            # POST /validate-rag with the same input data

            # For now, we simulate RAG validation results
            rag_failures = []

            # This is a placeholder - in reality, the RulePack would have
            # a separate RAG validation method that uses AI to validate records
            self.logger.info(f"Running RAG validation for domain {request.domain}")

            return {
                "failures": rag_failures,
                "confidence_scores": [],
                "processing_time_ms": 250,
                "source": "rag_validation",
            }

        except Exception as e:
            self.logger.error(f"RAG validation failed: {e}")
            raise

    def _calculate_average_confidence(self, failures: list[dict[str, Any]]) -> float:
        """Calculate average confidence from a list of failures"""
        if not failures:
            return 1.0  # Perfect confidence if no issues found

        confidences = [f.get("ai_confidence", 0.8) for f in failures if f.get("ai_confidence")]
        if not confidences:
            return 0.8  # Default confidence

        return sum(confidences) / len(confidences)

    def _convert_rag_data_to_response(
        self, rag_data: dict[str, Any], request: ValidationRequest
    ) -> ValidationResponse:
        """Convert RAG validation data to ValidationResponse format"""
        from datetime import datetime

        from cortx_rulepack_sdk.contracts import (
            ValidationFailure,
            ValidationResponse,
            ValidationStats,
        )

        # Convert RAG failures to ValidationFailure objects
        failures = []
        for failure_data in rag_data.get("failures", []):
            failure = ValidationFailure.model_validate(failure_data)
            failures.append(failure)

        # Calculate stats
        stats = ValidationStats(
            total_records=1,  # This would be calculated properly
            records_processed=1,
            total_failures=len(failures),
            fatal_count=sum(1 for f in failures if f.severity == "fatal"),
            error_count=sum(1 for f in failures if f.severity == "error"),
            warning_count=sum(1 for f in failures if f.severity == "warning"),
            info_count=sum(1 for f in failures if f.severity == "info"),
            processing_time_ms=rag_data.get("processing_time_ms", 0),
            mode_used=ValidationMode.AGENTIC,
            avg_ai_confidence=self._calculate_average_confidence(rag_data.get("failures", [])),
        )

        return ValidationResponse(
            request_id=request.request_id,
            domain=request.domain,
            success=True,
            summary=stats,
            failures=failures,
            mode_requested=request.options.mode,
            mode_executed=ValidationMode.AGENTIC,
            completed_at=datetime.utcnow(),
        )

    async def _get_rulepack_client(self, domain: str) -> RulePackClient | None:
        """
        Get or create RulePack client for domain.

        Args:
            domain: Domain identifier

        Returns:
            RulePack client or None if not found
        """
        # Check cache
        if domain in self._rulepack_clients:
            return self._rulepack_clients[domain]

        # Look up in registry
        registrations = await self.registry.discover(domain=domain)
        if not registrations:
            self.logger.error(f"No RulePack registered for domain: {domain}")
            return None

        # Use first active registration
        registration = next(
            (r for r in registrations if r.status.value == "active"), registrations[0]
        )

        # Create client
        client = RulePackClient(registration.endpoint_url)
        await client.connect()

        self._rulepack_clients[domain] = client

        self.logger.info(
            f"Connected to RulePack for domain '{domain}' " f"at {registration.endpoint_url}"
        )

        return client

    async def _get_rulepack_info(self, domain: str):
        """Get RulePack info for domain"""
        client = await self._get_rulepack_client(domain)
        if client:
            return await client.get_info()
        return None

    async def health_check(self) -> dict[str, Any]:
        """Check health of all connected RulePacks"""
        health_status = {
            "policy_router": "healthy",
            "connected_rulepacks": len(self._rulepack_clients),
            "rulepack_health": {},
        }

        # Check each connected RulePack
        for domain, client in self._rulepack_clients.items():
            try:
                rulepack_health = await client.health_check()
                health_status["rulepack_health"][domain] = rulepack_health
            except Exception as e:
                health_status["rulepack_health"][domain] = {"status": "unhealthy", "error": str(e)}
                health_status["policy_router"] = "degraded"

        return health_status

    async def cleanup(self) -> None:
        """Cleanup resources"""
        for client in self._rulepack_clients.values():
            await client.disconnect()

        self._rulepack_clients.clear()
        self.logger.info("PolicyRouter cleanup completed")
