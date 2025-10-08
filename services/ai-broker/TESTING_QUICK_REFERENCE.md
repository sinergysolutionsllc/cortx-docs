# AI Broker Testing - Quick Reference Card

## Quick Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific category
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only

# Run specific file
pytest tests/unit/test_models.py

# Run specific test
pytest tests/unit/test_models.py::TestCompletionRequest::test_completion_request_minimal

# Run with markers
pytest -m unit                        # All unit tests
pytest -m integration                 # All integration tests

# Parallel execution
pytest -n auto                        # Use all CPUs
pytest -n 4                          # Use 4 workers

# Using Makefile
make test                            # All tests with coverage
make test-unit                       # Unit tests only
make test-integration                # Integration tests only
make test-coverage                   # Generate HTML report

# Using shell script
./run_tests.sh                       # All tests
./run_tests.sh unit                  # Unit tests
./run_tests.sh integration           # Integration tests
./run_tests.sh coverage              # HTML coverage
./run_tests.sh fast                  # Fast (no coverage)
```

## Test Statistics

- **Total Tests**: 145
- **Unit Tests**: 53 (36.6%)
- **Integration Tests**: 92 (63.4%)
- **Test Files**: 7
- **Lines of Test Code**: ~1,496
- **Coverage Target**: >80%

## Test Files Overview

| File | Tests | Purpose |
|------|-------|---------|
| `test_imports.py` | 9 | Import validation |
| `test_mock_functions.py` | 20 | Mock AI functions |
| `test_models.py` | 24 | Pydantic models |
| `test_health_endpoints.py` | 14 | Health checks |
| `test_completion_endpoint.py` | 25 | Text completion API |
| `test_embedding_endpoint.py` | 30 | Embedding API |
| `test_models_endpoint.py` | 23 | Model listing API |

## Key Test Areas

### Unit Tests (53)

- ✅ Mock completion function (10 tests)
- ✅ Mock embedding function (10 tests)
- ✅ CompletionRequest model (9 tests)
- ✅ CompletionResponse model (3 tests)
- ✅ EmbeddingRequest model (4 tests)
- ✅ EmbeddingResponse model (4 tests)
- ✅ Model validation (4 tests)
- ✅ Import validation (9 tests)

### Integration Tests (92)

- ✅ Health endpoints (14 tests)
  - /healthz (6 tests)
  - /readyz (5 tests)
  - / root (4 tests)
- ✅ Completion endpoint (25 tests)
  - Success scenarios (8 tests)
  - Validation (6 tests)
  - Edge cases (7 tests)
  - Auth (2 tests)
  - Concurrency (2 tests)
- ✅ Embedding endpoint (30 tests)
  - Success scenarios (6 tests)
  - Edge cases (10 tests)
  - Determinism (3 tests)
  - Auth (2 tests)
  - Concurrency (2 tests)
  - Special cases (7 tests)
- ✅ Models endpoint (23 tests)
  - Basic functionality (5 tests)
  - Model structure (8 tests)
  - Model verification (6 tests)
  - Edge cases (4 tests)

## Common Test Patterns

### Using Fixtures

```python
def test_example(client, auth_headers, sample_completion_request):
    response = client.post("/completion",
                          json=sample_completion_request,
                          headers=auth_headers)
    assert response.status_code == 200
```

### Testing Validation

```python
def test_invalid_input(client):
    response = client.post("/completion", json={"invalid": "data"})
    assert response.status_code == 422  # Validation error
```

### Testing Edge Cases

```python
def test_empty_input(client):
    response = client.post("/completion", json={"prompt": ""})
    assert response.status_code == 200
    assert len(response.json()["text"]) > 0
```

## Debugging Tests

```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Show local variables on failure
pytest --showlocals

# Run with debugger on failure
pytest --pdb
```

## Coverage Tips

```bash
# View missing lines
pytest --cov=app --cov-report=term-missing

# Generate HTML report
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Check specific module
pytest --cov=app.main --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=app --cov-fail-under=80
```

## Continuous Integration

Tests run automatically on:

- Every push to main/develop
- Every pull request
- Python versions: 3.10, 3.11, 3.12
- Coverage uploaded to Codecov

## Troubleshooting

### Import Errors

```bash
# Ensure correct directory
cd /path/to/services/ai-broker

# Check Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### Coverage Not Working

```bash
# Clean old coverage data
rm -rf .coverage htmlcov/

# Run with explicit config
pytest --cov=app --cov-config=.coveragerc
```

### Tests Hanging

```bash
# Add timeout
pytest --timeout=30
```

### Authentication Issues

```bash
# Disable auth for testing
export REQUIRE_AUTH=false
```

## Files Created

```
services/ai-broker/
├── .coveragerc                      # Coverage config
├── .github/workflows/test.yml       # CI/CD pipeline
├── Makefile                         # Make commands
├── pytest.ini                       # Pytest config
├── requirements-dev.txt             # Dev dependencies
├── run_tests.sh                     # Test runner
├── TESTING_SUMMARY.md              # Full documentation
├── TESTING_QUICK_REFERENCE.md      # This file
└── tests/
    ├── README.md                    # Test guide
    ├── conftest.py                  # Fixtures
    ├── unit/
    │   ├── test_imports.py
    │   ├── test_mock_functions.py
    │   └── test_models.py
    └── integration/
        ├── test_health_endpoints.py
        ├── test_completion_endpoint.py
        ├── test_embedding_endpoint.py
        └── test_models_endpoint.py
```

## Next Steps

1. Run tests: `pytest --cov=app --cov-report=html`
2. View coverage: `open htmlcov/index.html`
3. Verify >80% coverage achieved
4. Add CI/CD to repository
5. Consider future enhancements:
   - Real Vertex AI integration tests
   - Streaming response tests
   - Rate limiting tests
   - Security/prompt injection tests
   - Performance tests

## Resources

- Full Documentation: `TESTING_SUMMARY.md`
- Test Guide: `tests/README.md`
- Quality Agent: `.claude/agents/quality-assurance-lead.md`
- pytest docs: <https://docs.pytest.org/>
- FastAPI testing: <https://fastapi.tiangolo.com/tutorial/testing/>
