"""
Unit tests for user authentication logic
"""

import hashlib

from app.main import MOCK_USERS, authenticate_user, verify_password


class TestPasswordVerification:
    """Test password verification functions"""

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        plain_password = "testpassword123"
        password_hash = hashlib.sha256(plain_password.encode()).hexdigest()

        assert verify_password(plain_password, password_hash) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        plain_password = "testpassword123"
        wrong_password = "wrongpassword"
        password_hash = hashlib.sha256(plain_password.encode()).hexdigest()

        assert verify_password(wrong_password, password_hash) is False

    def test_verify_password_empty(self):
        """Test password verification with empty password"""
        password_hash = hashlib.sha256(b"testpassword").hexdigest()

        assert verify_password("", password_hash) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case sensitive"""
        plain_password = "TestPassword123"
        password_hash = hashlib.sha256(plain_password.encode()).hexdigest()

        assert verify_password("testpassword123", password_hash) is False
        assert verify_password("TestPassword123", password_hash) is True

    def test_verify_password_with_special_characters(self):
        """Test password verification with special characters"""
        plain_password = "p@ssw0rd!#$%"
        password_hash = hashlib.sha256(plain_password.encode()).hexdigest()

        assert verify_password(plain_password, password_hash) is True

    def test_verify_password_with_spaces(self):
        """Test password verification with spaces"""
        plain_password = "password with spaces"
        password_hash = hashlib.sha256(plain_password.encode()).hexdigest()

        assert verify_password(plain_password, password_hash) is True
        assert verify_password("passwordwithspaces", password_hash) is False

    def test_verify_password_unicode(self):
        """Test password verification with unicode characters"""
        plain_password = "пароль密码"
        password_hash = hashlib.sha256(plain_password.encode()).hexdigest()

        assert verify_password(plain_password, password_hash) is True


class TestUserAuthentication:
    """Test user authentication logic"""

    def test_authenticate_user_success(self):
        """Test successful user authentication"""
        # Using the default admin user from MOCK_USERS
        user = authenticate_user("admin", "admin123")

        assert user is not None
        assert user["tenant_id"] == "default"
        assert "admin" in user["roles"]
        assert "admin" in user["scopes"]

    def test_authenticate_user_invalid_username(self):
        """Test authentication with invalid username"""
        user = authenticate_user("nonexistent", "password")

        assert user is None

    def test_authenticate_user_invalid_password(self):
        """Test authentication with invalid password"""
        user = authenticate_user("admin", "wrongpassword")

        assert user is None

    def test_authenticate_user_empty_username(self):
        """Test authentication with empty username"""
        user = authenticate_user("", "password")

        assert user is None

    def test_authenticate_user_empty_password(self):
        """Test authentication with empty password"""
        user = authenticate_user("admin", "")

        assert user is None

    def test_authenticate_user_returns_correct_data(self):
        """Test that authenticate_user returns all user data"""
        user = authenticate_user("admin", "admin123")

        assert user is not None
        assert "password_hash" in user
        assert "tenant_id" in user
        assert "roles" in user
        assert "scopes" in user
        assert "email" in user

    def test_authenticate_regular_user(self):
        """Test authentication for regular user"""
        # Using the default user from MOCK_USERS
        user = authenticate_user("user", "user123")

        assert user is not None
        assert user["tenant_id"] == "default"
        assert user["roles"] == ["user"]
        assert "read" in user["scopes"]

    def test_authenticate_case_sensitive_username(self):
        """Test that username is case sensitive"""
        user = authenticate_user("Admin", "admin123")  # Wrong case

        assert user is None

    def test_authenticate_user_with_sql_injection_attempt(self):
        """Test authentication with SQL injection attempt"""
        # Should safely return None without causing errors
        user = authenticate_user("admin' OR '1'='1", "password")

        assert user is None

    def test_authenticate_user_with_special_characters(self):
        """Test authentication with special characters in username"""
        user = authenticate_user("admin@#$%", "password")

        assert user is None


class TestUserAuthenticationSecurity:
    """Test security aspects of user authentication"""

    def test_timing_attack_resistance(self):
        """Test that authentication timing is consistent"""
        import time

        # Time authentication with valid username, wrong password
        start = time.time()
        authenticate_user("admin", "wrongpassword")
        time_valid_user = time.time() - start

        # Time authentication with invalid username
        start = time.time()
        authenticate_user("nonexistent", "wrongpassword")
        time_invalid_user = time.time() - start

        # The timing should be similar (within 50ms for this test)
        # Note: This is a basic test; real timing attack prevention requires more sophisticated approaches
        assert abs(time_valid_user - time_invalid_user) < 0.05

    def test_password_not_stored_in_plaintext(self):
        """Test that passwords are not stored in plaintext"""
        user = MOCK_USERS.get("admin")

        assert user is not None
        # Password hash should not equal plaintext password
        assert user["password_hash"] != "admin123"
        # Hash should be 64 characters (SHA256)
        assert len(user["password_hash"]) == 64

    def test_multiple_failed_authentication_attempts(self):
        """Test multiple failed authentication attempts"""
        # Should consistently return None without rate limiting (in basic implementation)
        for _ in range(10):
            user = authenticate_user("admin", "wrongpassword")
            assert user is None

    def test_authentication_with_null_bytes(self):
        """Test authentication with null bytes in input"""
        # Should safely handle null bytes
        user = authenticate_user("admin\x00injected", "password")
        assert user is None

        user = authenticate_user("admin", "password\x00injected")
        assert user is None


class TestUserAuthenticationEdgeCases:
    """Test edge cases for user authentication"""

    def test_authenticate_with_very_long_username(self):
        """Test authentication with very long username"""
        long_username = "a" * 10000
        user = authenticate_user(long_username, "password")

        assert user is None

    def test_authenticate_with_very_long_password(self):
        """Test authentication with very long password"""
        long_password = "a" * 10000
        user = authenticate_user("admin", long_password)

        assert user is None

    def test_authenticate_with_unicode_username(self):
        """Test authentication with unicode username"""
        user = authenticate_user("用户", "password")

        assert user is None

    def test_authenticate_with_whitespace_only_username(self):
        """Test authentication with whitespace-only username"""
        user = authenticate_user("   ", "password")

        assert user is None

    def test_authenticate_with_whitespace_only_password(self):
        """Test authentication with whitespace-only password"""
        user = authenticate_user("admin", "   ")

        assert user is None


class TestMockUserStore:
    """Test the mock user store"""

    def test_mock_users_structure(self):
        """Test that MOCK_USERS has correct structure"""
        assert isinstance(MOCK_USERS, dict)
        assert len(MOCK_USERS) > 0

        for username, user_data in MOCK_USERS.items():
            assert isinstance(username, str)
            assert isinstance(user_data, dict)
            assert "password_hash" in user_data
            assert "tenant_id" in user_data
            assert "roles" in user_data
            assert "scopes" in user_data

    def test_admin_user_exists(self):
        """Test that admin user exists in mock store"""
        assert "admin" in MOCK_USERS
        admin = MOCK_USERS["admin"]
        assert "admin" in admin["roles"]

    def test_regular_user_exists(self):
        """Test that regular user exists in mock store"""
        assert "user" in MOCK_USERS
        user = MOCK_USERS["user"]
        assert "user" in user["roles"]

    def test_user_roles_are_lists(self):
        """Test that user roles are stored as lists"""
        for user_data in MOCK_USERS.values():
            assert isinstance(user_data["roles"], list)
            assert isinstance(user_data["scopes"], list)

    def test_user_tenant_isolation(self):
        """Test that users have tenant_id set"""
        for user_data in MOCK_USERS.values():
            assert "tenant_id" in user_data
            assert isinstance(user_data["tenant_id"], str)
            assert len(user_data["tenant_id"]) > 0
