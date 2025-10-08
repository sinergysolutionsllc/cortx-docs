# Compliance Service Test Suite

Comprehensive testing documentation for the PropVerify Compliance Service.

## Test Structure

```
tests/
├── __init__.py                   # Test package initialization
├── conftest.py                   # Pytest fixtures and configuration
├── README.md                     # This file
├── __utils__/                    # Test utilities
│   ├── __init__.py
│   ├── factories.py              # Test data factories
│   └── helpers.py                # Test helper functions
├── unit/                         # Unit tests
│   ├── __init__.py
│   ├── test_event_logging.py    # Event logging logic tests
│   ├── test_report_generation.py # Report generation tests
│   └── test_event_filtering.py  # Filtering and querying tests
└── integration/                  # Integration tests
    ├── __init__.py
    ├── test_post_compliance_events.py  # POST endpoint tests
    ├── test_get_compliance_events.py   # GET events endpoint tests
    ├── test_compliance_report.py       # Report endpoint tests
    ├── test_authentication.py          # Auth and authz tests
    └── test_error_handling.py          # Error handling tests
```

## Running Tests

### Install Dependencies

```bash
# Install test dependencies
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing --cov-report=html

# Run with verbose output
pytest -v

# Run parallel tests (faster)
pytest -n auto
```

### Run Specific Test Types

```bash
# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run tests by marker
pytest -m unit
pytest -m integration
pytest -m auth
pytest -m compliance
```

### Run Specific Test Files

```bash
# Run specific test file
pytest tests/unit/test_event_logging.py -v

# Run specific test class
pytest tests/unit/test_event_logging.py::TestEventLogging -v

# Run specific test function
pytest tests/unit/test_event_logging.py::TestEventLogging::test_create_event_with_all_fields -v
```

## Test Coverage

### Coverage Targets

- **Unit Tests**: >80% line coverage
- **Integration Tests**: All API endpoints covered
- **Edge Cases**: Error handling and validation

### Generate Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage by Module

```bash
# Show coverage by module
pytest --cov=app --cov-report=term-missing
```

## Test Categories

### Unit Tests (tests/unit/)

**test_event_logging.py**

- Event creation with all fields
- Event creation with minimal fields
- Unique event ID generation
- Timestamp generation
- Data hash generation
- Correlation ID generation
- Event type factories (audit, violation, regulatory, workflow)
- Batch event creation
- Severity level mapping
- Event type mapping
- Data integrity preservation

**test_report_generation.py**

- Basic report creation
- Time range handling
- Event type breakdown
- Severity breakdown
- Compliance status calculation
- Event aggregation
- Time range filtering
- Report metrics calculations
- Time series event generation

**test_event_filtering.py**

- Filter by event type
- Filter by severity
- Filter by time range
- Event sorting (timestamp)
- Combined filter criteria
- Pagination logic
- Event limiting
- Complex query scenarios

### Integration Tests (tests/integration/)

**test_post_compliance_events.py** (30+ test cases)

- Log compliance event success
- Log minimal event
- Log audit events
- Log violation events
- Log regulatory events
- Log workflow events
- Log critical events
- Complex nested data
- Empty data handling
- Missing required fields
- Invalid data types
- Sequential event logging
- Data integrity preservation
- All severity levels

**test_get_compliance_events.py** (20+ test cases)

- Get all events
- Get empty event list
- Get events after posting
- Timestamp sorting
- Filter by type
- Filter by non-existent type
- Limit handling
- Default limit
- Zero limit
- Invalid limit
- Response structure validation
- Count matching
- Combined filters
- Data preservation

**test_compliance_report.py** (25+ test cases)

- Generate basic report
- Report with no events
- Default time range (24 hours)
- Custom time range
- Event type breakdown
- Severity breakdown
- Compliance status (compliant)
- Compliance status (needs review)
- Total events count
- Time range filtering
- Admin role requirement
- Correlation ID
- Generation timestamp
- Multiple event types
- Breakdown sum validation

**test_authentication.py** (15+ test cases)

- POST requires auth
- GET requires auth
- Report requires auth
- Valid authentication
- Admin role requirement
- Invalid token rejection
- Malformed auth header
- Expired token rejection
- Health endpoints (no auth required)
- CORS and security headers

**test_error_handling.py** (25+ test cases)

- Missing required fields
- Invalid data types
- Malformed JSON
- Extra fields handling
- Invalid query parameters
- Wrong HTTP methods
- Non-existent endpoints
- Null values
- Special characters
- Unicode handling
- Very long descriptions
- Deeply nested data
- Large arrays
- Concurrent access
- Edge cases and boundary conditions

## Test Fixtures

### Available Fixtures (conftest.py)

**Application Fixtures**

- `test_app`: FastAPI test application
- `client`: Test client for HTTP requests

**Authentication Fixtures**

- `create_test_token`: Factory for creating JWT tokens
- `auth_headers`: Standard authentication headers
- `admin_auth_headers`: Admin role authentication headers
- `write_auth_headers`: Write role authentication headers

**Data Fixtures**

- `sample_compliance_event`: Sample audit event
- `sample_compliance_event_critical`: Sample critical event
- `sample_regulatory_event`: Sample regulatory event
- `sample_workflow_event`: Sample workflow event
- `multiple_compliance_events`: Multiple events for testing
- `populated_compliance_events`: Pre-populated event storage

**Utility Fixtures**

- `mock_cortex_client`: Mock CortexClient
- `mock_correlation_id`: Mock correlation ID
- `mock_request`: Mock FastAPI Request
- `time_range`: Time range for testing
- `reset_compliance_events`: Auto-reset between tests

## Test Factories

### ComplianceEventFactory

```python
from tests.__utils__.factories import ComplianceEventFactory

# Create event with defaults
event = ComplianceEventFactory.create_event()

# Create specific event types
audit = ComplianceEventFactory.create_audit_event()
violation = ComplianceEventFactory.create_violation_event()
regulatory = ComplianceEventFactory.create_regulatory_event()
workflow = ComplianceEventFactory.create_workflow_event()
critical = ComplianceEventFactory.create_critical_event()

# Create batch of events
events = ComplianceEventFactory.create_batch(count=10)
```

### ComplianceReportFactory

```python
from tests.__utils__.factories import ComplianceReportFactory

# Create report with defaults
report = ComplianceReportFactory.create_report()

# Create compliant report
compliant = ComplianceReportFactory.create_compliant_report()

# Create non-compliant report
non_compliant = ComplianceReportFactory.create_non_compliant_report()
```

### ComplianceEventRequestFactory

```python
from tests.__utils__.factories import ComplianceEventRequestFactory

# Create request payload
request = ComplianceEventRequestFactory.create_request()

# Create minimal request
minimal = ComplianceEventRequestFactory.create_minimal_request()

# Create invalid request (for error testing)
invalid = ComplianceEventRequestFactory.create_invalid_request()
```

## Test Helpers

### Available Helper Functions

```python
from tests.__utils__.helpers import (
    assert_compliance_event_structure,
    assert_compliance_report_structure,
    assert_event_response_structure,
    count_events_by_type,
    count_events_by_severity,
    filter_events_by_type,
    filter_events_by_time_range,
    filter_events_by_severity,
    calculate_compliance_status,
    sort_events_by_timestamp,
    validate_event_hash,
    validate_correlation_id
)
```

## Compliance-Specific Testing Considerations

### Audit Trail Integrity

- All events have unique IDs
- Events are timestamped
- Data integrity is verified with hashes
- Correlation IDs for request tracing

### Regulatory Compliance

- HIPAA data access logging
- FedRAMP audit requirements
- SOC 2 compliance tracking
- NIST 800-53 control validation

### Security Testing

- Authentication required (when enabled)
- Role-based access control (admin for reports)
- Data validation and sanitization
- Error handling without information leakage

### Data Retention

- Time-based event filtering
- Report generation for audit periods
- Event aggregation and statistics

## Continuous Integration

### GitHub Actions

Tests run automatically on:

- Pull requests
- Pushes to main branch
- Nightly scheduled runs

### CI Configuration

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pytest --cov=app --cov-report=xml --cov-report=term
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Test Maintenance

### Adding New Tests

1. Identify the component/feature to test
2. Choose appropriate test type (unit vs integration)
3. Create test file in appropriate directory
4. Add fixtures to conftest.py if needed
5. Write test cases following existing patterns
6. Verify coverage with `pytest --cov`

### Test Naming Conventions

- Test files: `test_<module_name>.py`
- Test classes: `Test<FeatureName>`
- Test functions: `test_<specific_behavior>`

Example:

```python
class TestEventLogging:
    def test_create_event_with_all_fields(self):
        ...
```

### Markers

Available pytest markers:

- `@pytest.mark.unit`: Unit test
- `@pytest.mark.integration`: Integration test
- `@pytest.mark.auth`: Authentication test
- `@pytest.mark.compliance`: Compliance-specific test
- `@pytest.mark.slow`: Slow-running test

## Troubleshooting

### Common Issues

**Import Errors**

```bash
# Ensure you're in the service root directory
cd /path/to/services/compliance

# Install in development mode
pip install -e .
```

**Auth-Required Tests Skipping**

```bash
# Set environment variable to enable auth tests
export REQUIRE_AUTH=true
pytest tests/integration/test_authentication.py
```

**Coverage Not Including All Files**

```bash
# Ensure coverage is measuring the right directory
pytest --cov=app --cov-report=term-missing
```

## Test Statistics

- **Total Test Files**: 8
- **Total Test Cases**: 130+
- **Unit Tests**: 60+
- **Integration Tests**: 70+
- **Coverage Target**: >80%

## Next Steps

1. Run full test suite: `pytest -v`
2. Check coverage: `pytest --cov=app --cov-report=html`
3. Review coverage report: `open htmlcov/index.html`
4. Address any gaps in coverage
5. Add tests for new features

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Quality Assurance Lead Agent](/.claude/agents/quality-assurance-lead.md)
