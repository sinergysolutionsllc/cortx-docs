# OCR Service Test Suite

Comprehensive test suite for the AI-Enhanced OCR Service with >80% test coverage.

## Test Structure

```
tests/
├── conftest.py              # Shared pytest fixtures and configuration
├── unit/                    # Unit tests for individual components
│   ├── test_processor.py    # OCR processor logic tests
│   ├── test_models.py       # Database model tests
│   └── test_schemas.py      # Pydantic schema validation tests
└── integration/             # Integration tests for API endpoints
    ├── test_api.py          # Main API endpoint tests
    └── test_cache_stats.py  # Cache and statistics endpoint tests
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
pytest
```

### Run with Coverage Report

```bash
pytest --cov=app --cov-report=html --cov-report=term
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_processor.py

# Specific test class
pytest tests/unit/test_processor.py::TestTesseractOCR

# Specific test function
pytest tests/unit/test_processor.py::TestTesseractOCR::test_extract_text_success
```

### Run Tests with Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run tests that don't require external dependencies
pytest -m "not requires_anthropic"

# Run slow tests
pytest -m slow
```

### Parallel Test Execution

```bash
# Run tests in parallel (faster execution)
pytest -n auto
```

### Generate Coverage Reports

```bash
# Terminal report with missing lines
pytest --cov=app --cov-report=term-missing

# HTML report (open htmlcov/index.html)
pytest --cov=app --cov-report=html

# XML report (for CI/CD)
pytest --cov=app --cov-report=xml
```

## Test Coverage

Target: **>80% code coverage**

### Coverage by Module

- **processor.py**: OCR processing engine
  - DocumentPreprocessor: Image preprocessing
  - TesseractOCR: Tesseract extraction
  - ClaudeVisionOCR: AI vision extraction
  - OCRProcessor: Multi-tier pipeline

- **models.py**: Database models
  - OCRJob: Job tracking
  - OCRReview: Human review records
  - OCRCache: Result caching
  - Enums: OCRStatus, OCRTier

- **schemas.py**: API schemas
  - Request/response validation
  - Pydantic models
  - JSON serialization

- **main.py**: FastAPI application
  - API endpoints
  - Background tasks
  - Error handling

## Test Fixtures

### Database Fixtures

- `db_engine`: Test database engine
- `db_session`: Test database session
- `client`: FastAPI test client

### Data Fixtures

- `sample_image`: Test image with text
- `sample_image_base64`: Base64-encoded test image
- `sample_degraded_image`: Low-quality test image
- `sample_document_hash`: SHA-256 hash
- `sample_extracted_text`: Sample OCR results
- `sample_extracted_fields`: Structured field data

### Model Fixtures

- `sample_ocr_job`: Basic OCR job
- `completed_ocr_job`: Completed job with results
- `review_pending_job`: Job awaiting review
- `sample_cache_entry`: Cache entry
- `sample_review`: Review record

### Request Fixtures

- `sample_ocr_request`: OCR extraction request
- `sample_review_request`: Review submission request

## Writing New Tests

### Unit Test Example

```python
def test_new_feature(db_session):
    """Test description"""
    # Arrange
    data = create_test_data()

    # Act
    result = process_data(data)

    # Assert
    assert result.status == "success"
    assert result.value > 0
```

### Integration Test Example

```python
def test_new_endpoint(client):
    """Test new API endpoint"""
    response = client.post("/new-endpoint", json={"key": "value"})

    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

### Async Test Example

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function"""
    result = await async_operation()
    assert result is not None
```

## Mocking External Dependencies

### Mock Tesseract

```python
@patch('app.processor.pytesseract.image_to_string')
def test_with_mock_tesseract(mock_tesseract):
    mock_tesseract.return_value = "Mocked text"
    # Test code
```

### Mock Anthropic API

```python
@patch('app.processor.Anthropic')
def test_with_mock_anthropic(mock_anthropic_class):
    mock_client = MagicMock()
    mock_anthropic_class.return_value = mock_client
    # Test code
```

### Mock Environment Variables

```python
@patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
def test_with_api_key():
    # Test code with API key set
```

## Continuous Integration

### GitHub Actions Example

```yaml
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    pytest --cov=app --cov-report=xml --cov-report=term

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Test Quality Guidelines

1. **Arrange-Act-Assert**: Structure tests clearly
2. **Single Responsibility**: One test, one concept
3. **Descriptive Names**: Clear test function names
4. **Independent Tests**: No test dependencies
5. **Fast Execution**: Mock slow operations
6. **Clear Assertions**: Explicit expected values
7. **Edge Cases**: Test boundary conditions
8. **Error Cases**: Test failure scenarios

## Troubleshooting

### Tests Fail Locally

```bash
# Clean pytest cache
pytest --cache-clear

# Verbose output with full tracebacks
pytest -vvs --tb=long

# Run specific failing test
pytest tests/unit/test_file.py::test_name -vvs
```

### Coverage Issues

```bash
# See which lines are not covered
pytest --cov=app --cov-report=term-missing

# Generate detailed HTML report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Database Issues

```bash
# Tests use in-memory SQLite by default
# If issues occur, check conftest.py db_engine fixture
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
