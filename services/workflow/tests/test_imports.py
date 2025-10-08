"""Test that all imports work correctly"""



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
