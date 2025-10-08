"""
Unit tests for PolicyRouter

Tests the core routing logic for validation requests across different modes:
- Conservative mode (JSON rules + RAG explanations)
- Hybrid mode (JSON + RAG comparison)
- Agentic mode (RAG primary with fallback)
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.policy_router import PolicyDecision, PolicyRouter
from cortx_rulepack_sdk.contracts import (
    ValidationFailure,
    ValidationMode,
    ValidationOptions,
    ValidationRequest,
    ValidationResponse,
    ValidationStats,
)


@pytest.mark.unit
class TestPolicyRouterInitialization:
    """Test PolicyRouter initialization"""

    def test_init_with_registry_client(self, mock_registry_client):
        """Test PolicyRouter initializes with registry client"""
        router = PolicyRouter(mock_registry_client)

        assert router.registry == mock_registry_client
        assert router._rulepack_clients == {}

    def test_init_creates_logger(self, mock_registry_client):
        """Test PolicyRouter creates logger instance"""
        router = PolicyRouter(mock_registry_client)

        assert router.logger is not None
        assert router.logger.name == "app.policy_router"


@pytest.mark.unit
class TestPolicyDetermination:
    """Test policy decision logic"""

    @pytest.mark.asyncio
    async def test_determine_policy_static_mode(self, mock_registry_client):
        """Test policy determination for static mode"""
        router = PolicyRouter(mock_registry_client)

        request = ValidationRequest(
            domain="test.domain",
            input_type="records",
            input_data={"test": "data"},
            options=ValidationOptions(mode=ValidationMode.STATIC),
            request_id="test-123",
            submitted_at=datetime.utcnow(),
        )

        policy = await router._determine_policy(request)

        assert policy == PolicyDecision.CONSERVATIVE

    @pytest.mark.asyncio
    async def test_determine_policy_hybrid_mode(self, mock_registry_client):
        """Test policy determination for hybrid mode"""
        router = PolicyRouter(mock_registry_client)

        request = ValidationRequest(
            domain="test.domain",
            input_type="records",
            input_data={"test": "data"},
            options=ValidationOptions(mode=ValidationMode.HYBRID),
            request_id="test-123",
            submitted_at=datetime.utcnow(),
        )

        policy = await router._determine_policy(request)

        assert policy == PolicyDecision.HYBRID

    @pytest.mark.asyncio
    async def test_determine_policy_agentic_mode_supported(
        self, mock_registry_client, mock_rulepack_client
    ):
        """Test policy determination for agentic mode when supported"""
        router = PolicyRouter(mock_registry_client)

        # Mock rulepack info with agentic support
        mock_info = Mock()
        mock_info.supported_modes = [
            ValidationMode.STATIC,
            ValidationMode.HYBRID,
            ValidationMode.AGENTIC,
        ]
        mock_rulepack_client.get_info = AsyncMock(return_value=mock_info)

        # Mock getting rulepack client
        router._get_rulepack_client = AsyncMock(return_value=mock_rulepack_client)
        router._get_rulepack_info = AsyncMock(return_value=mock_info)

        request = ValidationRequest(
            domain="test.domain",
            input_type="records",
            input_data={"test": "data"},
            options=ValidationOptions(mode=ValidationMode.AGENTIC),
            request_id="test-123",
            submitted_at=datetime.utcnow(),
        )

        policy = await router._determine_policy(request)

        assert policy == PolicyDecision.AGENTIC

    @pytest.mark.asyncio
    async def test_determine_policy_agentic_mode_not_supported_fallback(self, mock_registry_client):
        """Test policy determination falls back to hybrid when agentic not supported"""
        router = PolicyRouter(mock_registry_client)

        # Mock rulepack info without agentic support
        mock_info = Mock()
        mock_info.supported_modes = [ValidationMode.STATIC, ValidationMode.HYBRID]

        router._get_rulepack_info = AsyncMock(return_value=mock_info)

        request = ValidationRequest(
            domain="test.domain",
            input_type="records",
            input_data={"test": "data"},
            options=ValidationOptions(mode=ValidationMode.AGENTIC),
            request_id="test-123",
            submitted_at=datetime.utcnow(),
        )

        policy = await router._determine_policy(request)

        assert policy == PolicyDecision.HYBRID


@pytest.mark.unit
class TestConservativeMode:
    """Test conservative mode routing (JSON rules + RAG explanations)"""

    @pytest.mark.asyncio
    async def test_route_conservative_mode_success(
        self, mock_registry_client, mock_rulepack_client, sample_validation_response
    ):
        """Test successful conservative mode validation"""
        router = PolicyRouter(mock_registry_client)

        # Mock rulepack client validate response
        mock_rulepack_client.validate = AsyncMock(return_value=sample_validation_response)
        router._get_rulepack_client = AsyncMock(return_value=mock_rulepack_client)
        router._enhance_failures_with_rag_explanations = AsyncMock()

        request = ValidationRequest(
            domain="test.domain",
            input_type="records",
            input_data={"test": "data"},
            options=ValidationOptions(mode=ValidationMode.STATIC),
            request_id="test-123",
            submitted_at=datetime.utcnow(),
        )

        response = await router._route_conservative_mode(request)

        assert response.mode_executed == ValidationMode.STATIC
        assert mock_rulepack_client.validate.called
        assert router._enhance_failures_with_rag_explanations.called

    @pytest.mark.asyncio
    async def test_route_conservative_mode_no_failures_no_enhancement(
        self, mock_registry_client, mock_rulepack_client
    ):
        """Test conservative mode with no failures doesn't call enhancement"""
        router = PolicyRouter(mock_registry_client)

        # Create response with no failures
        response_no_failures = ValidationResponse(
            request_id="test-123",
            domain="test.domain",
            success=True,
            summary=ValidationStats(
                total_records=1,
                records_processed=1,
                total_failures=0,
                fatal_count=0,
                error_count=0,
                warning_count=0,
                info_count=0,
                processing_time_ms=100,
                mode_used=ValidationMode.STATIC,
            ),
            failures=[],
            mode_requested=ValidationMode.STATIC,
            mode_executed=ValidationMode.STATIC,
            completed_at=datetime.utcnow(),
        )

        mock_rulepack_client.validate = AsyncMock(return_value=response_no_failures)
        router._get_rulepack_client = AsyncMock(return_value=mock_rulepack_client)
        router._enhance_failures_with_rag_explanations = AsyncMock()

        request = ValidationRequest(
            domain="test.domain",
            input_type="records",
            input_data={"test": "data"},
            options=ValidationOptions(mode=ValidationMode.STATIC),
            request_id="test-123",
            submitted_at=datetime.utcnow(),
        )

        response = await router._route_conservative_mode(request)

        assert response.mode_executed == ValidationMode.STATIC
        assert len(response.failures) == 0
        # Enhancement should not be called for empty failures list
        assert not router._enhance_failures_with_rag_explanations.called

    @pytest.mark.asyncio
    async def test_route_conservative_mode_rulepack_not_found(self, mock_registry_client):
        """Test conservative mode fails when rulepack not found"""
        router = PolicyRouter(mock_registry_client)
        router._get_rulepack_client = AsyncMock(return_value=None)

        request = ValidationRequest(
            domain="nonexistent.domain",
            input_type="records",
            input_data={"test": "data"},
            options=ValidationOptions(mode=ValidationMode.STATIC),
            request_id="test-123",
            submitted_at=datetime.utcnow(),
        )

        with pytest.raises(ValueError, match="No RulePack found"):
            await router._route_conservative_mode(request)


@pytest.mark.unit
class TestHybridMode:
    """Test hybrid mode routing (JSON + RAG comparison)"""

    @pytest.mark.asyncio
    async def test_route_hybrid_mode_success(
        self, mock_registry_client, mock_rulepack_client, sample_validation_response
    ):
        """Test successful hybrid mode validation"""
        router = PolicyRouter(mock_registry_client)

        mock_rulepack_client.validate = AsyncMock(return_value=sample_validation_response)
        router._get_rulepack_client = AsyncMock(return_value=mock_rulepack_client)

        rag_data = {
            "failures": [
                {
                    "rule_id": "RAG_001",
                    "severity": "error",
                    "field": "field1",
                    "message": "RAG detected issue",
                    "value": "value1",
                    "ai_confidence": 0.9,
                }
            ],
            "processing_time_ms": 200,
        }
        router._run_rag_validation = AsyncMock(return_value=rag_data)
        router._merge_hybrid_results = Mock(return_value=sample_validation_response)

        request = ValidationRequest(
            domain="test.domain",
            input_type="records",
            input_data={"test": "data"},
            options=ValidationOptions(mode=ValidationMode.HYBRID),
            request_id="test-123",
            submitted_at=datetime.utcnow(),
        )

        response = await router._route_hybrid_mode(request)

        assert mock_rulepack_client.validate.called
        assert router._run_rag_validation.called
        assert router._merge_hybrid_results.called

    @pytest.mark.asyncio
    async def test_route_hybrid_mode_rag_failure_fallback(
        self, mock_registry_client, mock_rulepack_client, sample_validation_response
    ):
        """Test hybrid mode falls back when RAG fails"""
        router = PolicyRouter(mock_registry_client)

        mock_rulepack_client.validate = AsyncMock(return_value=sample_validation_response)
        router._get_rulepack_client = AsyncMock(return_value=mock_rulepack_client)
        router._run_rag_validation = AsyncMock(side_effect=Exception("RAG service error"))

        request = ValidationRequest(
            domain="test.domain",
            input_type="records",
            input_data={"test": "data"},
            options=ValidationOptions(mode=ValidationMode.HYBRID),
            request_id="test-123",
            submitted_at=datetime.utcnow(),
        )

        response = await router._route_hybrid_mode(request)

        # Should return static response with fallback reason
        assert response.fallback_reason is not None
        assert "RAG validation error" in response.fallback_reason


@pytest.mark.unit
class TestAgenticMode:
    """Test agentic mode routing (RAG primary with fallback)"""

    @pytest.mark.asyncio
    async def test_route_agentic_mode_high_confidence(
        self, mock_registry_client, mock_rulepack_client
    ):
        """Test agentic mode with high confidence RAG results"""
        router = PolicyRouter(mock_registry_client)

        router._get_rulepack_client = AsyncMock(return_value=mock_rulepack_client)

        rag_data = {
            "failures": [
                {
                    "rule_id": "RAG_001",
                    "severity": "error",
                    "field": "field1",
                    "message": "RAG detected issue",
                    "value": "value1",
                    "ai_confidence": 0.95,
                }
            ],
            "processing_time_ms": 200,
        }
        router._run_rag_validation = AsyncMock(return_value=rag_data)
        router._calculate_average_confidence = Mock(return_value=0.95)
        router._convert_rag_data_to_response = Mock(
            return_value=Mock(mode_executed=ValidationMode.AGENTIC, failures=rag_data["failures"])
        )

        request = ValidationRequest(
            domain="test.domain",
            input_type="records",
            input_data={"test": "data"},
            options=ValidationOptions(mode=ValidationMode.AGENTIC, confidence_threshold=0.8),
            request_id="test-123",
            submitted_at=datetime.utcnow(),
        )

        response = await router._route_agentic_mode(request)

        assert response.mode_executed == ValidationMode.AGENTIC
        assert router._run_rag_validation.called

    @pytest.mark.asyncio
    async def test_route_agentic_mode_low_confidence_fallback(
        self, mock_registry_client, mock_rulepack_client, sample_validation_response
    ):
        """Test agentic mode falls back to conservative on low confidence"""
        router = PolicyRouter(mock_registry_client)

        router._get_rulepack_client = AsyncMock(return_value=mock_rulepack_client)

        rag_data = {
            "failures": [
                {
                    "rule_id": "RAG_001",
                    "severity": "error",
                    "field": "field1",
                    "message": "RAG detected issue",
                    "value": "value1",
                    "ai_confidence": 0.5,
                }
            ],
            "processing_time_ms": 200,
        }
        router._run_rag_validation = AsyncMock(return_value=rag_data)
        router._calculate_average_confidence = Mock(return_value=0.5)
        router._route_conservative_mode = AsyncMock(return_value=sample_validation_response)

        request = ValidationRequest(
            domain="test.domain",
            input_type="records",
            input_data={"test": "data"},
            options=ValidationOptions(mode=ValidationMode.AGENTIC, confidence_threshold=0.8),
            request_id="test-123",
            submitted_at=datetime.utcnow(),
        )

        response = await router._route_agentic_mode(request)

        assert router._route_conservative_mode.called
        assert response.fallback_reason is not None
        assert "Low RAG confidence" in response.fallback_reason


@pytest.mark.unit
class TestMergeHybridResults:
    """Test merging JSON and RAG results in hybrid mode"""

    def test_merge_hybrid_results_agreement(self, mock_registry_client):
        """Test merging results when JSON and RAG agree"""
        router = PolicyRouter(mock_registry_client)

        static_response = ValidationResponse(
            request_id="test-123",
            domain="test.domain",
            success=True,
            summary=ValidationStats(
                total_records=1,
                records_processed=1,
                total_failures=2,
                fatal_count=0,
                error_count=2,
                warning_count=0,
                info_count=0,
                processing_time_ms=150,
                mode_used=ValidationMode.STATIC,
            ),
            failures=[
                ValidationFailure(
                    rule_id="COMMON_001",
                    severity="error",
                    field="field1",
                    message="Test failure",
                    value="value1",
                    policy_references=[],
                    suggested_actions=[],
                ),
                ValidationFailure(
                    rule_id="JSON_001",
                    severity="error",
                    field="field2",
                    message="JSON only failure",
                    value="value2",
                    policy_references=[],
                    suggested_actions=[],
                ),
            ],
            mode_requested=ValidationMode.STATIC,
            mode_executed=ValidationMode.STATIC,
            completed_at=datetime.utcnow(),
        )

        rag_data = {
            "failures": [
                {
                    "rule_id": "COMMON_001",
                    "severity": "error",
                    "field": "field1",
                    "message": "Test failure",
                    "value": "value1",
                    "ai_confidence": 0.9,
                    "ai_explanation": "RAG explanation",
                },
                {
                    "rule_id": "RAG_001",
                    "severity": "error",
                    "field": "field3",
                    "message": "RAG only failure",
                    "value": "value3",
                    "ai_confidence": 0.85,
                },
            ]
        }

        request = ValidationRequest(
            domain="test.domain",
            input_type="records",
            input_data={"test": "data"},
            options=ValidationOptions(mode=ValidationMode.HYBRID),
            request_id="test-123",
            submitted_at=datetime.utcnow(),
        )

        merged = router._merge_hybrid_results(static_response, rag_data, request)

        assert hasattr(merged, "comparison_delta")
        assert merged.comparison_delta["json_failure_count"] == 2
        assert merged.comparison_delta["rag_failure_count"] == 2
        assert "COMMON_001" in merged.comparison_delta["common_failures"]


@pytest.mark.unit
class TestRulePackClientManagement:
    """Test RulePack client retrieval and caching"""

    @pytest.mark.asyncio
    async def test_get_rulepack_client_creates_new(
        self, mock_registry_client, mock_rulepack_client
    ):
        """Test getting rulepack client creates new instance"""
        router = PolicyRouter(mock_registry_client)

        registration = Mock()
        registration.domain = "test.domain"
        registration.endpoint_url = "http://localhost:9000/rulepack"
        registration.status = Mock(value="active")

        mock_registry_client.discover = AsyncMock(return_value=[registration])

        with patch("app.policy_router.RulePackClient") as mock_client_class:
            mock_client_class.return_value = mock_rulepack_client

            client = await router._get_rulepack_client("test.domain")

            assert client == mock_rulepack_client
            assert router._rulepack_clients["test.domain"] == mock_rulepack_client
            assert mock_rulepack_client.connect.called

    @pytest.mark.asyncio
    async def test_get_rulepack_client_uses_cache(self, mock_registry_client, mock_rulepack_client):
        """Test getting rulepack client uses cached instance"""
        router = PolicyRouter(mock_registry_client)

        # Pre-populate cache
        router._rulepack_clients["test.domain"] = mock_rulepack_client

        client = await router._get_rulepack_client("test.domain")

        assert client == mock_rulepack_client
        # Should not call discover since it's cached
        assert not mock_registry_client.discover.called

    @pytest.mark.asyncio
    async def test_get_rulepack_client_not_found(self, mock_registry_client):
        """Test getting rulepack client returns None when not found"""
        router = PolicyRouter(mock_registry_client)

        mock_registry_client.discover = AsyncMock(return_value=[])

        client = await router._get_rulepack_client("nonexistent.domain")

        assert client is None


@pytest.mark.unit
class TestHealthCheck:
    """Test health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, mock_registry_client, mock_rulepack_client):
        """Test health check with all services healthy"""
        router = PolicyRouter(mock_registry_client)

        router._rulepack_clients = {
            "domain1": mock_rulepack_client,
            "domain2": mock_rulepack_client,
        }

        health = await router.health_check()

        assert health["policy_router"] == "healthy"
        assert health["connected_rulepacks"] == 2
        assert "domain1" in health["rulepack_health"]
        assert "domain2" in health["rulepack_health"]

    @pytest.mark.asyncio
    async def test_health_check_degraded(self, mock_registry_client):
        """Test health check with unhealthy rulepack"""
        router = PolicyRouter(mock_registry_client)

        healthy_client = AsyncMock()
        healthy_client.health_check = AsyncMock(return_value={"status": "healthy"})

        unhealthy_client = AsyncMock()
        unhealthy_client.health_check = AsyncMock(side_effect=Exception("Connection failed"))

        router._rulepack_clients = {"domain1": healthy_client, "domain2": unhealthy_client}

        health = await router.health_check()

        assert health["policy_router"] == "degraded"
        assert health["rulepack_health"]["domain2"]["status"] == "unhealthy"


@pytest.mark.unit
class TestCleanup:
    """Test cleanup functionality"""

    @pytest.mark.asyncio
    async def test_cleanup_disconnects_clients(self, mock_registry_client, mock_rulepack_client):
        """Test cleanup disconnects all rulepack clients"""
        router = PolicyRouter(mock_registry_client)

        router._rulepack_clients = {
            "domain1": mock_rulepack_client,
            "domain2": mock_rulepack_client,
        }

        await router.cleanup()

        assert mock_rulepack_client.disconnect.call_count == 2
        assert len(router._rulepack_clients) == 0
