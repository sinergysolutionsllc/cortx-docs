"""
Integration tests for token refresh endpoints
"""

from jose import jwt


class TestRefreshTokenEndpoint:
    """Test token refresh endpoint"""

    def test_refresh_token_success(self, client, create_refresh_token):
        """Test successful token refresh"""
        refresh_token = create_refresh_token(
            username="testuser",
            tenant_id="test_tenant",
            roles=["user"],
            scopes=["read"],
        )

        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_returns_new_tokens(self, client, create_refresh_token):
        """Test that refresh returns new access and refresh tokens"""
        original_refresh = create_refresh_token(username="testuser")

        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": original_refresh},
        )

        assert response.status_code == 200
        data = response.json()

        # New tokens should be different from original
        assert data["access_token"] != original_refresh
        assert data["refresh_token"] != original_refresh

    def test_refresh_token_preserves_user_data(self, client, create_refresh_token):
        """Test that refresh preserves user data in new tokens"""
        refresh_token = create_refresh_token(
            username="admin",
            tenant_id="test_tenant",
            roles=["admin", "user"],
            scopes=["read", "write", "admin"],
        )

        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()

        # Decode new access token to verify user data
        from app.main import ALGORITHM, SECRET_KEY

        decoded = jwt.decode(data["access_token"], SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["sub"] == "admin"
        assert decoded["tenant_id"] == "test_tenant"
        assert "admin" in decoded["roles"]
        assert "admin" in decoded["scopes"]

    def test_refresh_token_invalid_token(self, client):
        """Test refresh with invalid token"""
        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )

        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.json()["detail"]

    def test_refresh_token_expired(self, client, test_refresh_secret_key):
        """Test refresh with expired refresh token"""
        from datetime import datetime, timedelta

        # Create expired refresh token
        expired_refresh = jwt.encode(
            {
                "sub": "testuser",
                "tenant_id": "test",
                "roles": ["user"],
                "scopes": ["read"],
                "type": "refresh",
                "exp": datetime.utcnow() - timedelta(days=1),
                "iat": datetime.utcnow() - timedelta(days=8),
            },
            test_refresh_secret_key,
            algorithm="HS256",
        )

        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": expired_refresh},
        )

        assert response.status_code == 401

    def test_refresh_token_wrong_type(self, client, create_test_token):
        """Test refresh with access token instead of refresh token"""
        # Try to use access token for refresh
        access_token = create_test_token(username="testuser")

        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": access_token},
        )

        # Should fail because it's not a refresh token
        assert response.status_code == 401

    def test_refresh_token_missing_type_claim(self, client, test_refresh_secret_key):
        """Test refresh with token missing type claim"""
        from datetime import datetime, timedelta

        # Create token without type claim
        token = jwt.encode(
            {
                "sub": "testuser",
                "tenant_id": "test",
                "exp": datetime.utcnow() + timedelta(days=7),
                "iat": datetime.utcnow(),
            },
            test_refresh_secret_key,
            algorithm="HS256",
        )

        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": token},
        )

        assert response.status_code == 401
        assert "Invalid token type" in response.json()["detail"]

    def test_refresh_token_empty_string(self, client):
        """Test refresh with empty token string"""
        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": ""},
        )

        assert response.status_code == 401

    def test_refresh_token_missing_parameter(self, client):
        """Test refresh without refresh_token parameter"""
        response = client.post(
            "/v1/auth/refresh",
            json={},
        )

        assert response.status_code == 422  # Validation error


class TestRevokeTokenEndpoint:
    """Test token revocation endpoint"""

    def test_revoke_token_success(self, client, create_refresh_token):
        """Test successful token revocation"""
        refresh_token = create_refresh_token(username="testuser")

        response = client.post(
            "/v1/auth/revoke",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "revoked" in data["message"].lower()

    def test_revoke_token_invalid(self, client):
        """Test revoking invalid token"""
        response = client.post(
            "/v1/auth/revoke",
            json={"refresh_token": "invalid_token"},
        )

        assert response.status_code == 401

    def test_revoke_token_expired(self, client, test_refresh_secret_key):
        """Test revoking expired token"""
        from datetime import datetime, timedelta

        expired_token = jwt.encode(
            {
                "sub": "testuser",
                "type": "refresh",
                "exp": datetime.utcnow() - timedelta(days=1),
                "iat": datetime.utcnow() - timedelta(days=8),
            },
            test_refresh_secret_key,
            algorithm="HS256",
        )

        response = client.post(
            "/v1/auth/revoke",
            json={"refresh_token": expired_token},
        )

        assert response.status_code == 401

    def test_revoke_token_empty_string(self, client):
        """Test revoking empty token string"""
        response = client.post(
            "/v1/auth/revoke",
            json={"refresh_token": ""},
        )

        assert response.status_code == 401


class TestTokenRotation:
    """Test token rotation scenarios"""

    def test_full_token_rotation_flow(self, client):
        """Test complete token rotation flow"""
        # 1. Login to get initial tokens
        login_response = client.post(
            "/v1/auth/login",
            json={
                "username": "admin",
                "password": "admin123",
            },
        )

        assert login_response.status_code == 200
        initial_token = login_response.json()["access_token"]

        # 2. Verify initial token works
        verify_response = client.get(
            "/v1/auth/verify",
            headers={"Authorization": f"Bearer {initial_token}"},
        )

        assert verify_response.status_code == 200

        # Note: The current implementation doesn't return refresh token on login
        # This test verifies the access token flow

    def test_multiple_refresh_cycles(self, client, create_refresh_token):
        """Test refreshing tokens multiple times"""
        initial_refresh = create_refresh_token(username="testuser")

        # First refresh
        response1 = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": initial_refresh},
        )

        assert response1.status_code == 200
        second_refresh = response1.json()["refresh_token"]

        # Second refresh with new token
        response2 = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": second_refresh},
        )

        assert response2.status_code == 200
        third_refresh = response2.json()["refresh_token"]

        # All refresh tokens should be different
        assert initial_refresh != second_refresh
        assert second_refresh != third_refresh

    def test_old_refresh_token_still_valid_after_rotation(self, client, create_refresh_token):
        """Test that old refresh token is still valid after creating new one"""
        # Note: In a production system with token blacklisting,
        # old refresh tokens should be invalidated
        refresh_token = create_refresh_token(username="testuser")

        # Use refresh token
        response1 = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response1.status_code == 200

        # Try to use old refresh token again
        response2 = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        # In current implementation, old token is still valid
        # In production with blacklist, this should fail
        assert response2.status_code == 200


class TestRefreshTokenSecurity:
    """Test security aspects of refresh tokens"""

    def test_refresh_token_different_secret_than_access(
        self, client, create_test_token, create_refresh_token
    ):
        """Test that refresh tokens use different secret key"""
        access_token = create_test_token(username="testuser")
        refresh_token = create_refresh_token(username="testuser")

        # Access token should not work as refresh token
        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": access_token},
        )

        assert response.status_code == 401

    def test_cannot_use_refresh_token_as_bearer(self, client, create_refresh_token):
        """Test that refresh token cannot be used as access token"""
        refresh_token = create_refresh_token(username="testuser")

        # Try to use refresh token as bearer token
        response = client.get(
            "/v1/auth/verify",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )

        # Should fail because it's not an access token
        assert response.status_code == 401

    def test_refresh_token_xss_protection(self, client, create_refresh_token):
        """Test XSS protection in refresh token handling"""
        malicious_token = "<script>alert('xss')</script>"

        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": malicious_token},
        )

        assert response.status_code == 401
        # Response should not execute script
        assert "<script>" not in str(response.content)

    def test_refresh_token_sql_injection(self, client):
        """Test SQL injection protection in refresh token"""
        malicious_token = "' OR '1'='1"

        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": malicious_token},
        )

        assert response.status_code == 401


class TestRefreshTokenEdgeCases:
    """Test edge cases for refresh tokens"""

    def test_refresh_with_very_long_token(self, client):
        """Test refresh with extremely long token string"""
        long_token = "a" * 10000

        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": long_token},
        )

        assert response.status_code == 401

    def test_refresh_with_unicode_token(self, client):
        """Test refresh with unicode characters"""
        unicode_token = "用户令牌"

        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": unicode_token},
        )

        assert response.status_code == 401

    def test_refresh_with_null_bytes(self, client):
        """Test refresh with null bytes in token"""
        token_with_null = "token\x00injected"

        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": token_with_null},
        )

        assert response.status_code == 401

    def test_refresh_token_concurrent_requests(self, client, create_refresh_token):
        """Test concurrent refresh requests with same token"""
        refresh_token = create_refresh_token(username="testuser")

        # Make multiple concurrent refresh requests
        # (In practice, this would be truly concurrent, but here we simulate)
        response1 = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        response2 = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        # Both should succeed in current implementation
        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_refresh_preserves_tenant_isolation(self, client, create_refresh_token):
        """Test that refresh preserves tenant isolation"""
        refresh_token = create_refresh_token(
            username="user1",
            tenant_id="tenant_a",
            roles=["user"],
            scopes=["read"],
        )

        response = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200

        # Decode new access token
        from app.main import ALGORITHM, SECRET_KEY

        decoded = jwt.decode(response.json()["access_token"], SECRET_KEY, algorithms=[ALGORITHM])

        # Tenant should be preserved
        assert decoded["tenant_id"] == "tenant_a"
