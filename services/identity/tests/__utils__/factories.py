"""
Test data factories for Identity Service tests
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from jose import jwt


class TokenFactory:
    """Factory for creating test tokens"""

    @staticmethod
    def create_token(
        secret_key: str,
        username: str = "testuser",
        tenant_id: str = "test_tenant",
        roles: Optional[List[str]] = None,
        scopes: Optional[List[str]] = None,
        expires_delta: Optional[timedelta] = None,
        algorithm: str = "HS256",
        **extra_claims,
    ) -> str:
        """Create a JWT token for testing"""
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

        return jwt.encode(to_encode, secret_key, algorithm=algorithm)

    @staticmethod
    def create_expired_token(
        secret_key: str,
        username: str = "testuser",
        algorithm: str = "HS256",
    ) -> str:
        """Create an expired token for testing"""
        expire = datetime.utcnow() - timedelta(hours=1)
        to_encode = {
            "sub": username,
            "tenant_id": "test_tenant",
            "roles": ["user"],
            "scopes": ["read"],
            "exp": expire,
            "iat": datetime.utcnow() - timedelta(hours=2),
            "iss": "cortx-identity",
        }

        return jwt.encode(to_encode, secret_key, algorithm=algorithm)


class UserFactory:
    """Factory for creating test user data"""

    @staticmethod
    def create_user(
        username: str = "testuser",
        tenant_id: str = "test_tenant",
        roles: Optional[List[str]] = None,
        scopes: Optional[List[str]] = None,
        email: Optional[str] = None,
    ) -> Dict:
        """Create test user data"""
        if roles is None:
            roles = ["user"]
        if scopes is None:
            scopes = ["read"]
        if email is None:
            email = f"{username}@test.local"

        return {
            "username": username,
            "tenant_id": tenant_id,
            "roles": roles,
            "scopes": scopes,
            "email": email,
        }

    @staticmethod
    def create_admin_user(
        username: str = "admin",
        tenant_id: str = "default",
    ) -> Dict:
        """Create test admin user data"""
        return {
            "username": username,
            "tenant_id": tenant_id,
            "roles": ["admin", "user"],
            "scopes": ["read", "write", "admin"],
            "email": f"{username}@test.local",
        }

    @staticmethod
    def create_credentials(
        username: str = "testuser",
        password: str = "testpass123",
        tenant_id: str = "test_tenant",
    ) -> Dict:
        """Create test credentials"""
        return {
            "username": username,
            "password": password,
            "tenant_id": tenant_id,
        }


class TenantFactory:
    """Factory for creating test tenant data"""

    @staticmethod
    def create_tenant(
        tenant_id: str = "test_tenant",
        name: str = "Test Tenant",
    ) -> Dict:
        """Create test tenant data"""
        return {
            "id": tenant_id,
            "name": name,
        }

    @staticmethod
    def create_tenants(count: int = 3) -> List[Dict]:
        """Create multiple test tenants"""
        return [
            TenantFactory.create_tenant(
                tenant_id=f"tenant_{i}",
                name=f"Tenant {i}",
            )
            for i in range(1, count + 1)
        ]


class RoleFactory:
    """Factory for creating test role data"""

    @staticmethod
    def create_role(
        role_name: str = "test_role",
        scopes: Optional[List[str]] = None,
    ) -> Dict:
        """Create test role data"""
        if scopes is None:
            scopes = ["read"]

        return {
            "name": role_name,
            "scopes": scopes,
        }

    @staticmethod
    def create_roles(count: int = 3) -> List[Dict]:
        """Create multiple test roles"""
        return [
            RoleFactory.create_role(
                role_name=f"role_{i}",
                scopes=["read"] if i == 1 else ["read", "write"],
            )
            for i in range(1, count + 1)
        ]


# Predefined test data
TEST_USERS = {
    "admin": UserFactory.create_admin_user(),
    "user": UserFactory.create_user(username="user"),
    "reader": UserFactory.create_user(
        username="reader",
        roles=["user"],
        scopes=["read"],
    ),
    "writer": UserFactory.create_user(
        username="writer",
        roles=["user"],
        scopes=["read", "write"],
    ),
}

TEST_TENANTS = {
    "default": TenantFactory.create_tenant("default", "Default Tenant"),
    "test": TenantFactory.create_tenant("test_tenant", "Test Tenant"),
    "demo": TenantFactory.create_tenant("demo", "Demo Tenant"),
}

TEST_ROLES = {
    "admin": RoleFactory.create_role("admin", ["read", "write", "admin"]),
    "user": RoleFactory.create_role("user", ["read", "write"]),
    "viewer": RoleFactory.create_role("viewer", ["read"]),
}
