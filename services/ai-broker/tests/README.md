# AI Broker Service - Test Suite

Comprehensive test suite for the PropVerify AI Broker Service, following CORTX Platform testing standards.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── README.md               # This file
├── unit/                   # Unit tests
│   ├── __init__.py
│   ├── test_imports.py     # Import validation tests
│   ├── test_mock_functions.py  # Tests for mock AI functions
│   └── test_models.py      # Tests for Pydantic models
└── integration/            # Integration tests
    ├── __init__.py
    ├── test_health_endpoints.py    # Health check endpoints
    ├── test_completion_endpoint.py # /completion endpoint tests
    ├── test_embedding_endpoint.py  # /embedding endpoint tests
    └── test_models_endpoint.py     # /models endpoint tests
```

## Running Tests

### Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development/testing dependencies
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_models.py

# Run specific test class
pytest tests/unit/test_models.py::TestCompletionRequest

# Run specific test
pytest tests/unit/test_models.py::TestCompletionRequest::test_completion_request_minimal
```

### Run with Coverage

```bash
# Run tests with coverage report
pytest --cov=app --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=app --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Run with Markers

```bash
# Run only tests marked as 'unit'
pytest -m unit

# Run only tests marked as 'integration'
pytest -m integration

# Run only mock-related tests
pytest -m mock

# Exclude slow tests
pytest -m "not slow"
```

### Parallel Execution

```bash
# Run tests in parallel using all CPU cores
pytest -n auto

# Run tests using specific number of workers
pytest -n 4
```

## Test Coverage Goals

- **Overall Coverage**: >80%
- **Unit Tests**: All functions, classes, and models
- **Integration Tests**: All API endpoints and error scenarios
- **Edge Cases**: Input validation, error handling, concurrent requests

## Key Test Areas

### Unit Tests

1. **Mock Functions** (`test_mock_functions.py`)
   - `mock_completion()` - AI text completion mock
   - `mock_embedding()` - Vector embedding mock
   - Determinism, edge cases, data validation

2. **Pydantic Models** (`test_models.py`)
   - `CompletionRequest` / `CompletionResponse`
   - `EmbeddingRequest` / `EmbeddingResponse`
   - Validation rules, defaults, serialization

3. **Imports** (`test_imports.py`)
   - Verify all imports work correctly
   - CORTX backend integration
   - Optional dependencies handling

### Integration Tests

1. **Health Endpoints** (`test_health_endpoints.py`)
   - `/healthz` - Basic health check
   - `/readyz` - Readiness with Vertex AI status
   - `/` - Service metadata

2. **Completion Endpoint** (`test_completion_endpoint.py`)
   - POST `/completion` - Text generation
   - Mock mode behavior
   - Input validation
   - Error handling
   - Concurrent requests
   - Authentication scenarios

3. **Embedding Endpoint** (`test_embedding_endpoint.py`)
   - POST `/embedding` - Vector embeddings
   - Mock mode behavior
   - Deterministic output
   - Edge cases (empty text, Unicode, etc.)
   - Concurrent requests

4. **Models Endpoint** (`test_models_endpoint.py`)
   - GET `/models` - List available models
   - Model metadata validation
   - Vertex AI status reporting

## Fixtures

Available in `conftest.py`:

- `client` - FastAPI TestClient
- `auth_headers` - Mock authentication headers
- `sample_completion_request` - Sample completion payload
- `sample_embedding_request` - Sample embedding payload
- `mock_vertex_completion` - Mock Vertex AI completion
- `mock_vertex_embedding` - Mock Vertex AI embedding
- `vertex_available_env` - Enable Vertex AI in tests
- `disable_auth` / `enable_auth` - Toggle authentication

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt -r requirements-dev.txt
    pytest --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## AI-Specific Testing Considerations

### Mock Mode Testing

- All tests run in mock mode by default (no Vertex AI required)
- Mock functions provide deterministic, testable outputs
- Tests verify graceful degradation when Vertex AI unavailable

### Vertex AI Integration Testing

- Tests use mocks for Vertex AI responses
- Real Vertex AI testing requires:
  - Valid `VERTEX_PROJECT_ID` environment variable
  - Google Cloud credentials
  - Network access to Vertex AI endpoints

### Rate Limiting

- Tests include concurrent request scenarios
- Verify service handles multiple simultaneous requests
- No rate limiting currently implemented (future enhancement)

### Error Handling

- Tests verify graceful error handling
- Mock failures and timeouts
- Validate error response formats

## Writing New Tests

### Unit Test Template

```python
# tests/unit/test_new_feature.py
import pytest

class TestNewFeature:
    """Test suite for new feature"""

    def test_basic_functionality(self):
        """Test basic functionality"""
        # Arrange
        input_data = "test"

        # Act
        result = my_function(input_data)

        # Assert
        assert result is not None
```

### Integration Test Template

```python
# tests/integration/test_new_endpoint.py
import pytest
from fastapi.testclient import TestClient

class TestNewEndpoint:
    """Test suite for new endpoint"""

    def test_endpoint_success(self, client: TestClient):
        """Test successful request"""
        response = client.post("/new-endpoint", json={"data": "test"})
        assert response.status_code == 200
```

## Troubleshooting

### Import Errors

```bash
# Ensure you're in the correct directory
cd /Users/michael/Development/sinergysolutionsllc/services/ai-broker

# Install in development mode
pip install -e .
```

### Coverage Not Reporting

```bash
# Ensure .coveragerc is present
ls -la .coveragerc

# Run with explicit config
pytest --cov=app --cov-config=.coveragerc
```

### Tests Hanging

```bash
# Add timeout to prevent hanging tests
pytest --timeout=30
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [CORTX Platform Testing Standards](../../docs/operations/index.md)
- [Quality Assurance Lead Agent](../../.claude/agents/quality-assurance-lead.md)
