# CORTX Ledger Service Tests

Comprehensive test suite for the CORTX Ledger Service, following the quality-assurance-lead patterns.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and test configuration
├── unit/                    # Unit tests
│   ├── test_hash_utils.py   # Hash generation and verification tests
│   ├── test_models.py       # Database model tests
│   └── test_database.py     # Database utilities tests
└── integration/             # Integration tests (API endpoints)
    ├── test_append_endpoint.py
    ├── test_verify_endpoint.py
    ├── test_events_endpoint.py
    ├── test_export_endpoint.py
    └── test_health_endpoints.py
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
pytest tests/unit/
```

### Run Integration Tests Only

```bash
pytest tests/integration/
```

### Run with Coverage Report

```bash
pytest --cov=app --cov-report=html
```

View coverage report:

```bash
open htmlcov/index.html
```

### Run Specific Test File

```bash
pytest tests/unit/test_hash_utils.py
```

### Run Specific Test

```bash
pytest tests/unit/test_hash_utils.py::TestSHA256Hex::test_hash_string
```

## Test Coverage

The test suite covers:

- **Hash utilities**: SHA-256 hashing, content hashing, chain hashing, genesis hash
- **Database models**: LedgerEvent model, JSONB storage, hash chain fields
- **Database utilities**: Session management, connection handling
- **API endpoints**:
  - POST /append - Appending events to the ledger
  - GET /verify - Verifying chain integrity
  - GET /events - Querying events with pagination and filtering
  - GET /export - Exporting events as CSV
  - GET /healthz - Health check
  - GET /readyz - Readiness check

## Key Test Patterns

### Blockchain/Ledger-Specific Tests

1. **Hash Chain Integrity**
   - Verifies that each event correctly links to the previous event
   - Tests genesis event points to GENESIS_HASH
   - Validates chain hash computation

2. **Tamper Detection**
   - Tests detecting modified event data
   - Tests detecting broken chain links
   - Tests detecting invalid hash values

3. **Multi-Tenant Isolation**
   - Verifies events are isolated by tenant_id
   - Tests that each tenant has independent chains

4. **Chronological Ordering**
   - Tests events maintain creation order
   - Verifies chain verification processes events in order

### Fixtures

The `conftest.py` provides comprehensive fixtures:

- `db_session`: Database session for each test (auto-rollback)
- `client`: FastAPI test client
- `ledger_event`: Single event fixture
- `ledger_chain`: Chain of 5 events for testing
- `multi_tenant_events`: Events for multiple tenants
- `tampered_event`: Event with tampered data for detection tests
- `sample_event_data`: Sample event data dictionary
- `sample_event_request`: Complete request payload

## Test Metrics

- **Total test files**: 8
- **Unit test modules**: 3
- **Integration test modules**: 5
- **Test coverage target**: >80%

## Best Practices

1. **Use fixtures**: Leverage pytest fixtures for test data setup
2. **Test isolation**: Each test is independent (auto-rollback)
3. **Clear naming**: Test names describe what they verify
4. **AAA pattern**: Arrange, Act, Assert
5. **Edge cases**: Test boundary conditions, empty data, errors
6. **Happy path + errors**: Test both success and failure scenarios

## Continuous Integration

Tests run automatically on:

- Every pull request
- Every commit to main branch
- Nightly builds

Required:

- All tests must pass
- Coverage must be >80%
- No security vulnerabilities
