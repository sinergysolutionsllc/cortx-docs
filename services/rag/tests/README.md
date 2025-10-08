# RAG Service Tests

Comprehensive test suite for the CORTX RAG (Retrieval-Augmented Generation) service.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_chunking.py    # Document chunking logic
│   ├── test_embeddings.py  # Embedding generation
│   ├── test_retrieval.py   # Retrieval algorithms
│   ├── test_models.py      # Database models
│   └── test_database.py    # Database operations
├── integration/             # Integration tests (require database)
│   ├── test_document_api.py # Document management endpoints
│   └── test_rag_api.py     # RAG query endpoints
└── __utils__/              # Test utilities
    ├── factories.py        # Test data factories
    └── helpers.py          # Helper functions
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

### Run Unit Tests Only

```bash
pytest -m unit
```

### Run Integration Tests Only

```bash
pytest -m integration
```

### Run Specific Test File

```bash
pytest tests/unit/test_chunking.py
```

### Run Specific Test

```bash
pytest tests/unit/test_chunking.py::TestChunkText::test_chunk_text_basic
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html --cov-report=term
```

View HTML coverage report:

```bash
open htmlcov/index.html
```

### Run in Parallel

```bash
pytest -n auto  # Use all CPU cores
pytest -n 4     # Use 4 workers
```

## Test Database Setup

Integration tests require a PostgreSQL database with pgvector extension.

### Using Docker

```bash
docker run -d \
  --name cortx-test-db \
  -e POSTGRES_USER=cortx \
  -e POSTGRES_PASSWORD=cortx_dev_password \
  -e POSTGRES_DB=cortx_test \
  -p 5432:5432 \
  ankane/pgvector
```

### Environment Variables

Set test database URL:

```bash
export TEST_DATABASE_URL="postgresql://cortx:cortx_dev_password@localhost:5432/cortx_test"
```

## Test Coverage Goals

Target coverage: **>80%** across all modules

Current coverage by module:

- `app/chunking.py`: Unit tests for all functions
- `app/embeddings.py`: Unit tests for embedding generation
- `app/retrieval.py`: Unit and integration tests for retrieval
- `app/models.py`: Unit tests for all models
- `app/database.py`: Unit and integration tests
- `app/main.py`: Integration tests for all endpoints

## Test Categories

### Unit Tests (`-m unit`)

Fast, isolated tests with no external dependencies:

- Document chunking logic
- Embedding generation (mocked)
- Model validations
- Helper functions
- Data transformations

### Integration Tests (`-m integration`)

Tests requiring database and external services:

- API endpoints
- Database operations
- Retrieval queries
- End-to-end workflows

### Slow Tests (`-m slow`)

Tests that take longer to run:

- Large document processing
- Batch operations
- Performance tests

## Fixtures

Key fixtures available in `conftest.py`:

- `db_session`: Database session with automatic cleanup
- `client`: FastAPI test client
- `auth_headers`: Mock authentication headers
- `mock_embedding_model`: Mocked sentence transformer
- `sample_text`: Sample markdown document
- `sample_document`: Pre-created document in database
- `sample_chunks`: Pre-created chunks with embeddings
- `suite_document`: Suite-level document
- `module_document`: Module-level document
- `mock_ai_broker`: Mocked AI Broker responses

## Writing New Tests

### Example Unit Test

```python
import pytest
from app.chunking import chunk_text

@pytest.mark.unit
def test_chunk_text_basic():
    """Test basic text chunking."""
    text = "Sample text for chunking."
    chunks = chunk_text(text, chunk_size=100)

    assert len(chunks) > 0
    assert all(c.content for c in chunks)
```

### Example Integration Test

```python
import pytest

@pytest.mark.integration
def test_upload_document(client, mock_embedding_model):
    """Test document upload endpoint."""
    response = client.post(
        "/documents/upload",
        files={"file": ("test.txt", b"content", "text/plain")},
        data={"title": "Test", "level": "platform"}
    )

    assert response.status_code == 200
    assert "id" in response.json()
```

## Test Factories

Use factories to create test data:

```python
from tests.__utils__.factories import DocumentFactory, ChunkFactory

# Create a document
doc = DocumentFactory.create_platform(title="Test Document")

# Create chunks
chunks = ChunkFactory.create_batch(document_id=doc.id, count=5)
```

## Debugging Tests

### Verbose Output

```bash
pytest -vv
```

### Show Print Statements

```bash
pytest -s
```

### Stop on First Failure

```bash
pytest -x
```

### Run Last Failed Tests

```bash
pytest --lf
```

### Debug with PDB

```bash
pytest --pdb
```

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pytest --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Performance

### Test Execution Time

- Unit tests: ~5-10 seconds
- Integration tests: ~30-60 seconds
- Full suite: ~1-2 minutes

### Optimization Tips

1. Use `pytest-xdist` for parallel execution
2. Mark slow tests with `@pytest.mark.slow`
3. Use fixtures for expensive setup
4. Mock external services
5. Use in-memory databases for unit tests

## Troubleshoties

### Database Connection Errors

Ensure PostgreSQL is running and pgvector is installed:

```bash
docker ps  # Check if container is running
psql -h localhost -U cortx -d cortx_test -c "SELECT * FROM pg_extension;"
```

### Import Errors

Ensure app directory is in Python path:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Fixture Errors

Clear pytest cache:

```bash
pytest --cache-clear
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Descriptive Names**: Use clear, descriptive test names
3. **Arrange-Act-Assert**: Follow AAA pattern
4. **Single Assertion**: Test one thing per test (when practical)
5. **Fast Tests**: Keep unit tests fast (<1s each)
6. **Mock External Services**: Don't hit real APIs in tests
7. **Clean Up**: Use fixtures for setup/teardown
8. **Coverage**: Aim for >80% but focus on critical paths

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
