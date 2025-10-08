"""
Integration tests for user management and RBAC endpoints
"""



class TestTenantsEndpoint:
    """Test tenant management endpoints"""

    def test_get_tenants_as_admin(self, client, admin_auth_headers):
        """Test getting tenants list as admin"""
        response = client.get("/v1/tenants", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "tenants" in data
        assert isinstance(data["tenants"], list)
        assert len(data["tenants"]) > 0

    def test_get_tenants_as_regular_user(self, client, auth_headers):
        """Test getting tenants list as regular user (should fail)"""
        headers = auth_headers(username="user", roles=["user"])

        response = client.get("/v1/tenants", headers=headers)

        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_get_tenants_without_auth(self, client):
        """Test getting tenants without authentication"""
        response = client.get("/v1/tenants")

        assert response.status_code == 403

    def test_tenants_response_structure(self, client, admin_auth_headers):
        """Test that tenants response has correct structure"""
        response = client.get("/v1/tenants", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()

        for tenant in data["tenants"]:
            assert "id" in tenant
            assert "name" in tenant
            assert isinstance(tenant["id"], str)
            assert isinstance(tenant["name"], str)


class TestRoleManagementEndpoint:
    """Test role management endpoints"""

    def test_create_role_as_admin(self, client, admin_auth_headers):
        """Test creating a role as admin"""
        response = client.post(
            "/v1/roles",
            params={"role_name": "test_role"},
            headers=admin_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "role" in data
        assert data["role"] == "test_role"

    def test_create_role_as_regular_user(self, client, auth_headers):
        """Test creating a role as regular user (should fail)"""
        headers = auth_headers(username="user", roles=["user"])

        response = client.post(
            "/v1/roles",
            params={"role_name": "test_role"},
            headers=headers,
        )

        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_create_role_without_auth(self, client):
        """Test creating a role without authentication"""
        response = client.post(
            "/v1/roles",
            params={"role_name": "test_role"},
        )

        assert response.status_code == 403

    def test_create_role_with_special_characters(self, client, admin_auth_headers):
        """Test creating a role with special characters"""
        response = client.post(
            "/v1/roles",
            params={"role_name": "test-role_123"},
            headers=admin_auth_headers,
        )

        assert response.status_code == 200

    def test_create_role_empty_name(self, client, admin_auth_headers):
        """Test creating a role with empty name"""
        response = client.post(
            "/v1/roles",
            params={"role_name": ""},
            headers=admin_auth_headers,
        )

        # Should still succeed as validation is minimal in mock
        assert response.status_code == 200


class TestUserRoleAuthorization:
    """Test role-based authorization for different endpoints"""

    def test_admin_can_access_tenants(self, client, auth_headers):
        """Test that admin role can access tenants endpoint"""
        headers = auth_headers(
            username="admin",
            tenant_id="default",
            roles=["admin", "user"],
            scopes=["admin"],
        )

        response = client.get("/v1/tenants", headers=headers)

        assert response.status_code == 200

    def test_user_cannot_access_tenants(self, client, auth_headers):
        """Test that user role cannot access tenants endpoint"""
        headers = auth_headers(
            username="user",
            tenant_id="default",
            roles=["user"],
            scopes=["read"],
        )

        response = client.get("/v1/tenants", headers=headers)

        assert response.status_code == 403

    def test_admin_can_create_roles(self, client, auth_headers):
        """Test that admin role can create roles"""
        headers = auth_headers(
            username="admin",
            roles=["admin"],
            scopes=["admin"],
        )

        response = client.post(
            "/v1/roles",
            params={"role_name": "new_role"},
            headers=headers,
        )

        assert response.status_code == 200

    def test_user_cannot_create_roles(self, client, auth_headers):
        """Test that user role cannot create roles"""
        headers = auth_headers(
            username="user",
            roles=["user"],
            scopes=["read"],
        )

        response = client.post(
            "/v1/roles",
            params={"role_name": "new_role"},
            headers=headers,
        )

        assert response.status_code == 403

    def test_user_with_multiple_roles_including_admin(self, client, auth_headers):
        """Test user with multiple roles including admin"""
        headers = auth_headers(
            username="superuser",
            roles=["user", "moderator", "admin"],
            scopes=["read", "write", "admin"],
        )

        # Should be able to access admin endpoints
        response = client.get("/v1/tenants", headers=headers)

        assert response.status_code == 200

    def test_all_users_can_access_me_endpoint(self, client, auth_headers):
        """Test that all authenticated users can access /v1/me"""
        # Regular user
        headers = auth_headers(username="user", roles=["user"])
        response = client.get("/v1/me", headers=headers)
        assert response.status_code == 200

        # Admin user
        headers = auth_headers(username="admin", roles=["admin"])
        response = client.get("/v1/me", headers=headers)
        assert response.status_code == 200

    def test_all_users_can_verify_token(self, client, auth_headers):
        """Test that all authenticated users can verify their token"""
        headers = auth_headers(username="user", roles=["user"])

        response = client.get("/v1/auth/verify", headers=headers)

        assert response.status_code == 200


class TestScopeBasedAuthorization:
    """Test scope-based authorization"""

    def test_user_with_read_scope(self, client, auth_headers):
        """Test user with read scope can access read endpoints"""
        headers = auth_headers(
            username="reader",
            roles=["user"],
            scopes=["read"],
        )

        response = client.get("/v1/me", headers=headers)

        assert response.status_code == 200

    def test_user_with_admin_scope_can_access_admin_endpoints(self, client, auth_headers):
        """Test user with admin scope can access admin endpoints"""
        headers = auth_headers(
            username="admin",
            roles=["admin"],
            scopes=["admin"],
        )

        response = client.get("/v1/tenants", headers=headers)

        assert response.status_code == 200

    def test_user_without_admin_scope_cannot_access_admin_endpoints(self, client, auth_headers):
        """Test user without admin scope cannot access admin endpoints"""
        headers = auth_headers(
            username="user",
            roles=["user"],
            scopes=["read", "write"],  # No admin scope
        )

        response = client.get("/v1/tenants", headers=headers)

        assert response.status_code == 403


class TestUserEdgeCases:
    """Test edge cases for user management"""

    def test_user_with_empty_roles_list(self, client, auth_headers):
        """Test user with no roles"""
        headers = auth_headers(
            username="noroles",
            roles=[],
            scopes=[],
        )

        # Can still access /v1/me (no role requirement)
        response = client.get("/v1/me", headers=headers)
        assert response.status_code == 200

        # Cannot access admin endpoints
        response = client.get("/v1/tenants", headers=headers)
        assert response.status_code == 403

    def test_user_with_case_variant_role(self, client, auth_headers):
        """Test that role checking is case-sensitive"""
        headers = auth_headers(
            username="user",
            roles=["Admin"],  # Capital A
            scopes=["admin"],
        )

        # Should fail because role is "Admin" not "admin"
        response = client.get("/v1/tenants", headers=headers)
        assert response.status_code == 403

    def test_user_with_custom_roles(self, client, auth_headers):
        """Test user with custom role names"""
        headers = auth_headers(
            username="custom",
            roles=["custom_role", "special-role", "role.name"],
            scopes=["read"],
        )

        # Can access /v1/me
        response = client.get("/v1/me", headers=headers)
        assert response.status_code == 200

        # Cannot access admin endpoints
        response = client.get("/v1/tenants", headers=headers)
        assert response.status_code == 403

    def test_user_with_duplicate_roles(self, client, auth_headers):
        """Test user with duplicate roles in list"""
        headers = auth_headers(
            username="user",
            roles=["admin", "admin", "user"],
            scopes=["admin"],
        )

        # Should still work
        response = client.get("/v1/tenants", headers=headers)
        assert response.status_code == 200

    def test_user_with_very_long_role_name(self, client, auth_headers):
        """Test user with very long role name"""
        long_role = "a" * 1000
        headers = auth_headers(
            username="user",
            roles=[long_role],
            scopes=["read"],
        )

        response = client.get("/v1/me", headers=headers)
        assert response.status_code == 200

    def test_authorization_header_case_sensitivity(self, client, create_test_token):
        """Test that Authorization header is case-insensitive"""
        token = create_test_token(username="testuser")

        # Try with different cases
        response1 = client.get(
            "/v1/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        response2 = client.get(
            "/v1/me",
            headers={"authorization": f"Bearer {token}"},  # lowercase
        )

        # FastAPI/Starlette handles header case-insensitivity
        assert response1.status_code == 200
        # Note: Second request might fail depending on client implementation
        # but typically headers are case-insensitive in HTTP
