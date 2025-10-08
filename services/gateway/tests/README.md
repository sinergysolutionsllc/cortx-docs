# Gateway Service Test Suite

Comprehensive test suite for the CORTX Gateway service.

## Test Organization

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest fixtures and configuration
├── unit/                       # Unit tests for business logic
│   ├── test_policy_router.py   # PolicyRouter unit tests
│   └── test_auth_middleware.py # Authentication middleware tests
├── integration/                # Integration tests for API endpoints
│   ├── test_orchestrator_api.py       # Orchestrator endpoint tests
│   ├── test_platform_services_proxy.py # Platform services proxy tests
│   ├── test_fedsuite_proxy.py         # FedSuite proxy tests
│   ├── test_propverify_proxy.py       # PropVerify proxy tests
│   ├── test_analytics_api.py          # Analytics endpoint tests
│   ├── test_services_api.py           # Services discovery tests
│   └── test_main_api.py               # Main app endpoint tests
└── __utils__/                  # Test utilities
    ├── factories.py            # Test data factories
    └── helpers.py              # Test helper functions
```

## Running Tests

### Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Types

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Authentication tests
pytest -m auth

# Proxy tests
pytest -m proxy
```

### Run Specific Test Files

```bash
# Run policy router tests
pytest tests/unit/test_policy_router.py

# Run orchestrator API tests
pytest tests/integration/test_orchestrator_api.py
```

### Run with Coverage Report

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View HTML coverage report
open htmlcov/index.html
```

### Run Tests in Parallel

```bash
# Run tests across multiple CPUs
pytest -n auto
```

## Test Coverage

Target coverage: >80%

Current coverage areas:

- PolicyRouter routing logic (Conservative, Hybrid, Agentic modes)
- Authentication middleware (JWT verification, role/scope checks)
- API endpoints (Orchestrator, Analytics, Services)
- Proxy functionality (RAG, OCR, Ledger, FedSuite, PropVerify)
- Error handling and edge cases
- Health checks and monitoring

## Writing Tests

### Unit Tests

Unit tests focus on individual components in isolation:

```python
@pytest.mark.unit
async def test_policy_router_conservative_mode(mock_registry_client):
    """Test conservative mode routing"""
    router = PolicyRouter(mock_registry_client)
    # Test implementation
```

### Integration Tests

Integration tests verify API endpoint behavior:

```python
@pytest.mark.integration
def test_create_validation_job(client, auth_headers):
    """Test POST /jobs/validate endpoint"""
    response = client.post(
        "/jobs/validate",
        params={"domain": "test", "mode": "static"},
        json={"data": "test"},
        headers=auth_headers
    )
    assert response.status_code == 200
```

### Using Fixtures

Common fixtures are defined in `conftest.py`:

```python
def test_with_auth(client, auth_headers):
    """Use auth_headers fixture for authenticated requests"""
    response = client.get("/protected", headers=auth_headers)
    assert response.status_code == 200
```

### Using Factories

Test data factories simplify test data creation:

```python
from tests.__utils__.factories import create_validation_request_data

def test_validation():
    request_data = create_validation_request_data(
        domain="test.domain",
        mode="hybrid"
    )
```

## Continuous Integration

Tests run automatically on:

- Pull requests
- Pushes to main branch
- Nightly builds

CI configuration in `.github/workflows/test.yml`

## Troubleshooting

### Mock Issues

If mocks aren't working as expected, verify:

1. The mock is patched at the correct import path
2. AsyncMock is used for async functions
3. The mock is configured before the test runs

### Coverage Gaps

To identify coverage gaps:

```bash
# Generate detailed coverage report
pytest --cov=app --cov-report=term-missing

# Check specific file coverage
pytest --cov=app/policy_router.py --cov-report=term-missing
```

### Flaky Tests

If tests fail intermittently:

1. Check for timing issues in async code
2. Verify mocks are reset between tests
3. Look for shared state between tests
4. Use `pytest-xdist` to identify race conditions

## Best Practices

1. **Arrange-Act-Assert**: Structure tests clearly
2. **One assertion per test**: Keep tests focused
3. **Descriptive names**: Test names should describe behavior
4. **Mock external dependencies**: Don't call real services
5. **Test edge cases**: Include error scenarios
6. **Use fixtures**: Reuse common test setup
7. **Keep tests fast**: Unit tests should run in milliseconds
