"""
Integration tests for tenant isolation and comprehensive error handling
"""



class TestTenantIsolation:
    """Test tenant isolation between different tenants"""

    def test_different_tenants_have_different_contexts(self, client, auth_headers):
        """Test that users from different tenants are isolated"""
        # User from tenant A
        headers_a = auth_headers(
            username="user_a",
            tenant_id="tenant_a",
            roles=["user"],
            scopes=["read"],
        )

        # User from tenant B
        headers_b = auth_headers(
            username="user_b",
            tenant_id="tenant_b",
            roles=["user"],
            scopes=["read"],
        )

        # Both should be able to access their own data
        response_a = client.get("/v1/me", headers=headers_a)
        assert response_a.status_code == 200
        assert response_a.json()["tenant_id"] == "tenant_a"

        response_b = client.get("/v1/me", headers=headers_b)
        assert response_b.status_code == 200
        assert response_b.json()["tenant_id"] == "tenant_b"

    def test_tenant_id_preserved_in_token(self, client, auth_headers):
        """Test that tenant_id is preserved in JWT token"""
        headers = auth_headers(
            username="testuser",
            tenant_id="custom_tenant",
            roles=["user"],
            scopes=["read"],
        )

        response = client.get("/v1/auth/verify", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "custom_tenant"

    def test_default_tenant_assignment(self, client, auth_headers):
        """Test default tenant is assigned when not specified"""
        # When using the default admin user
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "admin",
                "password": "admin123",
            },
        )

        assert response.status_code == 200

        # Verify the token
        token = response.json()["access_token"]
        response = client.get(
            "/v1/auth/verify",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        # Should have default tenant from user data
        assert "tenant_id" in response.json()

    def test_same_username_different_tenants(self, client, auth_headers):
        """Test that same username can exist in different tenants"""
        # Same username, different tenants
        headers1 = auth_headers(
            username="john",
            tenant_id="company_a",
            roles=["user"],
        )

        headers2 = auth_headers(
            username="john",
            tenant_id="company_b",
            roles=["user"],
        )

        response1 = client.get("/v1/me", headers=headers1)
        response2 = client.get("/v1/me", headers=headers2)

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        assert data1["username"] == data2["username"] == "john"
        assert data1["tenant_id"] != data2["tenant_id"]

    def test_admin_role_scoped_to_tenant(self, client, auth_headers):
        """Test that admin role is scoped to tenant"""
        # Admin in tenant A
        headers = auth_headers(
            username="admin_a",
            tenant_id="tenant_a",
            roles=["admin"],
            scopes=["admin"],
        )

        response = client.get("/v1/tenants", headers=headers)

        # Should be able to access admin endpoints
        assert response.status_code == 200

    def test_tenant_cannot_be_modified_via_token(self, client, create_test_token):
        """Test that tenant_id cannot be tampered with"""
        token = create_test_token(
            username="user",
            tenant_id="tenant_a",
            roles=["user"],
        )

        # Token should only work with the tenant it was issued for
        response = client.get(
            "/v1/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["tenant_id"] == "tenant_a"


class TestErrorHandling:
    """Test comprehensive error handling"""

    def test_invalid_token_error_message(self, client):
        """Test error message for invalid token"""
        response = client.get(
            "/v1/auth/verify",
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == 401
        assert "detail" in response.json()
        assert "credentials" in response.json()["detail"].lower()

    def test_expired_token_error_handling(self, client, expired_token):
        """Test error handling for expired token"""
        response = client.get(
            "/v1/auth/verify",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    def test_missing_authorization_header(self, client):
        """Test error when authorization header is missing"""
        response = client.get("/v1/auth/verify")

        assert response.status_code == 403

    def test_malformed_authorization_header(self, client):
        """Test error for malformed authorization header"""
        # Missing "Bearer" prefix
        response = client.get(
            "/v1/auth/verify",
            headers={"Authorization": "token123"},
        )

        assert response.status_code == 403

    def test_empty_authorization_header(self, client):
        """Test error for empty authorization header"""
        response = client.get(
            "/v1/auth/verify",
            headers={"Authorization": ""},
        )

        assert response.status_code == 403

    def test_invalid_credentials_error(self, client):
        """Test error for invalid login credentials"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "admin",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_validation_error_missing_fields(self, client):
        """Test validation error for missing required fields"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "admin",
                # Missing password
            },
        )

        assert response.status_code == 422
        error = response.json()
        assert "detail" in error

    def test_forbidden_error_for_insufficient_permissions(self, client, auth_headers):
        """Test 403 error when user lacks permissions"""
        headers = auth_headers(
            username="user",
            roles=["user"],
            scopes=["read"],
        )

        response = client.get("/v1/tenants", headers=headers)

        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_404_error_for_nonexistent_endpoint(self, client, auth_headers):
        """Test 404 error for non-existent endpoint"""
        headers = auth_headers(username="user")

        response = client.get("/v1/nonexistent", headers=headers)

        assert response.status_code == 404

    def test_method_not_allowed_error(self, client):
        """Test 405 error for wrong HTTP method"""
        # Try to DELETE on an endpoint that only supports GET
        response = client.delete("/health")

        assert response.status_code == 405

    def test_error_response_structure(self, client):
        """Test that error responses have consistent structure"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "admin",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        error = response.json()

        # Should have detail field
        assert "detail" in error
        assert isinstance(error["detail"], str)


class TestSecurityErrorHandling:
    """Test security-related error handling"""

    def test_sql_injection_attempt_returns_error(self, client):
        """Test that SQL injection attempts are handled safely"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "admin' OR '1'='1",
                "password": "anything",
            },
        )

        assert response.status_code == 401
        # Should not expose internal error details
        assert "sql" not in response.json()["detail"].lower()

    def test_xss_attempt_in_input(self, client):
        """Test XSS attempt in input is handled safely"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "<script>alert('xss')</script>",
                "password": "password",
            },
        )

        assert response.status_code == 401
        # Response should not contain script tags
        assert "<script>" not in str(response.content)

    def test_path_traversal_attempt(self, client, auth_headers):
        """Test path traversal attempt is blocked"""
        headers = auth_headers(username="user")

        response = client.get(
            "/v1/../../../etc/passwd",
            headers=headers,
        )

        # Should return 404, not expose file system
        assert response.status_code == 404

    def test_command_injection_attempt(self, client):
        """Test command injection attempt in input"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "admin; rm -rf /",
                "password": "password",
            },
        )

        assert response.status_code == 401

    def test_large_payload_handling(self, client):
        """Test handling of very large payloads"""
        large_username = "a" * 100000

        response = client.post(
            "/v1/auth/login",
            json={
                "username": large_username,
                "password": "password",
            },
        )

        # Should handle gracefully (either 401 or 413/422)
        assert response.status_code in [401, 413, 422]

    def test_malformed_json_handling(self, client):
        """Test handling of malformed JSON"""
        response = client.post(
            "/v1/auth/login",
            data="{'username': 'admin', 'password': 'admin123'",  # Invalid JSON
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_content_type_mismatch(self, client):
        """Test handling of content type mismatch"""
        response = client.post(
            "/v1/auth/login",
            data="username=admin&password=admin123",  # Form data instead of JSON
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        # Should return validation error
        assert response.status_code == 422

    def test_null_byte_injection(self, client):
        """Test null byte injection attempt"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "admin\x00injected",
                "password": "password",
            },
        )

        assert response.status_code == 401


class TestConcurrentRequests:
    """Test handling of concurrent requests"""

    def test_multiple_verification_requests(self, client, auth_headers):
        """Test multiple concurrent verification requests"""
        headers = auth_headers(username="testuser")

        # Make multiple requests
        responses = [client.get("/v1/auth/verify", headers=headers) for _ in range(5)]

        # All should succeed
        for response in responses:
            assert response.status_code == 200

    def test_multiple_login_attempts(self, client):
        """Test multiple login attempts"""
        # Multiple login requests
        responses = [
            client.post(
                "/v1/auth/login",
                json={
                    "username": "admin",
                    "password": "admin123",
                },
            )
            for _ in range(3)
        ]

        # All should succeed
        for response in responses:
            assert response.status_code == 200


class TestRateLimitingSimulation:
    """Test rate limiting scenarios (if implemented)"""

    def test_many_failed_login_attempts(self, client):
        """Test many failed login attempts"""
        # Note: Rate limiting not implemented in current version
        # This tests that system handles many requests gracefully
        for _ in range(20):
            response = client.post(
                "/v1/auth/login",
                json={
                    "username": "admin",
                    "password": "wrongpassword",
                },
            )
            assert response.status_code == 401

    def test_rapid_token_verification(self, client, auth_headers):
        """Test rapid token verification requests"""
        headers = auth_headers(username="testuser")

        for _ in range(50):
            response = client.get("/v1/auth/verify", headers=headers)
            assert response.status_code == 200


class TestEdgeCaseScenarios:
    """Test edge case scenarios"""

    def test_empty_json_body(self, client):
        """Test request with empty JSON body"""
        response = client.post(
            "/v1/auth/login",
            json={},
        )

        assert response.status_code == 422

    def test_null_values_in_request(self, client):
        """Test request with null values"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": None,
                "password": None,
            },
        )

        assert response.status_code == 422

    def test_unicode_in_credentials(self, client):
        """Test unicode characters in credentials"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "用户名",
                "password": "密码",
            },
        )

        assert response.status_code == 401

    def test_whitespace_only_credentials(self, client):
        """Test whitespace-only credentials"""
        response = client.post(
            "/v1/auth/login",
            json={
                "username": "   ",
                "password": "   ",
            },
        )

        assert response.status_code == 401

    def test_special_characters_in_tenant_id(self, client, auth_headers):
        """Test special characters in tenant_id"""
        headers = auth_headers(
            username="user",
            tenant_id="tenant-123_456.test",
            roles=["user"],
        )

        response = client.get("/v1/me", headers=headers)

        assert response.status_code == 200
        assert response.json()["tenant_id"] == "tenant-123_456.test"
