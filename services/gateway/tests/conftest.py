"""
Pytest configuration and fixtures for Gateway service tests
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from jose import jwt

# JWT Configuration for testing
TEST_JWT_SECRET = "test-secret-key-for-testing-only"
TEST_ALGORITHM = "HS256"


@pytest.fixture
def mock_registry_client():
    """Mock RegistryClient for testing"""
    client = AsyncMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.discover = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_rulepack_client():
    """Mock RulePackClient for testing"""
    client = AsyncMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.validate = AsyncMock()
    client.explain = AsyncMock()
    client.get_info = AsyncMock()
    client.health_check = AsyncMock(return_value={"status": "healthy"})
    return client


@pytest.fixture
def mock_policy_router(mock_registry_client):
    """Mock PolicyRouter for testing"""
    from app.policy_router import PolicyRouter

    router = PolicyRouter(mock_registry_client)
    router.route_validation = AsyncMock()
    router.route_explanation = AsyncMock()
    router.health_check = AsyncMock(
        return_value={"policy_router": "healthy", "connected_rulepacks": 0, "rulepack_health": {}}
    )
    router.cleanup = AsyncMock()

    return router


@pytest.fixture
def test_app(mock_policy_router):
    """Create test FastAPI app with mocked dependencies"""
    from app.main import app
    from app.routers import analytics, orchestrator

    # Inject mock policy router
    orchestrator.policy_router = mock_policy_router
    analytics.policy_router = mock_policy_router

    return app


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)


@pytest.fixture
def async_client(test_app):
    """Create async test client"""
    from httpx import AsyncClient

    async def _client():
        async with AsyncClient(app=test_app, base_url="http://test") as ac:
            yield ac

    return _client


@pytest.fixture
def create_test_token():
    """Factory fixture to create JWT tokens for testing"""

    def _create_token(
        username: str = "test_user",
        tenant_id: str = "test_tenant",
        roles: list[str] = None,
        scopes: list[str] = None,
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
    """Generate admin auth headers for testing"""
    token = create_test_token(roles=["admin", "user"], scopes=["read", "write", "admin"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def propverify_auth_headers(create_test_token):
    """Generate PropVerify auth headers for testing"""
    token = create_test_token(
        roles=[
            "propverify:ingest",
            "propverify:validate",
            "propverify:workflow:execute",
            "propverify:workflow:approve",
            "propverify:ai:generate",
            "propverify:ai:sign",
            "propverify:ledger:anchor",
        ],
        scopes=["read", "write"],
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for proxy tests"""
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b'{"status": "ok"}'
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json = Mock(return_value={"status": "ok"})

    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    return mock_client


@pytest.fixture
def sample_validation_request():
    """Sample validation request data"""
    from cortx_rulepack_sdk.contracts import ValidationMode, ValidationOptions, ValidationRequest

    return ValidationRequest(
        domain="test.domain",
        input_type="records",
        input_data={"field1": "value1", "field2": 100},
        options=ValidationOptions(mode=ValidationMode.STATIC, tenant_id="test_tenant"),
        request_id="test-request-123",
        submitted_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_validation_response():
    """Sample validation response data"""
    from cortx_rulepack_sdk.contracts import (
        ValidationFailure,
        ValidationMode,
        ValidationResponse,
        ValidationStats,
    )

    stats = ValidationStats(
        total_records=1,
        records_processed=1,
        total_failures=1,
        fatal_count=0,
        error_count=1,
        warning_count=0,
        info_count=0,
        processing_time_ms=150,
        mode_used=ValidationMode.STATIC,
    )

    failures = [
        ValidationFailure(
            rule_id="TEST_001",
            severity="error",
            field="field1",
            message="Test validation failure",
            value="value1",
            policy_references=[],
            suggested_actions=[],
        )
    ]

    return ValidationResponse(
        request_id="test-request-123",
        domain="test.domain",
        success=True,
        summary=stats,
        failures=failures,
        mode_requested=ValidationMode.STATIC,
        mode_executed=ValidationMode.STATIC,
        completed_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_rulepack_registration():
    """Sample RulePack registration data"""
    from unittest.mock import Mock

    registration = Mock()
    registration.domain = "test.domain"
    registration.endpoint_url = "http://localhost:9000/rulepack"
    registration.status = Mock(value="active")
    registration.supported_modes = ["static", "hybrid", "agentic"]

    return registration


@pytest.fixture
def mock_identity_service(mock_httpx_client):
    """Mock identity service for auth tests"""

    def _configure_response(valid=True, username="test_user", tenant_id="test_tenant", roles=None):
        if roles is None:
            roles = ["user"]

        if valid:
            mock_httpx_client.request.return_value.status_code = 200
            mock_httpx_client.request.return_value.json = Mock(
                return_value={
                    "valid": True,
                    "username": username,
                    "tenant_id": tenant_id,
                    "roles": roles,
                    "scopes": ["read", "write"],
                }
            )
        else:
            mock_httpx_client.request.return_value.status_code = 401
            mock_httpx_client.request.return_value.json = Mock(return_value={"valid": False})

    return _configure_response


@pytest.fixture
def mock_platform_service(mock_httpx_client):
    """Mock platform service responses (RAG, OCR, Ledger)"""

    def _configure_response(status_code=200, response_data=None):
        if response_data is None:
            response_data = {"status": "ok"}

        import json

        mock_httpx_client.request.return_value.status_code = status_code
        mock_httpx_client.request.return_value.content = json.dumps(response_data).encode()
        mock_httpx_client.request.return_value.headers = {"content-type": "application/json"}
        mock_httpx_client.request.return_value.json = Mock(return_value=response_data)

    return _configure_response


@pytest.fixture(autouse=True)
def reset_policy_router():
    """Reset policy router state between tests"""
    yield
    # Cleanup happens here if needed


@pytest.fixture
def mock_audit_emit(monkeypatch):
    """Mock audit event emission"""
    mock_emit = AsyncMock()

    from cortx_core import auditing

    monkeypatch.setattr(auditing, "emit_audit", mock_emit)

    return mock_emit


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "auth: mark test as authentication/authorization test")
    config.addinivalue_line("markers", "proxy: mark test as proxy functionality test")
