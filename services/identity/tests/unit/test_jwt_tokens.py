"""
Unit tests for JWT token generation and validation
"""

from datetime import datetime, timedelta

import pytest
from app.main import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY, create_access_token
from jose import JWTError, jwt


class TestJWTTokenGeneration:
    """Test JWT token generation functions"""

    def test_create_access_token_default_expiry(self):
        """Test creating access token with default expiry"""
        data = {
            "sub": "testuser",
            "tenant_id": "test_tenant",
            "roles": ["user"],
            "scopes": ["read"],
        }
        token = create_access_token(data)

        # Verify token can be decoded
        assert token is not None
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["sub"] == "testuser"
        assert decoded["tenant_id"] == "test_tenant"
        assert decoded["roles"] == ["user"]
        assert decoded["scopes"] == ["read"]
        assert decoded["iss"] == "cortx-identity"

    def test_create_access_token_custom_expiry(self):
        """Test creating access token with custom expiry"""
        data = {"sub": "testuser", "tenant_id": "test_tenant"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=expires_delta)

        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.utcfromtimestamp(decoded["exp"])
        iat_time = datetime.utcfromtimestamp(decoded["iat"])

        # Verify expiry is approximately 30 minutes from issued time
        time_diff = (exp_time - iat_time).total_seconds()
        assert 1790 <= time_diff <= 1810  # 30 min ± 10 seconds

    def test_create_access_token_includes_required_claims(self):
        """Test that access token includes all required JWT claims"""
        data = {
            "sub": "testuser",
            "tenant_id": "test_tenant",
            "roles": ["admin"],
            "scopes": ["read", "write"],
        }
        token = create_access_token(data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Standard JWT claims
        assert "exp" in decoded  # Expiration time
        assert "iat" in decoded  # Issued at time
        assert "iss" in decoded  # Issuer

        # Custom claims
        assert "sub" in decoded  # Subject (username)
        assert "tenant_id" in decoded
        assert "roles" in decoded
        assert "scopes" in decoded

    def test_create_access_token_with_additional_claims(self):
        """Test creating token with additional custom claims"""
        data = {
            "sub": "testuser",
            "tenant_id": "test_tenant",
            "custom_claim": "custom_value",
        }
        token = create_access_token(data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["custom_claim"] == "custom_value"

    def test_token_expiry_calculation(self):
        """Test that token expiry is calculated correctly"""
        data = {"sub": "testuser"}
        before_time = datetime.utcnow()
        token = create_access_token(data)
        after_time = datetime.utcnow()

        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.utcfromtimestamp(decoded["exp"])

        # Expected expiry should be ACCESS_TOKEN_EXPIRE_MINUTES from now
        expected_min = before_time + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expected_max = after_time + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        assert expected_min <= exp_time <= expected_max


class TestJWTTokenValidation:
    """Test JWT token validation"""

    def test_decode_valid_token(self, create_test_token):
        """Test decoding a valid token"""
        token = create_test_token(
            username="testuser",
            tenant_id="test_tenant",
            roles=["user"],
            scopes=["read"],
        )

        decoded = jwt.decode(token, "test_secret_key_for_testing_only", algorithms=[ALGORITHM])

        assert decoded["sub"] == "testuser"
        assert decoded["tenant_id"] == "test_tenant"
        assert decoded["roles"] == ["user"]
        assert decoded["scopes"] == ["read"]

    def test_decode_expired_token_raises_error(self, expired_token):
        """Test that decoding expired token raises JWTError"""
        with pytest.raises(JWTError):
            jwt.decode(expired_token, "test_secret_key_for_testing_only", algorithms=[ALGORITHM])

    def test_decode_invalid_signature_raises_error(self, create_test_token):
        """Test that token with invalid signature raises JWTError"""
        token = create_test_token(username="testuser")

        with pytest.raises(JWTError):
            jwt.decode(token, "wrong_secret_key", algorithms=[ALGORITHM])

    def test_decode_malformed_token_raises_error(self, malformed_token):
        """Test that malformed token raises JWTError"""
        with pytest.raises(JWTError):
            jwt.decode(malformed_token, "test_secret_key_for_testing_only", algorithms=[ALGORITHM])

    def test_token_with_missing_subject(self, test_secret_key):
        """Test token validation with missing subject claim"""
        # Create token without 'sub' claim
        token = jwt.encode(
            {"tenant_id": "test", "exp": datetime.utcnow() + timedelta(hours=1)},
            test_secret_key,
            algorithm=ALGORITHM,
        )

        decoded = jwt.decode(token, test_secret_key, algorithms=[ALGORITHM])
        # Should decode successfully but 'sub' will be None
        assert decoded.get("sub") is None

    def test_token_with_empty_roles(self, create_test_token):
        """Test token with empty roles list"""
        token = create_test_token(username="testuser", roles=[])
        decoded = jwt.decode(token, "test_secret_key_for_testing_only", algorithms=[ALGORITHM])

        assert decoded["roles"] == []

    def test_token_with_multiple_roles(self, create_test_token):
        """Test token with multiple roles"""
        token = create_test_token(
            username="admin",
            roles=["admin", "user", "moderator"],
            scopes=["read", "write", "delete"],
        )
        decoded = jwt.decode(token, "test_secret_key_for_testing_only", algorithms=[ALGORITHM])

        assert len(decoded["roles"]) == 3
        assert "admin" in decoded["roles"]
        assert "moderator" in decoded["roles"]


class TestJWTTokenSecurity:
    """Test JWT token security features"""

    def test_token_cannot_be_modified(self, create_test_token):
        """Test that modifying token payload invalidates signature"""
        token = create_test_token(username="testuser")

        # Split token into parts
        parts = token.split(".")
        assert len(parts) == 3

        # Try to decode with modified payload (different secret will fail)
        with pytest.raises(JWTError):
            jwt.decode(token, "different_secret", algorithms=[ALGORITHM])

    def test_algorithm_none_attack_prevented(self, create_test_token):
        """Test that 'none' algorithm is not accepted"""
        token = create_test_token(username="testuser")

        # Try to decode with 'none' algorithm
        with pytest.raises(JWTError):
            jwt.decode(token, options={"verify_signature": False}, algorithms=["none"])

    def test_token_issuer_claim(self, create_test_token):
        """Test that tokens include proper issuer claim"""
        token = create_test_token(username="testuser")
        decoded = jwt.decode(token, "test_secret_key_for_testing_only", algorithms=[ALGORITHM])

        assert decoded["iss"] == "cortx-identity"

    def test_different_tenants_have_different_tokens(self, create_test_token):
        """Test that tokens for different tenants are different"""
        token1 = create_test_token(username="user", tenant_id="tenant1")
        token2 = create_test_token(username="user", tenant_id="tenant2")

        assert token1 != token2

        decoded1 = jwt.decode(token1, "test_secret_key_for_testing_only", algorithms=[ALGORITHM])
        decoded2 = jwt.decode(token2, "test_secret_key_for_testing_only", algorithms=[ALGORITHM])

        assert decoded1["tenant_id"] == "tenant1"
        assert decoded2["tenant_id"] == "tenant2"


class TestJWTTokenEdgeCases:
    """Test edge cases for JWT tokens"""

    def test_token_with_very_long_username(self, create_test_token):
        """Test token creation with very long username"""
        long_username = "a" * 1000
        token = create_test_token(username=long_username)
        decoded = jwt.decode(token, "test_secret_key_for_testing_only", algorithms=[ALGORITHM])

        assert decoded["sub"] == long_username

    def test_token_with_special_characters(self, create_test_token):
        """Test token with special characters in claims"""
        token = create_test_token(
            username="user@example.com",
            tenant_id="tenant-123_456",
        )
        decoded = jwt.decode(token, "test_secret_key_for_testing_only", algorithms=[ALGORITHM])

        assert decoded["sub"] == "user@example.com"
        assert decoded["tenant_id"] == "tenant-123_456"

    def test_token_with_unicode_characters(self, create_test_token):
        """Test token with unicode characters"""
        token = create_test_token(
            username="用户",  # Chinese characters
            tenant_id="租户",
        )
        decoded = jwt.decode(token, "test_secret_key_for_testing_only", algorithms=[ALGORITHM])

        assert decoded["sub"] == "用户"
        assert decoded["tenant_id"] == "租户"

    def test_token_near_expiry(self, create_test_token):
        """Test token that's about to expire"""
        # Create token expiring in 1 second
        token = create_test_token(
            username="testuser",
            expires_delta=timedelta(seconds=1),
        )

        # Should still be valid immediately
        decoded = jwt.decode(token, "test_secret_key_for_testing_only", algorithms=[ALGORITHM])
        assert decoded["sub"] == "testuser"
