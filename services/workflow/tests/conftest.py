"""Pytest configuration and fixtures for Workflow Service tests."""

import os

# Set environment variables BEFORE any imports
os.environ["REQUIRE_AUTH"] = "false"
os.environ["CORTX_GATEWAY_URL"] = "http://test-gateway:8080"
os.environ["CORTX_IDENTITY_URL"] = "http://test-identity:8081"
os.environ["CORTX_COMPLIANCE_URL"] = "http://test-compliance:8082"
os.environ["JWT_AUDIENCE"] = "workflow"
os.environ["JWT_ISSUER"] = "http://test-identity:8081"

import uuid
from typing import Any, Dict, Generator
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """Ensure environment variables are set for testing."""
    # These are already set above, but this fixture ensures they persist
    pass


@pytest.fixture
def mock_cortx_client() -> Generator[Mock, None, None]:
    """Mock CORTXClient for testing."""
    mock_client = Mock()
    mock_client.get_json = Mock(return_value={"status": "ok"})
    mock_client.post_json = Mock(return_value={"status": "ok", "id": str(uuid.uuid4())})
    mock_client._client = Mock()
    mock_client._client.close = Mock()
    yield mock_client


@pytest.fixture
def mock_cortex_client() -> Generator[Mock, None, None]:
    """Mock CortexClient for compliance logging."""
    mock_client = Mock()
    mock_client.log_compliance_event = Mock(return_value=None)
    yield mock_client


@pytest.fixture
def client(mock_cortx_client, mock_cortex_client) -> Generator[TestClient, None, None]:
    """Create test client with mocked dependencies."""
    with patch("app.main.client", mock_cortx_client):
        with patch("app.main.cortex_client", mock_cortex_client):
            with patch("app.main.approval_tasks", {}):
                from app.main import app

                with TestClient(app) as test_client:
                    yield test_client


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """Generate auth headers for testing."""
    # For testing, we use REQUIRE_AUTH=false, so headers are optional
    return {"Authorization": "Bearer test_token", "X-Correlation-ID": str(uuid.uuid4())}


@pytest.fixture
def workflow_pack_id() -> str:
    """Sample workflow pack ID."""
    return "test.workflow.pack"


@pytest.fixture
def workflow_execution_request() -> Dict[str, Any]:
    """Sample workflow execution request payload."""
    return {
        "workflow_pack_id": "test.workflow.pack",
        "workflow_type": "operational",
        "payload": {
            "action": "process_document",
            "document_id": "doc_123",
            "parameters": {"priority": "high"},
        },
        "metadata": {"source": "api", "version": "1.0.0"},
    }


@pytest.fixture
def legal_workflow_request() -> Dict[str, Any]:
    """Sample legal workflow request that requires HIL approval."""
    return {
        "workflow_pack_id": "legal.title.check",
        "workflow_type": "legal",
        "payload": {
            "property_id": "prop_456",
            "title_commitment": "TC-2024-001",
            "legal_description": "Lot 1, Block 2, Example Subdivision",
        },
        "metadata": {"source": "title_company"},
    }


@pytest.fixture
def financial_workflow_request() -> Dict[str, Any]:
    """Sample financial workflow request with high amount."""
    return {
        "workflow_pack_id": "financial.payment",
        "workflow_type": "financial",
        "payload": {"amount": 50000, "currency": "USD", "recipient": "vendor_789"},
        "metadata": {"source": "payment_system"},
    }


@pytest.fixture
def designer_compile_request() -> Dict[str, Any]:
    """Sample designer compile request."""
    return {
        "designer_output": {
            "type": "workflow",
            "id": "test_workflow",
            "version": "1.0.0",
            "steps": [
                {"id": "step1", "type": "validation", "config": {"rule_pack": "test.rules"}},
                {"id": "step2", "type": "action", "config": {"action": "notify"}},
            ],
        },
        "output_format": "json",
        "validate_schema": True,
        "metadata": {"designer_version": "2.0.0"},
    }


@pytest.fixture
def mock_approval_task() -> Dict[str, Any]:
    """Sample approval task data."""
    workflow_id = str(uuid.uuid4())
    return {
        "workflow_id": workflow_id,
        "workflow_request": {
            "workflow_pack_id": "legal.workflow",
            "workflow_type": "legal",
            "payload": {"legal_description": "Test property"},
            "metadata": {},
        },
        "status": "pending_approval",
        "created_at": 1234567890.0,
        "correlation_id": str(uuid.uuid4()),
    }


@pytest.fixture
def mock_workflow_response() -> Dict[str, Any]:
    """Sample workflow response from CORTX service."""
    return {
        "workflow_id": str(uuid.uuid4()),
        "status": "executed",
        "steps_completed": 2,
        "steps_total": 2,
        "result": {"success": True, "output": "Workflow completed successfully"},
    }


@pytest.fixture
def clear_approval_tasks():
    """Clear approval tasks between tests."""
    from app.main import approval_tasks

    approval_tasks.clear()
    yield
    approval_tasks.clear()
