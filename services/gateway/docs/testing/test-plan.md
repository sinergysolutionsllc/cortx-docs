# Gateway Service Test Plan

## Test Objectives

1. Verify all API endpoints function correctly
2. Ensure authentication and authorization work as expected
3. Validate upstream service integration
4. Confirm error handling and resilience
5. Measure performance under load

## Test Scope

### In Scope

- All REST API endpoints
- JWT authentication flows
- Suite proxy routing
- Analytics endpoints
- Health and readiness probes
- Error handling and status codes
- Request/response validation
- CORS configuration

### Out of Scope

- Upstream service business logic (tested in respective services)
- Frontend UI testing
- Infrastructure provisioning
- Database schema validation

## Test Environments

### Local Development

- Target: `http://localhost:8080`
- Auth: Optional (REQUIRE_AUTH=false)
- Purpose: Unit and integration testing

### Staging

- Target: `https://staging-api.cortx.ai`
- Auth: Required
- Purpose: End-to-end testing, smoke tests

### Production

- Target: `https://api.cortx.ai`
- Auth: Required
- Purpose: Smoke tests, monitoring validation

## Test Categories

### 1. Unit Tests

**Framework**: pytest
**Location**: `services/gateway/tests/unit/`
**Coverage Target**: >80%

#### Test Cases

```python
# test_health.py
def test_health_endpoint_returns_200():
    """Health endpoint should return 200 OK"""

def test_health_response_structure():
    """Health response should include status, service, version"""

# test_auth.py
def test_missing_token_returns_401():
    """Requests without token should return 401"""

def test_invalid_token_returns_401():
    """Requests with invalid token should return 401"""

def test_expired_token_returns_401():
    """Requests with expired token should return 401"""

# test_validation_jobs.py
def test_create_validation_job_success():
    """Creating validation job should return job_id"""

def test_create_validation_job_missing_domain_returns_422():
    """Missing domain parameter should return 422"""

def test_get_job_status_returns_correct_structure():
    """Job status should include all required fields"""

def test_get_nonexistent_job_returns_404():
    """Non-existent job should return 404"""

# test_proxy.py
def test_fedsuite_proxy_forwards_request():
    """FedSuite proxy should forward to backend"""

def test_proxy_includes_auth_headers():
    """Proxy should include Authorization header"""

def test_proxy_handles_backend_errors():
    """Proxy should return appropriate error for backend failures"""
```

#### Run Unit Tests

```bash
cd services/gateway
pytest tests/unit/ -v --cov=app --cov-report=html
```

### 2. Integration Tests

**Framework**: pytest + httpx
**Location**: `services/gateway/tests/integration/`
**Dependencies**: All upstream services must be running

#### Test Cases

```python
# test_validation_flow.py
def test_end_to_end_validation_job():
    """
    1. Create validation job
    2. Poll for completion
    3. Verify results
    """

def test_validation_with_failures():
    """
    1. Create job with invalid data
    2. Get failures
    3. Explain failure
    4. Update decision
    """

# test_analytics_integration.py
def test_comparison_summary_aggregates_correctly():
    """Analytics should aggregate from validation results"""

def test_detailed_comparison_filters():
    """Filters should correctly limit results"""

# test_auth_integration.py
def test_login_and_use_token():
    """
    1. Login via Identity service
    2. Use token in Gateway request
    3. Verify request succeeds
    """
```

#### Run Integration Tests

```bash
# Start all services
docker-compose up -d

# Run integration tests
pytest tests/integration/ -v --tb=short

# Cleanup
docker-compose down
```

### 3. API Contract Tests

**Framework**: schemathesis
**Location**: `services/gateway/tests/contract/`
**Source**: OpenAPI specification

#### Test OpenAPI Compliance

```bash
# Install schemathesis
pip install schemathesis

# Test all endpoints against spec
schemathesis run services/gateway/openapi.yaml \
  --base-url http://localhost:8080 \
  --hypothesis-max-examples=50 \
  --checks all

# Generate test report
schemathesis run services/gateway/openapi.yaml \
  --base-url http://localhost:8080 \
  --hypothesis-max-examples=50 \
  --junit-xml=test-results.xml
```

### 4. Performance Tests

**Framework**: Locust
**Location**: `services/gateway/tests/performance/`

#### Test Scenarios

```python
# locustfile.py
from locust import HttpUser, task, between

class GatewayUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login and get token"""
        response = self.client.post("/v1/auth/login", json={
            "username": "test",
            "password": "test"
        })
        self.token = response.json()["access_token"]

    @task(3)
    def get_health(self):
        """Health check - high frequency"""
        self.client.get("/health")

    @task(2)
    def create_validation_job(self):
        """Create validation job - medium frequency"""
        self.client.post(
            "/jobs/validate?domain=test",
            json={"input_data": {}},
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(1)
    def get_analytics(self):
        """Get analytics - low frequency"""
        self.client.get(
            "/analytics/comparison/summary?domain=test&days_back=7",
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

#### Run Performance Tests

```bash
# Install locust
pip install locust

# Run with web UI
locust -f tests/performance/locustfile.py --host http://localhost:8080

# Run headless
locust -f tests/performance/locustfile.py \
  --host http://localhost:8080 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --html performance-report.html
```

#### Performance Targets

| Metric | Target | Acceptable |
|--------|--------|------------|
| Health check latency (p50) | < 50ms | < 100ms |
| Job creation latency (p50) | < 200ms | < 500ms |
| Job status latency (p50) | < 100ms | < 200ms |
| Analytics latency (p50) | < 500ms | < 1000ms |
| Error rate | < 0.1% | < 1% |
| Throughput | > 1000 req/s | > 500 req/s |

### 5. Security Tests

**Framework**: pytest + custom security checks
**Location**: `services/gateway/tests/security/`

#### Test Cases

```python
# test_authentication.py
def test_no_token_returns_401():
    """Endpoints should require authentication"""

def test_malformed_token_returns_401():
    """Malformed tokens should be rejected"""

def test_sql_injection_prevention():
    """SQL injection attempts should be blocked"""

def test_xss_prevention():
    """XSS attempts should be sanitized"""

# test_authorization.py
def test_tenant_isolation():
    """Users cannot access other tenant data"""

def test_admin_only_endpoints():
    """Admin endpoints require admin role"""

def test_cross_tenant_access_denied():
    """Cross-tenant requests should be denied"""

# test_rate_limiting.py
def test_rate_limit_enforced():
    """Rate limits should prevent excessive requests"""

def test_rate_limit_per_tenant():
    """Rate limits should be per-tenant"""
```

### 6. Resilience Tests

**Framework**: Chaos Mesh / pytest
**Location**: `services/gateway/tests/resilience/`

#### Test Scenarios

```python
# test_circuit_breaker.py
def test_circuit_breaker_opens_on_failures():
    """Circuit breaker should open after N failures"""

def test_circuit_breaker_half_open_recovery():
    """Circuit breaker should attempt recovery"""

# test_timeout_handling.py
def test_upstream_timeout_returns_504():
    """Slow upstream should return 504"""

def test_timeout_does_not_block_other_requests():
    """Timeout should not affect other requests"""

# test_partial_failure.py
def test_validation_continues_on_rag_failure():
    """Validation should fallback to JSON on RAG failure"""

def test_analytics_unavailable_returns_graceful_error():
    """Analytics failure should not crash gateway"""
```

## Test Data Management

### Test Fixtures

```python
# conftest.py
import pytest

@pytest.fixture
def auth_token():
    """Valid JWT token for testing"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

@pytest.fixture
def test_tenant_id():
    """Test tenant ID"""
    return "test-tenant-123"

@pytest.fixture
def sample_validation_data():
    """Sample validation input data"""
    return {
        "input_data": {
            "field1": "value1",
            "field2": 123
        },
        "options": {
            "strict": True
        }
    }
```

### Mock Data

```python
# mocks.py
from unittest.mock import Mock

def mock_identity_service():
    """Mock Identity service responses"""
    mock = Mock()
    mock.verify_token.return_value = {
        "user_id": "test-user",
        "tenant_id": "test-tenant",
        "roles": ["user"]
    }
    return mock

def mock_validation_service():
    """Mock Validation service responses"""
    mock = Mock()
    mock.create_job.return_value = {
        "job_id": "test-job-123",
        "status": "pending"
    }
    return mock
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/gateway-tests.yml
name: Gateway Service Tests

on:
  push:
    branches: [main]
    paths:
      - 'services/gateway/**'
  pull_request:
    branches: [main]
    paths:
      - 'services/gateway/**'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd services/gateway
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run unit tests
        run: |
          cd services/gateway
          pytest tests/unit/ --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./services/gateway/coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker-compose up -d
      - name: Wait for services
        run: |
          sleep 30
          curl --retry 10 --retry-delay 5 http://localhost:8080/health
      - name: Run integration tests
        run: |
          cd services/gateway
          pytest tests/integration/ -v
      - name: Cleanup
        run: docker-compose down

  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install schemathesis
        run: pip install schemathesis
      - name: Start gateway
        run: docker-compose up -d gateway
      - name: Run contract tests
        run: |
          schemathesis run services/gateway/openapi.yaml \
            --base-url http://localhost:8080 \
            --checks all
```

## Test Reports

### Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html tests/

# Open report
open htmlcov/index.html
```

### Test Results Dashboard

Use pytest-html for comprehensive test reports:

```bash
pip install pytest-html
pytest --html=report.html --self-contained-html
```

## Sign-off Criteria

Gateway service is ready for production when:

- [ ] Unit test coverage > 80%
- [ ] All integration tests passing
- [ ] OpenAPI contract tests passing
- [ ] Performance tests meet targets
- [ ] Security tests passing
- [ ] Resilience tests passing
- [ ] Zero critical or high severity bugs
- [ ] Documentation complete and reviewed
- [ ] Deployment tested in staging
- [ ] Rollback procedure verified
