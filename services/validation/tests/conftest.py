"""Pytest configuration and fixtures for Validation Service tests."""

import os
import sys
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

# Mock cortx_backend module before importing app.main
sys.modules["cortx_backend"] = MagicMock()
sys.modules["cortx_backend.common"] = MagicMock()
sys.modules["cortx_backend.common.cortex_client"] = MagicMock()
sys.modules["cortx_backend.common.models"] = MagicMock()
sys.modules["cortx_backend.common.audit"] = MagicMock()
sys.modules["cortx_backend.common.config"] = MagicMock()
sys.modules["cortx_backend.common.http_client"] = MagicMock()
sys.modules["cortx_backend.common.logging"] = MagicMock()
sys.modules["cortx_backend.common.metrics"] = MagicMock()
sys.modules["cortx_backend.common.middleware"] = MagicMock()
sys.modules["cortx_backend.common.tokens"] = MagicMock()
sys.modules["cortx_backend.common.tracing"] = MagicMock()
sys.modules["cortx_backend.common.auth"] = MagicMock()
sys.modules["cortx_backend.common.redaction"] = MagicMock()

# Mock the functions and classes used by app.main
from unittest.mock import MagicMock

sys.modules["cortx_backend.common.logging"].setup_logging = MagicMock(return_value=MagicMock())
sys.modules["cortx_backend.common.audit"].sha256_hex = MagicMock(return_value="mocked_hash")
sys.modules["cortx_backend.common.redaction"].redact_text = MagicMock(
    side_effect=lambda x, **kwargs: x
)
sys.modules["cortx_backend.common.auth"].get_user_id_from_request = MagicMock(
    return_value="test-user"
)
sys.modules["cortx_backend.common.auth"].require_auth = MagicMock(return_value=lambda r: {})
sys.modules["cortx_backend.common.auth"].decode_token_optional = MagicMock(return_value={})
sys.modules["cortx_backend.common.auth"].require_roles = MagicMock(return_value=lambda r: {})


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["REQUIRE_AUTH"] = "false"
    os.environ["CORTX_GATEWAY_URL"] = "http://localhost:8000"
    os.environ["CORTX_COMPLIANCE_URL"] = "http://localhost:8003"
    os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture
def mock_cortx_client() -> Generator[MagicMock, None, None]:
    """Mock CORTXClient for testing."""
    with patch("app.main.client") as mock_client:
        mock_client.get_json = Mock(return_value={})
        mock_client.post_json = Mock(return_value={})
        yield mock_client


@pytest.fixture
def mock_cortex_client() -> Generator[MagicMock, None, None]:
    """Mock CortexClient for compliance logging."""
    with patch("app.main.cortex_client") as mock_cortex:
        mock_cortex.log_compliance_event = Mock()
        yield mock_cortex


@pytest.fixture
def test_client(mock_cortx_client, mock_cortex_client) -> TestClient:
    """Create test client with mocked dependencies."""
    import uuid

    from app.main import app
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    # Add middleware to set correlation_id on request.state
    class CorrelationIDMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            request.state.correlation_id = str(uuid.uuid4())
            response = await call_next(request)
            return response

    # Clear existing middleware and add test middleware
    app.user_middleware = []
    app.middleware_stack = None
    app.add_middleware(CorrelationIDMiddleware)
    app.build_middleware_stack()

    return TestClient(app)


@pytest.fixture
def sample_validation_request() -> Dict[str, Any]:
    """Sample validation request payload."""
    return {
        "rule_pack_id": "test.rulepack.v1",
        "payload": {
            "id": "test-123",
            "data": {"amount": 100.50, "currency": "USD", "account_number": "1234567890"},
        },
        "validation_type": "standard",
        "strict_mode": True,
        "metadata": {"source": "test_suite", "environment": "testing"},
    }


@pytest.fixture
def sample_rule_pack() -> Dict[str, Any]:
    """Sample RulePack for testing validation logic."""
    return {
        "pack_id": "test.rulepack.v1",
        "version": "1.0.0",
        "rules": [
            {"name": "check_id", "type": "required_field", "field": "id", "severity": "error"},
            {"name": "check_data", "type": "required_field", "field": "data", "severity": "error"},
            {
                "name": "check_amount_positive",
                "type": "range_check",
                "field": "amount",
                "min": 0,
                "max": 1000000,
                "severity": "warning",
            },
        ],
    }


@pytest.fixture
def sample_rule_pack_with_format_validation() -> Dict[str, Any]:
    """RulePack with format validation rules."""
    return {
        "pack_id": "format.validation.pack",
        "version": "1.0.0",
        "rules": [
            {
                "name": "email_format",
                "type": "format_validation",
                "field": "email",
                "pattern": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
                "required": True,
            },
            {
                "name": "phone_format",
                "type": "format_validation",
                "field": "phone",
                "pattern": r"^\d{10}$",
                "required": False,
            },
        ],
    }


@pytest.fixture
def sample_rule_pack_with_all_operators() -> Dict[str, Any]:
    """RulePack with various operators for comprehensive testing."""
    return {
        "pack_id": "comprehensive.pack",
        "version": "1.0.0",
        "rules": [
            {"name": "required_id", "type": "required_field", "field": "id"},
            {
                "name": "amount_range",
                "type": "range_check",
                "field": "amount",
                "min": 10,
                "max": 1000,
            },
            {
                "name": "status_format",
                "type": "format_validation",
                "field": "status",
                "pattern": r"^(active|inactive|pending)$",
                "required": True,
            },
            {"name": "custom_validation", "type": "custom", "field": "custom_field"},
        ],
    }


@pytest.fixture
def valid_payload_for_comprehensive_pack() -> Dict[str, Any]:
    """Valid payload matching comprehensive pack rules."""
    return {"id": "test-123", "amount": 500, "status": "active", "custom_field": "test"}


@pytest.fixture
def invalid_payload_missing_fields() -> Dict[str, Any]:
    """Payload with missing required fields."""
    return {
        "amount": 50
        # Missing: id, data
    }


@pytest.fixture
def invalid_payload_out_of_range() -> Dict[str, Any]:
    """Payload with values outside allowed range."""
    return {"id": "test-123", "amount": -100}  # Negative amount


@pytest.fixture
def invalid_payload_format_mismatch() -> Dict[str, Any]:
    """Payload with format validation failures."""
    return {
        "email": "not-an-email",  # Invalid email format
        "phone": "123",  # Invalid phone format (too short)
    }


@pytest.fixture
def sample_raw_validation_result_success() -> Dict[str, Any]:
    """Sample raw validation result (success)."""
    return {
        "valid": True,
        "errors": [],
        "warnings": [],
        "rule_results": {
            "rule_1": {"passed": True, "message": "Validation passed", "metadata": {}},
            "rule_2": {
                "passed": True,
                "message": "All checks passed",
                "metadata": {"checked_fields": ["id", "data"]},
            },
        },
        "metadata": {"execution_time": 10, "rules_executed": 2},
    }


@pytest.fixture
def sample_raw_validation_result_with_errors() -> Dict[str, Any]:
    """Sample raw validation result with errors."""
    return {
        "valid": False,
        "errors": [
            {
                "code": "MISSING_FIELD",
                "message": "Required field 'account_number' contains PII: 1234567890",
                "field": "account_number",
                "severity": "error",
            },
            {
                "code": "INVALID_FORMAT",
                "message": "Email john.doe@example.com does not match pattern",
                "field": "email",
                "severity": "error",
            },
        ],
        "warnings": [
            {
                "code": "DEPRECATED_FIELD",
                "message": "Field 'legacy_id' is deprecated, SSN: 123-45-6789",
                "field": "legacy_id",
                "severity": "warning",
            }
        ],
        "rule_results": {
            "rule_1": {
                "passed": False,
                "message": "Field validation failed with sensitive data: credit card 4111-1111-1111-1111",
                "metadata": {},
            }
        },
    }


@pytest.fixture
def sample_raw_validation_result_with_warnings() -> Dict[str, Any]:
    """Sample raw validation result with warnings only."""
    return {
        "valid": True,
        "errors": [],
        "warnings": [
            {
                "code": "RANGE_WARNING",
                "message": "Value is within acceptable range but close to limit",
                "field": "amount",
                "severity": "warning",
            }
        ],
        "rule_results": {
            "rule_1": {
                "passed": True,
                "message": "Passed with warning",
                "metadata": {"warning_threshold_reached": True},
            }
        },
    }


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """Mock authentication headers (when auth is enabled)."""
    return {
        "Authorization": "Bearer test-token-12345",
        "X-User-ID": "test-user",
        "X-Tenant-ID": "test-tenant",
    }


@pytest.fixture
def correlation_id() -> str:
    """Sample correlation ID for tracing."""
    return "test-correlation-id-12345"


@pytest.fixture
def traceparent() -> str:
    """Sample W3C traceparent header."""
    return "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
