"""
Unit tests for Authentication Middleware

Tests JWT authentication, token verification, and authorization checks
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.middleware.auth import AuthMiddleware, get_current_user, require_role, require_scope
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials


@pytest.mark.unit
@pytest.mark.auth
class TestAuthMiddlewareInitialization:
    """Test AuthMiddleware initialization"""

    def test_init_default_identity_url(self):
        """Test AuthMiddleware initializes with default identity URL"""
        middleware = AuthMiddleware()

        assert middleware.identity_url is not None
        assert middleware.client is not None

    def test_init_custom_identity_url(self):
        """Test AuthMiddleware initializes with custom identity URL"""
        custom_url = "http://custom-identity:8082"
        middleware = AuthMiddleware(identity_url=custom_url)

        assert middleware.identity_url == custom_url


@pytest.mark.unit
@pytest.mark.auth
class TestRemoteTokenVerification:
    """Test remote token verification with identity service"""

    @pytest.mark.asyncio
    async def test_verify_token_remote_success(self, mock_httpx_client):
        """Test successful remote token verification"""
        middleware = AuthMiddleware()
        middleware.client = mock_httpx_client

        # Configure mock response
        mock_httpx_client.get = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(
            return_value={
                "valid": True,
                "username": "test_user",
                "tenant_id": "test_tenant",
                "roles": ["user"],
                "scopes": ["read", "write"],
            }
        )
        mock_httpx_client.get.return_value = mock_response

        result = await middleware.verify_token_remote("test-token")

        assert result is not None
        assert result["valid"] is True
        assert result["username"] == "test_user"
        assert mock_httpx_client.get.called

    @pytest.mark.asyncio
    async def test_verify_token_remote_invalid(self, mock_httpx_client):
        """Test remote token verification with invalid token"""
        middleware = AuthMiddleware()
        middleware.client = mock_httpx_client

        mock_httpx_client.get = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_httpx_client.get.return_value = mock_response

        result = await middleware.verify_token_remote("invalid-token")

        assert result is None

    @pytest.mark.asyncio
    async def test_verify_token_remote_network_error(self, mock_httpx_client):
        """Test remote token verification handles network errors"""
        middleware = AuthMiddleware()
        middleware.client = mock_httpx_client

        mock_httpx_client.get = AsyncMock(side_effect=Exception("Network error"))

        result = await middleware.verify_token_remote("test-token")

        assert result is None


@pytest.mark.unit
@pytest.mark.auth
class TestLocalTokenVerification:
    """Test local token verification"""

    def test_verify_token_local_success(self, create_test_token):
        """Test successful local token verification"""
        middleware = AuthMiddleware()

        token = create_test_token(
            username="test_user", tenant_id="test_tenant", roles=["user"], scopes=["read"]
        )

        with patch.dict("os.environ", {"JWT_SECRET_KEY": "test-secret-key-for-testing-only"}):
            with patch("app.middleware.auth.JWT_SECRET_KEY", "test-secret-key-for-testing-only"):
                result = middleware.verify_token_local(token)

                assert result is not None
                assert result["valid"] is True
                assert result["username"] == "test_user"
                assert result["tenant_id"] == "test_tenant"

    def test_verify_token_local_no_secret_key(self, create_test_token):
        """Test local token verification returns None without secret key"""
        middleware = AuthMiddleware()

        token = create_test_token()

        with patch("app.middleware.auth.JWT_SECRET_KEY", None):
            result = middleware.verify_token_local(token)

            assert result is None

    def test_verify_token_local_invalid_token(self):
        """Test local token verification with invalid token"""
        middleware = AuthMiddleware()

        with patch("app.middleware.auth.JWT_SECRET_KEY", "test-secret-key"):
            result = middleware.verify_token_local("invalid-token")

            assert result is None


@pytest.mark.unit
@pytest.mark.auth
class TestAuthMiddlewareCall:
    """Test AuthMiddleware __call__ method"""

    @pytest.mark.asyncio
    async def test_call_public_endpoint(self):
        """Test middleware allows public endpoints"""
        middleware = AuthMiddleware()

        request = Mock(spec=Request)
        request.url.path = "/health"

        result = await middleware(request, credentials=None)

        assert result is None

    @pytest.mark.asyncio
    async def test_call_no_credentials_no_cookie(self):
        """Test middleware raises 401 without credentials or cookie"""
        middleware = AuthMiddleware()

        request = Mock(spec=Request)
        request.url.path = "/api/protected"
        request.cookies = {}

        with pytest.raises(HTTPException) as exc_info:
            await middleware(request, credentials=None)

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_call_with_bearer_credentials(self, create_test_token):
        """Test middleware with Bearer token credentials"""
        middleware = AuthMiddleware()

        request = Mock(spec=Request)
        request.url.path = "/api/protected"
        request.state = Mock()

        token = create_test_token()
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with patch.object(middleware, "verify_token_local") as mock_local:
            mock_local.return_value = {
                "valid": True,
                "username": "test_user",
                "tenant_id": "test_tenant",
                "roles": ["user"],
            }

            result = await middleware(request, credentials=credentials)

            assert result is not None
            assert result["valid"] is True
            assert request.state.user is not None
            assert request.state.tenant_id == "test_tenant"

    @pytest.mark.asyncio
    async def test_call_with_cookie(self):
        """Test middleware with token in cookie"""
        middleware = AuthMiddleware()

        request = Mock(spec=Request)
        request.url.path = "/api/protected"
        request.cookies = {"access_token": "cookie-token"}
        request.state = Mock()

        with patch.object(middleware, "verify_token_local") as mock_local:
            mock_local.return_value = {
                "valid": True,
                "username": "test_user",
                "tenant_id": "test_tenant",
                "roles": ["user"],
            }

            result = await middleware(request, credentials=None)

            assert result is not None
            assert mock_local.called

    @pytest.mark.asyncio
    async def test_call_local_verification_fallback_to_remote(self, create_test_token):
        """Test middleware falls back to remote verification"""
        middleware = AuthMiddleware()

        request = Mock(spec=Request)
        request.url.path = "/api/protected"
        request.state = Mock()

        token = create_test_token()
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with patch.object(middleware, "verify_token_local") as mock_local:
            with patch.object(middleware, "verify_token_remote") as mock_remote:
                mock_local.return_value = None  # Local fails
                mock_remote.return_value = {
                    "valid": True,
                    "username": "test_user",
                    "tenant_id": "test_tenant",
                    "roles": ["user"],
                }

                result = await middleware(request, credentials=credentials)

                assert result is not None
                assert mock_local.called
                assert mock_remote.called

    @pytest.mark.asyncio
    async def test_call_invalid_token(self, create_test_token):
        """Test middleware raises 401 for invalid token"""
        middleware = AuthMiddleware()

        request = Mock(spec=Request)
        request.url.path = "/api/protected"

        token = create_test_token()
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with patch.object(middleware, "verify_token_local") as mock_local:
            with patch.object(middleware, "verify_token_remote") as mock_remote:
                mock_local.return_value = None
                mock_remote.return_value = {"valid": False}

                with pytest.raises(HTTPException) as exc_info:
                    await middleware(request, credentials=credentials)

                assert exc_info.value.status_code == 401


@pytest.mark.unit
@pytest.mark.auth
class TestGetCurrentUser:
    """Test get_current_user dependency"""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test get_current_user with valid credentials"""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

        with patch("app.middleware.auth.auth_middleware") as mock_middleware:
            mock_middleware.verify_token_remote = AsyncMock(
                return_value={"valid": True, "username": "test_user", "tenant_id": "test_tenant"}
            )

            result = await get_current_user(credentials)

            assert result is not None
            assert result["username"] == "test_user"

    @pytest.mark.asyncio
    async def test_get_current_user_no_credentials(self):
        """Test get_current_user raises 401 without credentials"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(None)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user raises 401 for invalid token"""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")

        with patch("app.middleware.auth.auth_middleware") as mock_middleware:
            mock_middleware.verify_token_remote = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)

            assert exc_info.value.status_code == 401


@pytest.mark.unit
@pytest.mark.auth
class TestRequireRole:
    """Test require_role dependency factory"""

    @pytest.mark.asyncio
    async def test_require_role_success(self):
        """Test require_role with user having required role"""
        role_checker = require_role("admin")

        user = {"username": "admin_user", "roles": ["admin", "user"]}

        result = await role_checker(user)

        assert result == user

    @pytest.mark.asyncio
    async def test_require_role_missing(self):
        """Test require_role raises 403 when role missing"""
        role_checker = require_role("admin")

        user = {"username": "regular_user", "roles": ["user"]}

        with pytest.raises(HTTPException) as exc_info:
            await role_checker(user)

        assert exc_info.value.status_code == 403
        assert "admin" in exc_info.value.detail


@pytest.mark.unit
@pytest.mark.auth
class TestRequireScope:
    """Test require_scope dependency factory"""

    @pytest.mark.asyncio
    async def test_require_scope_success(self):
        """Test require_scope with user having required scope"""
        scope_checker = require_scope("write")

        user = {"username": "test_user", "scopes": ["read", "write"]}

        result = await scope_checker(user)

        assert result == user

    @pytest.mark.asyncio
    async def test_require_scope_missing(self):
        """Test require_scope raises 403 when scope missing"""
        scope_checker = require_scope("admin")

        user = {"username": "test_user", "scopes": ["read", "write"]}

        with pytest.raises(HTTPException) as exc_info:
            await scope_checker(user)

        assert exc_info.value.status_code == 403
        assert "admin" in exc_info.value.detail
