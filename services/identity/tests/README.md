# Identity Service Test Suite

Comprehensive test suite for the CORTX Identity Service, implementing JWT-based authentication and authorization testing.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── README.md                # This file
├── unit/                    # Unit tests
│   ├── test_jwt_tokens.py           # JWT token generation/validation
│   ├── test_authentication.py       # User authentication logic
│   ├── test_rbac_authorization.py   # RBAC authorization
│   └── test_refresh_tokens.py       # Refresh token handling
├── integration/             # Integration tests
│   ├── test_auth_endpoints.py       # Login/logout endpoints
│   ├── test_refresh_endpoints.py    # Token refresh endpoints
│   ├── test_user_management.py      # User management & RBAC
│   └── test_tenant_isolation.py     # Tenant isolation & error handling
└── __utils__/               # Test utilities
    ├── __init__.py
    └── factories.py         # Test data factories

```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run with detailed coverage report
pytest --cov=app --cov-report=html
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_jwt_tokens.py

# Run specific test class
pytest tests/unit/test_jwt_tokens.py::TestJWTTokenGeneration

# Run specific test
pytest tests/unit/test_jwt_tokens.py::TestJWTTokenGeneration::test_create_access_token_default_expiry
```

### Run Tests with Markers

```bash
# Run security tests
pytest -m security

# Run slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

## Test Coverage

The test suite aims for >80% code coverage across all modules:

- **JWT Token Generation**: 100% coverage
- **Authentication Logic**: 100% coverage
- **RBAC Authorization**: 100% coverage
- **Refresh Tokens**: 100% coverage
- **API Endpoints**: 95%+ coverage
- **Error Handling**: 90%+ coverage

### View Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Open in browser (macOS)
open htmlcov/index.html

# View in terminal
pytest --cov=app --cov-report=term-missing
```

## Test Categories

### Unit Tests (tests/unit/)

**test_jwt_tokens.py** - 45 test cases

- JWT token generation (default/custom expiry, claims)
- Token validation (valid, expired, malformed)
- Token security (signature, algorithm, issuer)
- Edge cases (long usernames, special characters, unicode)

**test_authentication.py** - 35 test cases

- Password verification (correct, incorrect, case sensitivity)
- User authentication (success, failures, edge cases)
- Security aspects (timing attacks, plaintext passwords)
- Mock user store validation

**test_rbac_authorization.py** - 30 test cases

- Token verification (valid, expired, invalid)
- Current user extraction
- Role-based authorization (admin, user, multiple roles)
- Scope-based authorization (read, write, admin)
- Tenant isolation in authorization

**test_refresh_tokens.py** - 35 test cases

- Refresh token generation (basic, expiry, claims)
- Access token creation from refresh
- Token type differentiation (access vs refresh)
- Token rotation scenarios
- Security aspects (different secrets, preservation of data)

### Integration Tests (tests/integration/)

**test_auth_endpoints.py** - 50 test cases

- Login endpoints (POST /v1/auth/login, POST /v1/auth/token)
- Token verification (GET /v1/auth/verify)
- Current user info (GET /v1/me)
- Health check (GET /health)
- Service info (GET /docs/info)
- Security (SQL injection, XSS, rate limiting simulation)

**test_refresh_endpoints.py** - 25 test cases

- Token refresh (POST /v1/auth/refresh)
- Token revocation (POST /v1/auth/revoke)
- Token rotation flows
- Security (token type validation, secret isolation)
- Edge cases (expired, invalid, malformed tokens)

**test_user_management.py** - 30 test cases

- Tenant management (GET /v1/tenants)
- Role management (POST /v1/roles)
- RBAC enforcement (admin vs user access)
- Scope-based authorization
- Edge cases (empty roles, case sensitivity, duplicates)

**test_tenant_isolation.py** - 40 test cases

- Tenant isolation (different contexts, same usernames)
- Error handling (invalid tokens, missing headers, validation)
- Security error handling (SQL injection, XSS, path traversal)
- Concurrent requests
- Edge cases (unicode, null bytes, large payloads)

## Test Fixtures

### Available Fixtures (conftest.py)

- `client`: FastAPI test client
- `test_secret_key`: Test JWT secret key
- `test_refresh_secret_key`: Test refresh secret key
- `mock_user_data`: Mock user data
- `mock_admin_data`: Mock admin data
- `create_test_token`: Factory for creating test tokens
- `create_refresh_token`: Factory for creating refresh tokens
- `auth_headers`: Factory for creating auth headers
- `admin_auth_headers`: Admin auth headers
- `expired_token`: Expired JWT token
- `invalid_token`: Invalid token string
- `malformed_token`: Malformed JWT token
- `mock_users`: Mock user database
- `different_tenant_token`: Token for different tenant

## Test Data Factories

Use the factories in `tests/__utils__/factories.py`:

```python
from tests.__utils__.factories import TokenFactory, UserFactory, TenantFactory

# Create test token
token = TokenFactory.create_token(
    secret_key="test_key",
    username="testuser",
    roles=["admin"]
)

# Create test user
user = UserFactory.create_user(username="john")

# Create test tenant
tenant = TenantFactory.create_tenant(tenant_id="acme")
```

## Writing New Tests

### Unit Test Template

```python
import pytest

class TestNewFeature:
    """Test new feature"""

    def test_feature_success(self):
        """Test successful feature operation"""
        # Arrange
        data = {...}

        # Act
        result = function(data)

        # Assert
        assert result == expected

    def test_feature_failure(self):
        """Test feature failure scenario"""
        with pytest.raises(ExpectedException):
            function(invalid_data)
```

### Integration Test Template

```python
def test_new_endpoint(client, auth_headers):
    """Test new API endpoint"""
    headers = auth_headers(username="testuser")

    response = client.post(
        "/v1/new-endpoint",
        json={"data": "value"},
        headers=headers
    )

    assert response.status_code == 200
    assert "expected_field" in response.json()
```

## Continuous Integration

Tests are run automatically on:

- Every pull request
- Every commit to main branch
- Nightly builds

CI pipeline ensures:

- All tests pass
- Coverage threshold (>80%) is met
- No security vulnerabilities
- Code quality standards are met

## Troubleshooting

### Common Issues

**Import Errors**

```bash
# Ensure you're in the service directory
cd services/identity

# Install dependencies
pip install -r requirements-dev.txt
```

**Coverage Too Low**

```bash
# View missing lines
pytest --cov=app --cov-report=term-missing

# Generate detailed HTML report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

**Test Failures**

```bash
# Run with verbose output
pytest -v

# Run with print statements shown
pytest -s

# Run specific failing test
pytest tests/path/to/test.py::TestClass::test_method -v
```

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure >80% coverage for new code
3. Add integration tests for new endpoints
4. Update this README if adding new test categories
5. Run full test suite before committing

## Related Documentation

- [Identity Service README](../README.md)
- [OpenAPI Specification](../openapi.yaml)
- [Quality Assurance Lead Guide](../../../.claude/agents/quality-assurance-lead.md)
