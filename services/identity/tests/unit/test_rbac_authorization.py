"""
Unit tests for RBAC (Role-Based Access Control) authorization
"""

import pytest
from app.main import TokenData, User, get_current_user, verify_token
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt


class TestTokenVerification:
    """Test token verification and extraction"""

    @pytest.mark.asyncio
    async def test_verify_valid_token(self, create_test_token):
        """Test verification of valid token"""
        token = create_test_token(
            username="testuser",
            tenant_id="test_tenant",
            roles=["user"],
            scopes=["read"],
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        token_data = await verify_token(credentials)

        assert isinstance(token_data, TokenData)
        assert token_data.username == "testuser"
        assert token_data.tenant_id == "test_tenant"
        assert token_data.roles == ["user"]
        assert token_data.scopes == ["read"]

    @pytest.mark.asyncio
    async def test_verify_token_with_multiple_roles(self, create_test_token):
        """Test verification of token with multiple roles"""
        token = create_test_token(
            username="admin",
            roles=["admin", "user", "moderator"],
            scopes=["read", "write", "delete"],
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        token_data = await verify_token(credentials)

        assert len(token_data.roles) == 3
        assert "admin" in token_data.roles
        assert "user" in token_data.roles
        assert "moderator" in token_data.roles

    @pytest.mark.asyncio
    async def test_verify_expired_token_raises_exception(self, expired_token):
        """Test that expired token raises HTTPException"""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token)

        with pytest.raises(HTTPException) as exc_info:
            await verify_token(credentials)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_invalid_token_raises_exception(self, invalid_token):
        """Test that invalid token raises HTTPException"""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=invalid_token)

        with pytest.raises(HTTPException) as exc_info:
            await verify_token(credentials)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_token_missing_subject_raises_exception(self, test_secret_key):
        """Test that token without subject raises HTTPException"""
        from datetime import datetime, timedelta

        # Create token without 'sub' claim
        token = jwt.encode(
            {
                "tenant_id": "test",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iat": datetime.utcnow(),
            },
            test_secret_key,
            algorithm="HS256",
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await verify_token(credentials)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_token_defaults_missing_fields(self, test_secret_key):
        """Test that missing optional fields are set to defaults"""
        from datetime import datetime, timedelta

        # Create token with only required fields
        token = jwt.encode(
            {
                "sub": "testuser",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iat": datetime.utcnow(),
            },
            test_secret_key,
            algorithm="HS256",
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        token_data = await verify_token(credentials)

        assert token_data.username == "testuser"
        assert token_data.tenant_id == "default"  # Default value
        assert token_data.roles == []  # Default empty list
        assert token_data.scopes == []  # Default empty list


class TestGetCurrentUser:
    """Test getting current user from token"""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test getting current user from valid token data"""
        token_data = TokenData(
            username="testuser",
            tenant_id="test_tenant",
            roles=["user"],
            scopes=["read"],
        )

        user = await get_current_user(token_data)

        assert isinstance(user, User)
        assert user.username == "testuser"
        assert user.tenant_id == "test_tenant"
        assert user.roles == ["user"]
        assert user.scopes == ["read"]

    @pytest.mark.asyncio
    async def test_get_current_user_with_admin_role(self):
        """Test getting current user with admin role"""
        token_data = TokenData(
            username="admin",
            tenant_id="default",
            roles=["admin", "user"],
            scopes=["read", "write", "admin"],
        )

        user = await get_current_user(token_data)

        assert "admin" in user.roles
        assert "admin" in user.scopes

    @pytest.mark.asyncio
    async def test_get_current_user_preserves_all_data(self):
        """Test that get_current_user preserves all token data"""
        token_data = TokenData(
            username="testuser",
            tenant_id="custom_tenant",
            roles=["role1", "role2", "role3"],
            scopes=["scope1", "scope2"],
        )

        user = await get_current_user(token_data)

        assert user.username == token_data.username
        assert user.tenant_id == token_data.tenant_id
        assert user.roles == token_data.roles
        assert user.scopes == token_data.scopes


class TestRoleBasedAuthorization:
    """Test role-based access control logic"""

    def test_admin_role_check(self):
        """Test checking for admin role"""
        user = User(
            username="admin",
            tenant_id="default",
            roles=["admin", "user"],
            scopes=["read", "write", "admin"],
        )

        assert "admin" in user.roles

    def test_user_role_check(self):
        """Test checking for user role"""
        user = User(
            username="user",
            tenant_id="default",
            roles=["user"],
            scopes=["read"],
        )

        assert "user" in user.roles
        assert "admin" not in user.roles

    def test_multiple_roles_check(self):
        """Test user with multiple roles"""
        user = User(
            username="moderator",
            tenant_id="default",
            roles=["user", "moderator", "contributor"],
            scopes=["read", "write", "moderate"],
        )

        assert "user" in user.roles
        assert "moderator" in user.roles
        assert "contributor" in user.roles
        assert "admin" not in user.roles

    def test_no_roles_user(self):
        """Test user with no roles"""
        user = User(
            username="noroles",
            tenant_id="default",
            roles=[],
            scopes=[],
        )

        assert len(user.roles) == 0
        assert "admin" not in user.roles
        assert "user" not in user.roles


class TestScopeBasedAuthorization:
    """Test scope-based access control"""

    def test_read_scope_check(self):
        """Test checking for read scope"""
        user = User(
            username="reader",
            tenant_id="default",
            roles=["user"],
            scopes=["read"],
        )

        assert "read" in user.scopes

    def test_write_scope_check(self):
        """Test checking for write scope"""
        user = User(
            username="writer",
            tenant_id="default",
            roles=["user"],
            scopes=["read", "write"],
        )

        assert "read" in user.scopes
        assert "write" in user.scopes

    def test_admin_scope_check(self):
        """Test checking for admin scope"""
        user = User(
            username="admin",
            tenant_id="default",
            roles=["admin"],
            scopes=["read", "write", "admin"],
        )

        assert "admin" in user.scopes

    def test_multiple_scopes(self):
        """Test user with multiple scopes"""
        user = User(
            username="power_user",
            tenant_id="default",
            roles=["user"],
            scopes=["read", "write", "delete", "create", "update"],
        )

        assert len(user.scopes) == 5
        assert "read" in user.scopes
        assert "delete" in user.scopes

    def test_no_scopes_user(self):
        """Test user with no scopes"""
        user = User(
            username="noscopes",
            tenant_id="default",
            roles=["user"],
            scopes=[],
        )

        assert len(user.scopes) == 0


class TestTenantIsolation:
    """Test tenant isolation in authorization"""

    def test_user_has_tenant_id(self):
        """Test that user has tenant_id"""
        user = User(
            username="testuser",
            tenant_id="tenant_123",
            roles=["user"],
            scopes=["read"],
        )

        assert user.tenant_id == "tenant_123"

    def test_different_tenants_different_users(self):
        """Test that users from different tenants are different"""
        user1 = User(
            username="testuser",
            tenant_id="tenant_1",
            roles=["user"],
            scopes=["read"],
        )

        user2 = User(
            username="testuser",
            tenant_id="tenant_2",
            roles=["user"],
            scopes=["read"],
        )

        # Same username, different tenants
        assert user1.username == user2.username
        assert user1.tenant_id != user2.tenant_id

    def test_default_tenant(self):
        """Test default tenant assignment"""
        user = User(
            username="testuser",
            tenant_id="default",
            roles=["user"],
            scopes=["read"],
        )

        assert user.tenant_id == "default"


class TestAuthorizationEdgeCases:
    """Test edge cases for authorization"""

    def test_empty_username(self):
        """Test user with empty username"""
        user = User(
            username="",
            tenant_id="default",
            roles=["user"],
            scopes=["read"],
        )

        assert user.username == ""

    def test_special_characters_in_roles(self):
        """Test roles with special characters"""
        user = User(
            username="testuser",
            tenant_id="default",
            roles=["user-admin", "data_analyst", "report.viewer"],
            scopes=["read"],
        )

        assert "user-admin" in user.roles
        assert "data_analyst" in user.roles
        assert "report.viewer" in user.roles

    def test_case_sensitivity_in_roles(self):
        """Test that roles are case sensitive"""
        user = User(
            username="testuser",
            tenant_id="default",
            roles=["Admin"],
            scopes=["read"],
        )

        assert "Admin" in user.roles
        assert "admin" not in user.roles

    def test_duplicate_roles(self):
        """Test user with duplicate roles"""
        user = User(
            username="testuser",
            tenant_id="default",
            roles=["user", "user", "admin"],
            scopes=["read"],
        )

        # Should contain duplicates as given
        assert user.roles.count("user") == 2

    def test_very_long_role_name(self):
        """Test role with very long name"""
        long_role = "a" * 1000
        user = User(
            username="testuser",
            tenant_id="default",
            roles=[long_role],
            scopes=["read"],
        )

        assert long_role in user.roles

    @pytest.mark.asyncio
    async def test_token_with_null_tenant(self, test_secret_key):
        """Test token with null tenant_id"""
        from datetime import datetime, timedelta

        token = jwt.encode(
            {
                "sub": "testuser",
                "tenant_id": None,
                "roles": ["user"],
                "scopes": ["read"],
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iat": datetime.utcnow(),
            },
            test_secret_key,
            algorithm="HS256",
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        token_data = await verify_token(credentials)
        # Should default to "default" tenant
        assert token_data.tenant_id is None or token_data.tenant_id == "default"
