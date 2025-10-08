"""
Integration tests for authentication endpoints
"""



class TestLoginEndpoints:
    """Test login and authentication endpoints"""

    def test_login_endpoint_success(self, client):
        """Test successful login with valid credentials"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "admin",
                "password": "admin123",
                "tenant_id": "default",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)
        assert len(data["access_token"]) > 0

    def test_login_endpoint_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "admin",
                "password": "wrongpassword",
                "tenant_id": "default",
            },
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_endpoint_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "password",
                "tenant_id": "default",
            },
        )

        assert response.status_code == 401

    def test_login_endpoint_missing_password(self, client):
        """Test login with missing password"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "admin",
                "tenant_id": "default",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_login_endpoint_missing_username(self, client):
        """Test login with missing username"""
        response = client.post(
            "/v1/auth/login",
            json={
                "password": "admin123",
                "tenant_id": "default",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_login_endpoint_empty_username(self, client):
        """Test login with empty username"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "",
                "password": "admin123",
                "tenant_id": "default",
            },
        )

        assert response.status_code == 401

    def test_login_endpoint_empty_password(self, client):
        """Test login with empty password"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "admin",
                "password": "",
                "tenant_id": "default",
            },
        )

        assert response.status_code == 401

    def test_login_endpoint_regular_user(self, client):
        """Test login with regular user credentials"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "user",
                "password": "user123",
                "tenant_id": "default",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_endpoint_without_tenant_id(self, client):
        """Test login without specifying tenant_id (should use default)"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "admin",
                "password": "admin123",
            },
        )

        assert response.status_code == 200

    def test_login_endpoint_case_sensitive_username(self, client):
        """Test that username is case sensitive"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "Admin",  # Wrong case
                "password": "admin123",
                "tenant_id": "default",
            },
        )

        assert response.status_code == 401


class TestOAuth2TokenEndpoint:
    """Test OAuth2 compatible token endpoint"""

    def test_token_endpoint_success(self, client):
        """Test OAuth2 token endpoint with valid credentials"""
        response = client.post(
            "/v1/auth/token",
            data={
                "username": "admin",
                "password": "admin123",
                "grant_type": "password",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"

    def test_token_endpoint_invalid_credentials(self, client):
        """Test OAuth2 token endpoint with invalid credentials"""
        response = client.post(
            "/v1/auth/token",
            data={
                "username": "admin",
                "password": "wrongpassword",
                "grant_type": "password",
            },
        )

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_token_endpoint_form_data(self, client):
        """Test that OAuth2 endpoint accepts form data"""
        # OAuth2 requires form data, not JSON
        response = client.post(
            "/v1/auth/token",
            data={
                "username": "admin",
                "password": "admin123",
            },
        )

        assert response.status_code == 200

    def test_token_endpoint_json_not_accepted(self, client):
        """Test that OAuth2 endpoint doesn't accept JSON"""
        response = client.post(
            "/v1/auth/token",
            json={
                "username": "admin",
                "password": "admin123",
            },
        )

        # Should fail because OAuth2 expects form data
        assert response.status_code == 422


class TestTokenVerificationEndpoint:
    """Test token verification endpoint"""

    def test_verify_endpoint_valid_token(self, client, auth_headers):
        """Test verify endpoint with valid token"""
        headers = auth_headers(username="testuser", tenant_id="test_tenant")

        response = client.get("/v1/auth/verify", headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert data["username"] == "testuser"
        assert data["tenant_id"] == "test_tenant"
        assert "roles" in data
        assert "scopes" in data

    def test_verify_endpoint_no_token(self, client):
        """Test verify endpoint without token"""
        response = client.get("/v1/auth/verify")

        assert response.status_code == 403  # Forbidden without credentials

    def test_verify_endpoint_invalid_token(self, client):
        """Test verify endpoint with invalid token"""
        response = client.get(
            "/v1/auth/verify",
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == 401

    def test_verify_endpoint_expired_token(self, client, expired_token):
        """Test verify endpoint with expired token"""
        response = client.get(
            "/v1/auth/verify",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401

    def test_verify_endpoint_malformed_authorization_header(self, client):
        """Test verify endpoint with malformed authorization header"""
        response = client.get(
            "/v1/auth/verify",
            headers={"Authorization": "InvalidFormat token"},
        )

        assert response.status_code == 403

    def test_verify_endpoint_missing_bearer_prefix(self, client, create_test_token):
        """Test verify endpoint without Bearer prefix"""
        token = create_test_token(username="testuser")

        response = client.get(
            "/v1/auth/verify",
            headers={"Authorization": token},  # Missing "Bearer " prefix
        )

        assert response.status_code == 403

    def test_verify_endpoint_returns_user_data(self, client, auth_headers):
        """Test that verify endpoint returns correct user data"""
        headers = auth_headers(
            username="admin",
            tenant_id="default",
            roles=["admin", "user"],
            scopes=["read", "write", "admin"],
        )

        response = client.get("/v1/auth/verify", headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert data["username"] == "admin"
        assert data["tenant_id"] == "default"
        assert "admin" in data["roles"]
        assert "admin" in data["scopes"]


class TestGetMeEndpoint:
    """Test /v1/me endpoint for getting current user info"""

    def test_get_me_success(self, client, auth_headers):
        """Test getting current user info"""
        headers = auth_headers(username="testuser", tenant_id="test_tenant")

        response = client.get("/v1/me", headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert data["username"] == "testuser"
        assert data["tenant_id"] == "test_tenant"
        assert "roles" in data
        assert "scopes" in data

    def test_get_me_without_auth(self, client):
        """Test /v1/me without authentication"""
        response = client.get("/v1/me")

        assert response.status_code == 403

    def test_get_me_with_admin_user(self, client, admin_auth_headers):
        """Test /v1/me with admin user"""
        response = client.get("/v1/me", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["username"] == "admin"
        assert "admin" in data["roles"]

    def test_get_me_includes_all_user_fields(self, client, auth_headers):
        """Test that /v1/me returns all user fields"""
        headers = auth_headers(
            username="fulluser",
            tenant_id="tenant1",
            roles=["user", "admin"],
            scopes=["read", "write"],
        )

        response = client.get("/v1/me", headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert "username" in data
        assert "tenant_id" in data
        assert "roles" in data
        assert "scopes" in data
        # email is optional
        assert "email" in data or data.get("email") is None


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "identity"

    def test_health_endpoint_no_auth_required(self, client):
        """Test that health endpoint doesn't require authentication"""
        response = client.get("/health")

        assert response.status_code == 200


class TestServiceInfoEndpoint:
    """Test service information endpoint"""

    def test_service_info_endpoint(self, client):
        """Test service info endpoint"""
        response = client.get("/docs/info")

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "identity"
        assert "version" in data
        assert "capabilities" in data
        assert "endpoints" in data

    def test_service_info_includes_capabilities(self, client):
        """Test that service info includes capabilities"""
        response = client.get("/docs/info")

        assert response.status_code == 200
        data = response.json()

        assert "user_authentication" in data["capabilities"]
        assert "jwt_token_management" in data["capabilities"]
        assert "role_based_access_control" in data["capabilities"]


class TestAuthenticationSecurity:
    """Test security aspects of authentication"""

    def test_multiple_failed_login_attempts(self, client):
        """Test multiple failed login attempts"""
        for _ in range(5):
            response = client.post(
                "/v1/auth/login",
                json={
                    "username": "admin",
                    "password": "wrongpassword",
                    "tenant_id": "default",
                },
            )
            assert response.status_code == 401

    def test_login_does_not_leak_user_existence(self, client):
        """Test that login error messages don't leak user existence"""
        # Try with existing user, wrong password
        response1 = client.post(
            "/v1/auth/login",
            json={
                "username": "admin",
                "password": "wrongpassword",
            },
        )

        # Try with non-existing user
        response2 = client.post(
            "/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "password",
            },
        )

        # Both should return same error message
        assert response1.status_code == response2.status_code
        assert response1.json()["detail"] == response2.json()["detail"]

    def test_token_cannot_be_reused_across_endpoints(self, client, create_test_token):
        """Test that token works across different endpoints"""
        token = create_test_token(username="testuser")
        headers = {"Authorization": f"Bearer {token}"}

        # Token should work on verify endpoint
        response1 = client.get("/v1/auth/verify", headers=headers)
        assert response1.status_code == 200

        # Token should work on /v1/me endpoint
        response2 = client.get("/v1/me", headers=headers)
        assert response2.status_code == 200

    def test_sql_injection_in_login(self, client):
        """Test SQL injection attempt in login"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "admin' OR '1'='1",
                "password": "anything",
            },
        )

        assert response.status_code == 401

    def test_xss_in_username(self, client):
        """Test XSS attempt in username"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "<script>alert('xss')</script>",
                "password": "password",
            },
        )

        assert response.status_code == 401
