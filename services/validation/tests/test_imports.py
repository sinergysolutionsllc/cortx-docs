"""Test that all imports work correctly"""

import pytest


def test_cortx_backend_imports():
    """Verify cortx_backend package imports successfully"""
    from cortx_backend.common.audit import sha256_hex
    from cortx_backend.common.cortex_client import CortexClient
    from cortx_backend.common.models import ComplianceEvent, ComplianceLevel, EventType

    assert callable(sha256_hex)
    assert ComplianceEvent is not None
    assert EventType is not None
    assert ComplianceLevel is not None
    assert CortexClient is not None


@pytest.mark.skip(reason="cortx_backend is mocked in tests - skip actual implementation tests")
def test_sha256_hex_function():
    """Test sha256_hex utility function"""
    from cortx_backend.common.audit import sha256_hex

    result = sha256_hex("test")
    assert isinstance(result, str)
    assert len(result) == 64  # SHA256 hex is 64 characters

    # Same input should produce same hash
    assert sha256_hex("test") == result

    # Different input should produce different hash
    assert sha256_hex("different") != result


@pytest.mark.skip(reason="cortx_backend is mocked in tests - skip actual implementation tests")
def test_compliance_event_model():
    """Test ComplianceEvent Pydantic model"""
    from cortx_backend.common.models import ComplianceEvent, ComplianceLevel, EventType

    event = ComplianceEvent(
        event_type=EventType.DATA_VALIDATE,
        compliance_level=ComplianceLevel.LOW,
        action="Test validation action",
    )

    assert event.event_type == EventType.DATA_VALIDATE
    assert event.compliance_level == ComplianceLevel.LOW
    assert event.action == "Test validation action"
    assert event.tenant_id == "default"

    # Test with additional fields
    event_with_details = ComplianceEvent(
        event_type=EventType.WORKFLOW_START,
        compliance_level=ComplianceLevel.HIGH,
        action="Start workflow",
        user_id="test-user",
        details={"key": "value"},
    )

    assert event_with_details.details == {"key": "value"}
    assert event_with_details.user_id == "test-user"

    # Test hash signing
    event.sign()
    assert event.hash is not None
    assert len(event.hash) == 64  # SHA256 hex
