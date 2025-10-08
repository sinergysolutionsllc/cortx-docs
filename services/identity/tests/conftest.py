"""
pytest configuration and fixtures for Identity Service tests
"""

import os
from datetime import datetime, timedelta
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from jose import jwt

# Set test environment variables before importing app
os.environ["JWT_SECRET_KEY"] = "test_secret_key_for_testing_only"
os.environ["JWT_REFRESH_SECRET_KEY"] = "test_refresh_secret_key_for_testing_only"

from app.main import ALGORITHM, app  # noqa: E402


@pytest.fixture(scope="session")
def test_secret_key() -> str:
    """Return test JWT secret key"""
    return "test_secret_key_for_testing_only"


@pytest.fixture(scope="session")
def test_refresh_secret_key() -> str:
    """Return test refresh secret key"""
    return "test_refresh_secret_key_for_testing_only"


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_user_data() -> Dict:
    """Mock user data for testing"""
    return {
        "username": "testuser",
        "password": "testpass123",
        "tenant_id": "test_tenant",
        "roles": ["user"],
        "scopes": ["read", "write"],
        "email": "testuser@cortx.local",
    }


@pytest.fixture
def mock_admin_data() -> Dict:
    """Mock admin user data for testing"""
    return {
        "username": "admin",
        "password": "admin123",
        "tenant_id": "default",
        "roles": ["admin", "user"],
        "scopes": ["read", "write", "admin"],
        "email": "admin@cortx.local",
    }


@pytest.fixture
def create_test_token(test_secret_key: str):
    """Factory fixture to create test JWT tokens"""

    def _create_token(
        username: str = "testuser",
        tenant_id: str = "test_tenant",
        roles: list = None,
        scopes: list = None,
        expires_delta: timedelta = None,
        **extra_claims,
    ) -> str:
        """Create a test JWT token with custom claims"""
        if roles is None:
            roles = ["user"]
        if scopes is None:
            scopes = ["read"]

        if expires_delta is None:
            expires_delta = timedelta(hours=1)

        expire = datetime.utcnow() + expires_delta
        to_encode = {
            "sub": username,
            "tenant_id": tenant_id,
            "roles": roles,
            "scopes": scopes,
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": "cortx-identity",
            **extra_claims,
        }

        return jwt.encode(to_encode, test_secret_key, algorithm=ALGORITHM)

    return _create_token


@pytest.fixture
def create_refresh_token(test_refresh_secret_key: str):
    """Factory fixture to create test refresh tokens"""

    def _create_refresh_token(
        username: str = "testuser",
        tenant_id: str = "test_tenant",
        roles: list = None,
        scopes: list = None,
        expires_delta: timedelta = None,
    ) -> str:
        """Create a test refresh token"""
        if roles is None:
            roles = ["user"]
        if scopes is None:
            scopes = ["read"]

        if expires_delta is None:
            expires_delta = timedelta(days=7)

        expire = datetime.utcnow() + expires_delta
        to_encode = {
            "sub": username,
            "tenant_id": tenant_id,
            "roles": roles,
            "scopes": scopes,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
        }

        return jwt.encode(to_encode, test_refresh_secret_key, algorithm="HS256")

    return _create_refresh_token


@pytest.fixture
def auth_headers(create_test_token):
    """Generate authentication headers with valid token"""

    def _auth_headers(
        username: str = "testuser",
        tenant_id: str = "test_tenant",
        roles: list = None,
        scopes: list = None,
    ) -> Dict[str, str]:
        """Create auth headers with Bearer token"""
        token = create_test_token(
            username=username, tenant_id=tenant_id, roles=roles, scopes=scopes
        )
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers


@pytest.fixture
def admin_auth_headers(create_test_token):
    """Generate admin authentication headers"""
    token = create_test_token(
        username="admin",
        tenant_id="default",
        roles=["admin", "user"],
        scopes=["read", "write", "admin"],
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def expired_token(test_secret_key: str) -> str:
    """Create an expired JWT token for testing"""
    expire = datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
    to_encode = {
        "sub": "testuser",
        "tenant_id": "test_tenant",
        "roles": ["user"],
        "scopes": ["read"],
        "exp": expire,
        "iat": datetime.utcnow() - timedelta(hours=2),
        "iss": "cortx-identity",
    }
    return jwt.encode(to_encode, test_secret_key, algorithm=ALGORITHM)


@pytest.fixture
def invalid_token() -> str:
    """Return an invalid JWT token for testing"""
    return "invalid.jwt.token"


@pytest.fixture
def malformed_token() -> str:
    """Return a malformed JWT token for testing"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.malformed"


@pytest.fixture
def mock_users():
    """Mock user database for testing"""
    return {
        "testuser": {
            "password_hash": "hashed_password",
            "tenant_id": "test_tenant",
            "roles": ["user"],
            "scopes": ["read", "write"],
            "email": "testuser@cortx.local",
        },
        "admin": {
            "password_hash": "hashed_admin_password",
            "tenant_id": "default",
            "roles": ["admin", "user"],
            "scopes": ["read", "write", "admin"],
            "email": "admin@cortx.local",
        },
    }


@pytest.fixture
def different_tenant_token(create_test_token):
    """Create token for a different tenant (for isolation tests)"""
    return create_test_token(
        username="otheruser",
        tenant_id="other_tenant",
        roles=["user"],
        scopes=["read"],
    )


# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)
