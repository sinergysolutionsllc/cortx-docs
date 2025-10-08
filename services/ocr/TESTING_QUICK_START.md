# OCR Service Testing Quick Start

Quick reference guide for running and managing tests.

## Setup

```bash
# Install test dependencies
pip install -r requirements-dev.txt
```

## Common Commands

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html
```

### View Coverage Report

```bash
open htmlcov/index.html
```

### Run Specific Tests

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific file
pytest tests/unit/test_processor.py

# Specific test
pytest tests/unit/test_processor.py::TestTesseractOCR::test_extract_text_success

# Tests matching pattern
pytest -k "test_extract"
```

### Run in Parallel

```bash
# Automatic CPU detection
pytest -n auto

# Specific number of workers
pytest -n 4
```

### Verbose Output

```bash
# Show all test names
pytest -v

# Show print statements
pytest -s

# Show full traceback
pytest --tb=long

# Combination
pytest -vvs --tb=long
```

## Test Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run tests that don't need Anthropic API
pytest -m "not requires_anthropic"
```

## Coverage Commands

```bash
# Basic coverage
pytest --cov=app

# Terminal report with missing lines
pytest --cov=app --cov-report=term-missing

# HTML report
pytest --cov=app --cov-report=html

# XML report (for CI)
pytest --cov=app --cov-report=xml

# All reports
pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml

# Fail if coverage below 80%
pytest --cov=app --cov-fail-under=80
```

## Debugging

```bash
# Stop on first failure
pytest -x

# Stop after N failures
pytest --maxfail=3

# Show local variables in tracebacks
pytest --showlocals

# Enter debugger on failure
pytest --pdb

# Drop into debugger at start of test
pytest --trace
```

## Watch Mode

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests on file changes
ptw

# With coverage
ptw -- --cov=app
```

## Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
pytest --cov=app --cov-fail-under=80
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

Make executable:

```bash
chmod +x .git/hooks/pre-commit
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    pytest --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

### GitLab CI

```yaml
test:
  script:
    - pip install -r requirements-dev.txt
    - pytest --cov=app --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests (fast)
│   ├── test_processor.py    # OCR logic tests
│   ├── test_models.py       # Database tests
│   └── test_schemas.py      # Schema tests
└── integration/             # Integration tests
    ├── test_api.py          # API endpoint tests
    └── test_cache_stats.py  # Cache/stats tests
```

## Writing New Tests

### Basic Test

```python
def test_example(db_session):
    """Test description"""
    # Arrange
    data = {"key": "value"}

    # Act
    result = process(data)

    # Assert
    assert result.status == "success"
```

### API Test

```python
def test_endpoint(client):
    """Test API endpoint"""
    response = client.post("/endpoint", json={"key": "value"})

    assert response.status_code == 200
    assert response.json()["result"] == "expected"
```

### Mock External Service

```python
@patch('app.processor.external_service')
def test_with_mock(mock_service):
    """Test with mocked service"""
    mock_service.return_value = "mocked_result"

    result = my_function()

    assert result == "expected"
    mock_service.assert_called_once()
```

## Troubleshooting

### Clear Cache

```bash
pytest --cache-clear
```

### Reinstall Dependencies

```bash
pip install --force-reinstall -r requirements-dev.txt
```

### Check Test Collection

```bash
pytest --collect-only
```

### Dry Run

```bash
pytest --collect-only -q
```

### Show Fixtures

```bash
pytest --fixtures
```

### Show Markers

```bash
pytest --markers
```

## Performance

### Fastest Tests First

```bash
pytest --ff
```

### Run Failed Tests First

```bash
pytest --lf
```

### Disable Warnings

```bash
pytest --disable-warnings
```

### Quiet Mode

```bash
pytest -q
```

## Code Quality

### Run Linter

```bash
ruff check app/ tests/
```

### Run Formatter

```bash
black app/ tests/
```

### Type Check

```bash
mypy app/
```

### All Quality Checks

```bash
ruff check app/ tests/ && \
black --check app/ tests/ && \
mypy app/ && \
pytest --cov=app --cov-fail-under=80
```

## Current Test Status

- **Total Tests**: 138
- **Unit Tests**: 85
- **Integration Tests**: 53
- **Target Coverage**: >80%
- **Test Files**: 9

## Resources

- Full Documentation: [tests/README.md](tests/README.md)
- Implementation Summary: [TEST_IMPLEMENTATION_SUMMARY.md](TEST_IMPLEMENTATION_SUMMARY.md)
- Pytest Docs: <https://docs.pytest.org/>
- Coverage Docs: <https://coverage.readthedocs.io/>
