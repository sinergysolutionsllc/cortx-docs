"""
Integration tests for Orchestrator API endpoints

Tests the main validation orchestration endpoints
"""

from unittest.mock import AsyncMock, Mock

import pytest
from cortx_rulepack_sdk.contracts import ValidationMode
from tests.__utils__.factories import create_validation_failure


@pytest.mark.integration
class TestValidationJobCreation:
    """Test POST /jobs/validate endpoint"""

    def test_create_validation_job_success(
        self, client, mock_policy_router, sample_validation_response
    ):
        """Test successful validation job creation"""
        mock_policy_router.route_validation = AsyncMock(return_value=sample_validation_response)

        response = client.post(
            "/jobs/validate",
            params={"domain": "test.domain", "mode": "static"},
            json={"field1": "value1", "field2": 100},
            headers={"x-tenant-id": "test_tenant", "x-request-id": "test-123"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["request_id"] == "test-123"
        assert data["domain"] == "test.domain"
        assert data["success"] is True
        assert "summary" in data
        assert "failures" in data

    def test_create_validation_job_with_input_ref(
        self, client, mock_policy_router, sample_validation_response
    ):
        """Test validation job with input reference"""
        mock_policy_router.route_validation = AsyncMock(return_value=sample_validation_response)

        response = client.post(
            "/jobs/validate",
            params={"domain": "test.domain", "mode": "static", "input_ref": "s3://bucket/file.csv"},
            headers={"x-tenant-id": "test_tenant"},
        )

        assert response.status_code == 200
        assert mock_policy_router.route_validation.called

    def test_create_validation_job_hybrid_mode(
        self, client, mock_policy_router, sample_validation_response
    ):
        """Test validation job in hybrid mode"""
        mock_policy_router.route_validation = AsyncMock(return_value=sample_validation_response)

        response = client.post(
            "/jobs/validate",
            params={"domain": "test.domain", "mode": "hybrid"},
            json={"test": "data"},
        )

        assert response.status_code == 200
        call_args = mock_policy_router.route_validation.call_args
        request = call_args[0][0]
        assert request.options.mode == ValidationMode.HYBRID

    def test_create_validation_job_with_options(
        self, client, mock_policy_router, sample_validation_response
    ):
        """Test validation job with custom options"""
        mock_policy_router.route_validation = AsyncMock(return_value=sample_validation_response)

        response = client.post(
            "/jobs/validate",
            params={
                "domain": "test.domain",
                "mode": "agentic",
                "options": {"confidence_threshold": 0.9, "include_warnings": True},
            },
            json={"test": "data"},
        )

        assert response.status_code == 200

    def test_create_validation_job_missing_input(self, client):
        """Test validation job fails without input"""
        response = client.post("/jobs/validate", params={"domain": "test.domain", "mode": "static"})

        assert response.status_code == 400
        assert "input_ref or input_data must be provided" in response.json()["detail"]

    def test_create_validation_job_policy_router_error(self, client, mock_policy_router):
        """Test validation job handles policy router errors"""
        mock_policy_router.route_validation = AsyncMock(
            side_effect=Exception("RulePack connection failed")
        )

        response = client.post(
            "/jobs/validate",
            params={"domain": "test.domain", "mode": "static"},
            json={"test": "data"},
        )

        assert response.status_code == 500
        assert "Validation failed" in response.json()["detail"]

    def test_create_validation_job_default_headers(
        self, client, mock_policy_router, sample_validation_response
    ):
        """Test validation job uses default tenant when not provided"""
        mock_policy_router.route_validation = AsyncMock(return_value=sample_validation_response)

        response = client.post(
            "/jobs/validate",
            params={"domain": "test.domain", "mode": "static"},
            json={"test": "data"},
        )

        assert response.status_code == 200
        # Verify default tenant_id was used
        call_args = mock_policy_router.route_validation.call_args
        request = call_args[0][0]
        assert request.options.tenant_id == "default"


@pytest.mark.integration
class TestJobStatusRetrieval:
    """Test GET /jobs/{job_id} endpoint"""

    def test_get_job_status(self, client):
        """Test getting job status"""
        response = client.get("/jobs/test-job-123", headers={"x-tenant-id": "test_tenant"})

        assert response.status_code == 200
        data = response.json()

        assert data["job_id"] == "test-job-123"
        assert data["status"] == "completed"
        assert data["tenant_id"] == "test_tenant"

    def test_get_job_status_default_tenant(self, client):
        """Test getting job status with default tenant"""
        response = client.get("/jobs/test-job-123")

        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "default"


@pytest.mark.integration
class TestExplanationGeneration:
    """Test POST /explain endpoint"""

    def test_explain_failure_success(self, client, mock_policy_router):
        """Test successful explanation generation"""
        explanation_response = Mock()
        explanation_response.explanation = "Test explanation"
        explanation_response.recommendation = "Test recommendation"
        explanation_response.confidence = 0.85
        explanation_response.policy_references = ["Policy 1"]
        explanation_response.suggested_actions = ["Action 1"]

        mock_policy_router.route_explanation = AsyncMock(return_value=explanation_response)

        failure_data = create_validation_failure()

        response = client.post(
            "/explain",
            params={"domain": "test.domain", "failure_id": "fail-123"},
            json=failure_data,
            headers={"x-tenant-id": "test_tenant", "x-request-id": "req-123"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["explanation"] == "Test explanation"
        assert data["recommendation"] == "Test recommendation"
        assert data["confidence"] == 0.85

    def test_explain_failure_with_options(self, client, mock_policy_router):
        """Test explanation with custom options"""
        explanation_response = Mock()
        explanation_response.explanation = "Test explanation"
        explanation_response.recommendation = "Test recommendation"
        explanation_response.confidence = 0.85
        explanation_response.policy_references = []
        explanation_response.suggested_actions = []

        mock_policy_router.route_explanation = AsyncMock(return_value=explanation_response)

        failure_data = create_validation_failure()

        response = client.post(
            "/explain",
            params={
                "domain": "test.domain",
                "failure_id": "fail-123",
                "include_policy_refs": False,
                "include_remediation": False,
            },
            json=failure_data,
        )

        assert response.status_code == 200

    def test_explain_failure_error(self, client, mock_policy_router):
        """Test explanation handles errors"""
        mock_policy_router.route_explanation = AsyncMock(
            side_effect=Exception("RAG service unavailable")
        )

        failure_data = create_validation_failure()

        response = client.post(
            "/explain",
            params={"domain": "test.domain", "failure_id": "fail-123"},
            json=failure_data,
        )

        assert response.status_code == 500
        assert "Explanation failed" in response.json()["detail"]


@pytest.mark.integration
class TestFailureDecisionUpdate:
    """Test PUT /failures/{failure_id}/decision endpoint"""

    def test_update_failure_decision_accept(self, client):
        """Test accepting a failure"""
        response = client.put(
            "/failures/fail-123/decision",
            params={
                "decision": "accept",
                "reason": "Approved by manager",
                "notes": "Exception granted",
            },
            headers={"x-tenant-id": "test_tenant", "x-request-id": "req-123"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["failure_id"] == "fail-123"
        assert data["decision"] == "accept"

    def test_update_failure_decision_defer(self, client):
        """Test deferring a failure"""
        response = client.put("/failures/fail-123/decision", params={"decision": "defer"})

        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "defer"

    def test_update_failure_decision_ignore(self, client):
        """Test ignoring a failure"""
        response = client.put(
            "/failures/fail-123/decision", params={"decision": "ignore", "reason": "Known issue"}
        )

        assert response.status_code == 200

    def test_update_failure_decision_override(self, client):
        """Test overriding a failure"""
        response = client.put(
            "/failures/fail-123/decision",
            params={"decision": "override", "reason": "Business requirement"},
        )

        assert response.status_code == 200

    def test_update_failure_decision_invalid(self, client):
        """Test invalid decision value"""
        response = client.put(
            "/failures/fail-123/decision", params={"decision": "invalid_decision"}
        )

        assert response.status_code == 400
        assert "Invalid decision" in response.json()["detail"]


@pytest.mark.integration
class TestRAGFeedbackSubmission:
    """Test POST /feedback/rag/{interaction_id} endpoint"""

    def test_submit_rag_feedback_helpful(self, client):
        """Test submitting helpful feedback"""
        response = client.post(
            "/feedback/rag/interaction-123",
            params={"feedback": "helpful", "details": "Clear and actionable"},
            headers={"x-tenant-id": "test_tenant", "x-request-id": "req-123"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["interaction_id"] == "interaction-123"
        assert data["feedback"] == "helpful"

    def test_submit_rag_feedback_not_helpful(self, client):
        """Test submitting not helpful feedback"""
        response = client.post(
            "/feedback/rag/interaction-123",
            params={"feedback": "not_helpful", "details": "Incorrect recommendation"},
        )

        assert response.status_code == 200

    def test_submit_rag_feedback_partially_helpful(self, client):
        """Test submitting partially helpful feedback"""
        response = client.post(
            "/feedback/rag/interaction-123", params={"feedback": "partially_helpful"}
        )

        assert response.status_code == 200

    def test_submit_rag_feedback_irrelevant(self, client):
        """Test submitting irrelevant feedback"""
        response = client.post("/feedback/rag/interaction-123", params={"feedback": "irrelevant"})

        assert response.status_code == 200

    def test_submit_rag_feedback_invalid(self, client):
        """Test invalid feedback value"""
        response = client.post(
            "/feedback/rag/interaction-123", params={"feedback": "invalid_feedback"}
        )

        assert response.status_code == 400
        assert "Invalid feedback" in response.json()["detail"]


@pytest.mark.integration
class TestOrchestratorHealthCheck:
    """Test GET /health endpoint"""

    def test_health_check_healthy(self, client, mock_policy_router):
        """Test health check when all services healthy"""
        mock_policy_router.health_check = AsyncMock(
            return_value={
                "policy_router": "healthy",
                "connected_rulepacks": 2,
                "rulepack_health": {
                    "domain1": {"status": "healthy"},
                    "domain2": {"status": "healthy"},
                },
            }
        )

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["orchestrator"] == "running"
        assert "policy_router" in data

    def test_health_check_unhealthy(self, client, mock_policy_router):
        """Test health check when service unhealthy"""
        mock_policy_router.health_check = AsyncMock(side_effect=Exception("Connection failed"))

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "unhealthy"
        assert "error" in data
