"""
Unit tests for refresh token handling
"""

from datetime import datetime, timedelta

import pytest
from app.refresh import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_SECRET_KEY,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
)
from jose import jwt


class TestRefreshTokenGeneration:
    """Test refresh token generation"""

    def test_create_refresh_token_basic(self):
        """Test creating a basic refresh token"""
        data = {
            "sub": "testuser",
            "tenant_id": "test_tenant",
            "roles": ["user"],
            "scopes": ["read"],
        }

        token = create_refresh_token(data)

        assert token is not None
        decoded = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["sub"] == "testuser"
        assert decoded["tenant_id"] == "test_tenant"
        assert decoded["roles"] == ["user"]
        assert decoded["scopes"] == ["read"]
        assert decoded["type"] == "refresh"

    def test_create_refresh_token_expiry(self):
        """Test refresh token expiry time"""
        data = {"sub": "testuser", "tenant_id": "test_tenant"}

        before_time = datetime.utcnow()
        token = create_refresh_token(data)
        after_time = datetime.utcnow()

        decoded = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.utcfromtimestamp(decoded["exp"])
        iat_time = datetime.utcfromtimestamp(decoded["iat"])

        # Verify expiry is approximately REFRESH_TOKEN_EXPIRE_DAYS from issued time
        expected_min = before_time + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        expected_max = after_time + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        assert expected_min <= exp_time <= expected_max

    def test_create_refresh_token_has_type_claim(self):
        """Test that refresh token has 'type' claim set to 'refresh'"""
        data = {"sub": "testuser"}
        token = create_refresh_token(data)

        decoded = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        assert "type" in decoded
        assert decoded["type"] == "refresh"

    def test_create_refresh_token_includes_all_user_data(self):
        """Test that refresh token includes all user data"""
        data = {
            "sub": "testuser",
            "tenant_id": "custom_tenant",
            "roles": ["admin", "user"],
            "scopes": ["read", "write", "admin"],
        }

        token = create_refresh_token(data)
        decoded = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["sub"] == "testuser"
        assert decoded["tenant_id"] == "custom_tenant"
        assert decoded["roles"] == ["admin", "user"]
        assert decoded["scopes"] == ["read", "write", "admin"]

    def test_create_refresh_token_with_different_secret(self):
        """Test that refresh token uses different secret key"""
        data = {"sub": "testuser"}
        token = create_refresh_token(data)

        # Should fail to decode with access token secret
        with pytest.raises(Exception):
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Should succeed with refresh token secret
        decoded = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "testuser"


class TestAccessTokenFromRefresh:
    """Test creating access tokens from refresh tokens"""

    def test_create_access_token_basic(self):
        """Test creating access token from refresh module"""
        data = {
            "sub": "testuser",
            "tenant_id": "test_tenant",
            "roles": ["user"],
            "scopes": ["read"],
        }

        token = create_access_token(data)

        assert token is not None
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["sub"] == "testuser"
        assert decoded["type"] == "access"

    def test_create_access_token_expiry(self):
        """Test access token expiry time"""
        data = {"sub": "testuser"}

        before_time = datetime.utcnow()
        token = create_access_token(data)
        after_time = datetime.utcnow()

        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.utcfromtimestamp(decoded["exp"])

        # Verify expiry is approximately ACCESS_TOKEN_EXPIRE_MINUTES from now
        expected_min = before_time + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expected_max = after_time + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        assert expected_min <= exp_time <= expected_max

    def test_create_access_token_has_type_claim(self):
        """Test that access token has 'type' claim set to 'access'"""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert "type" in decoded
        assert decoded["type"] == "access"

    def test_refresh_token_longer_expiry_than_access(self):
        """Test that refresh tokens expire later than access tokens"""
        # Refresh token should expire in days, access token in minutes
        assert REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 > ACCESS_TOKEN_EXPIRE_MINUTES


class TestTokenTypeDifferentiation:
    """Test differentiation between access and refresh tokens"""

    def test_refresh_token_type_is_refresh(self):
        """Test that refresh token has type='refresh'"""
        data = {"sub": "testuser"}
        token = create_refresh_token(data)

        decoded = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["type"] == "refresh"

    def test_access_token_type_is_access(self):
        """Test that access token has type='access'"""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["type"] == "access"

    def test_token_types_are_different(self):
        """Test that access and refresh tokens are different"""
        data = {"sub": "testuser", "tenant_id": "test"}

        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        assert access_token != refresh_token

        access_decoded = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        refresh_decoded = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        assert access_decoded["type"] == "access"
        assert refresh_decoded["type"] == "refresh"


class TestRefreshTokenSecurity:
    """Test security aspects of refresh tokens"""

    def test_refresh_token_cannot_be_decoded_with_access_secret(self):
        """Test that refresh token cannot be decoded with access token secret"""
        data = {"sub": "testuser"}
        refresh_token = create_refresh_token(data)

        # Should fail with wrong secret
        with pytest.raises(Exception):
            jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

    def test_access_token_cannot_be_decoded_with_refresh_secret(self):
        """Test that access token cannot be decoded with refresh token secret"""
        data = {"sub": "testuser"}
        access_token = create_access_token(data)

        # Should fail with wrong secret
        with pytest.raises(Exception):
            jwt.decode(access_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

    def test_refresh_token_preserves_user_data(self):
        """Test that refresh token preserves all user data for new access token"""
        data = {
            "sub": "testuser",
            "tenant_id": "test_tenant",
            "roles": ["admin", "user"],
            "scopes": ["read", "write", "admin"],
        }

        refresh_token = create_refresh_token(data)
        decoded = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        # All data should be preserved
        assert decoded["sub"] == data["sub"]
        assert decoded["tenant_id"] == data["tenant_id"]
        assert decoded["roles"] == data["roles"]
        assert decoded["scopes"] == data["scopes"]

    def test_different_users_different_refresh_tokens(self):
        """Test that different users get different refresh tokens"""
        token1 = create_refresh_token({"sub": "user1", "tenant_id": "tenant1"})
        token2 = create_refresh_token({"sub": "user2", "tenant_id": "tenant1"})

        assert token1 != token2

        decoded1 = jwt.decode(token1, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        decoded2 = jwt.decode(token2, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded1["sub"] != decoded2["sub"]


class TestRefreshTokenEdgeCases:
    """Test edge cases for refresh tokens"""

    def test_refresh_token_with_empty_roles(self):
        """Test refresh token with empty roles"""
        data = {"sub": "testuser", "roles": [], "scopes": []}
        token = create_refresh_token(data)

        decoded = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["roles"] == []
        assert decoded["scopes"] == []

    def test_refresh_token_with_many_roles(self):
        """Test refresh token with many roles"""
        roles = [f"role_{i}" for i in range(100)]
        data = {"sub": "testuser", "roles": roles}
        token = create_refresh_token(data)

        decoded = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        assert len(decoded["roles"]) == 100

    def test_refresh_token_with_special_characters(self):
        """Test refresh token with special characters"""
        data = {
            "sub": "user@example.com",
            "tenant_id": "tenant-123_456",
            "roles": ["role:admin", "role.user"],
        }
        token = create_refresh_token(data)

        decoded = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["sub"] == "user@example.com"
        assert decoded["tenant_id"] == "tenant-123_456"

    def test_refresh_token_with_unicode(self):
        """Test refresh token with unicode characters"""
        data = {"sub": "用户", "tenant_id": "租户"}
        token = create_refresh_token(data)

        decoded = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["sub"] == "用户"
        assert decoded["tenant_id"] == "租户"

    def test_refresh_token_timestamp_fields(self):
        """Test that refresh token has correct timestamp fields"""
        data = {"sub": "testuser"}
        token = create_refresh_token(data)

        decoded = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        assert "iat" in decoded  # Issued at
        assert "exp" in decoded  # Expiration

        iat_time = datetime.utcfromtimestamp(decoded["iat"])
        exp_time = datetime.utcfromtimestamp(decoded["exp"])

        # Expiration should be after issued time
        assert exp_time > iat_time


class TestTokenRotation:
    """Test token rotation scenarios"""

    def test_can_create_new_access_token_from_refresh_data(self):
        """Test creating new access token from refresh token data"""
        # Simulate refresh flow
        original_data = {
            "sub": "testuser",
            "tenant_id": "test_tenant",
            "roles": ["user"],
            "scopes": ["read"],
        }

        # Create refresh token
        refresh_token = create_refresh_token(original_data)

        # Decode refresh token
        decoded = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        # Extract user data
        user_data = {
            "sub": decoded["sub"],
            "tenant_id": decoded["tenant_id"],
            "roles": decoded["roles"],
            "scopes": decoded["scopes"],
        }

        # Create new access token
        new_access_token = create_access_token(user_data)

        # Verify new access token
        access_decoded = jwt.decode(new_access_token, SECRET_KEY, algorithms=[ALGORITHM])

        assert access_decoded["sub"] == original_data["sub"]
        assert access_decoded["tenant_id"] == original_data["tenant_id"]
        assert access_decoded["type"] == "access"

    def test_multiple_access_tokens_from_same_refresh(self):
        """Test creating multiple access tokens from same refresh token data"""
        refresh_data = {"sub": "testuser", "tenant_id": "test"}

        # Create multiple access tokens
        access1 = create_access_token(refresh_data)
        access2 = create_access_token(refresh_data)

        # Tokens should be different (due to timestamp)
        assert access1 != access2

        # But should contain same user data
        decoded1 = jwt.decode(access1, SECRET_KEY, algorithms=[ALGORITHM])
        decoded2 = jwt.decode(access2, SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded1["sub"] == decoded2["sub"]
        assert decoded1["tenant_id"] == decoded2["tenant_id"]
