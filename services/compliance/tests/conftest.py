"""
Pytest configuration and fixtures for Compliance service tests
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from jose import jwt

# JWT Configuration for testing
TEST_JWT_SECRET = "test-secret-key-for-testing-only"
TEST_ALGORITHM = "HS256"


@pytest.fixture
def test_app():
    """Create test FastAPI app"""
    from app.main import app

    return app


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)


@pytest.fixture
def create_test_token():
    """Factory fixture to create JWT tokens for testing"""

    def _create_token(
        username: str = "test_user",
        tenant_id: str = "test_tenant",
        roles: List[str] = None,
        scopes: List[str] = None,
        expires_delta: timedelta = None,
    ) -> str:
        """Create a test JWT token"""
        if roles is None:
            roles = ["user"]
        if scopes is None:
            scopes = ["read", "write"]

        if expires_delta is None:
            expires_delta = timedelta(hours=1)

        expire = datetime.utcnow() + expires_delta

        payload = {
            "sub": username,
            "tenant_id": tenant_id,
            "roles": roles,
            "scopes": scopes,
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        return jwt.encode(payload, TEST_JWT_SECRET, algorithm=TEST_ALGORITHM)

    return _create_token


@pytest.fixture
def auth_headers(create_test_token):
    """Generate auth headers for testing"""
    token = create_test_token()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(create_test_token):
    """Generate admin auth headers with propverify:admin role"""
    token = create_test_token(roles=["propverify:admin", "user"], scopes=["read", "write", "admin"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def write_auth_headers(create_test_token):
    """Generate write auth headers with propverify:write role"""
    token = create_test_token(roles=["propverify:write", "user"], scopes=["read", "write"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_compliance_event() -> Dict[str, Any]:
    """Sample compliance event data"""
    return {
        "event_type": "audit",
        "description": "User login attempt",
        "data": {"ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0", "success": True},
        "user_id": "user_123",
        "severity": "info",
    }


@pytest.fixture
def sample_compliance_event_critical() -> Dict[str, Any]:
    """Sample critical compliance event data"""
    return {
        "event_type": "violation",
        "description": "Unauthorized access attempt to sensitive data",
        "data": {
            "resource": "/api/v1/sensitive/data",
            "attempted_action": "DELETE",
            "blocked": True,
        },
        "user_id": "user_456",
        "severity": "critical",
    }


@pytest.fixture
def sample_regulatory_event() -> Dict[str, Any]:
    """Sample regulatory compliance event"""
    return {
        "event_type": "regulatory",
        "description": "HIPAA data access logged",
        "data": {
            "patient_id": "PHI_789",
            "accessed_fields": ["name", "ssn", "diagnosis"],
            "purpose": "treatment",
        },
        "user_id": "doctor_001",
        "severity": "high",
    }


@pytest.fixture
def sample_workflow_event() -> Dict[str, Any]:
    """Sample workflow compliance event"""
    return {
        "event_type": "workflow",
        "description": "Workflow execution started",
        "data": {"workflow_id": "wf_123", "pack_id": "test.pack", "version": "1.0.0"},
        "user_id": "user_123",
        "severity": "info",
    }


@pytest.fixture
def multiple_compliance_events() -> List[Dict[str, Any]]:
    """Multiple compliance events for testing aggregation"""
    current_time = int(time.time())
    return [
        {
            "event_id": "evt_001",
            "event_type": "audit",
            "description": "User login",
            "data": {"success": True},
            "user_id": "user_001",
            "severity": "info",
            "correlation_id": "corr_001",
            "timestamp": current_time - 3600,
            "data_hash": "hash_001",
        },
        {
            "event_id": "evt_002",
            "event_type": "violation",
            "description": "Access denied",
            "data": {"resource": "/api/admin"},
            "user_id": "user_002",
            "severity": "high",
            "correlation_id": "corr_002",
            "timestamp": current_time - 1800,
            "data_hash": "hash_002",
        },
        {
            "event_id": "evt_003",
            "event_type": "regulatory",
            "description": "HIPAA data access",
            "data": {"patient_id": "PHI_123"},
            "user_id": "user_003",
            "severity": "medium",
            "correlation_id": "corr_003",
            "timestamp": current_time - 900,
            "data_hash": "hash_003",
        },
        {
            "event_id": "evt_004",
            "event_type": "audit",
            "description": "User logout",
            "data": {"success": True},
            "user_id": "user_001",
            "severity": "info",
            "correlation_id": "corr_004",
            "timestamp": current_time - 600,
            "data_hash": "hash_004",
        },
        {
            "event_id": "evt_005",
            "event_type": "violation",
            "description": "Rate limit exceeded",
            "data": {"endpoint": "/api/data"},
            "user_id": "user_004",
            "severity": "critical",
            "correlation_id": "corr_005",
            "timestamp": current_time - 300,
            "data_hash": "hash_005",
        },
    ]


@pytest.fixture
def mock_cortex_client():
    """Mock CortexClient for testing"""
    client = Mock()
    client.log_compliance_event = Mock()
    return client


@pytest.fixture
def mock_correlation_id():
    """Mock correlation ID for testing"""
    return "test-correlation-id-12345"


@pytest.fixture(autouse=True)
def reset_compliance_events():
    """Reset compliance events storage between tests"""
    from app.main import compliance_events

    compliance_events.clear()
    yield
    compliance_events.clear()


@pytest.fixture
def populated_compliance_events(multiple_compliance_events):
    """Populate compliance events storage with test data"""
    from app.main import compliance_events

    compliance_events.extend(multiple_compliance_events)
    return compliance_events


@pytest.fixture
def mock_request():
    """Mock FastAPI Request object"""
    mock = Mock()
    mock.state.correlation_id = "test-correlation-id"
    mock.headers.get = Mock(return_value="00-trace-id-00-01")
    return mock


@pytest.fixture
def time_range():
    """Time range for report testing"""
    current_time = int(time.time())
    return {
        "start_time": current_time - 86400,  # 24 hours ago
        "end_time": current_time,
        "current_time": current_time,
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "auth: mark test as authentication/authorization test")
    config.addinivalue_line("markers", "compliance: mark test as compliance-specific test")
