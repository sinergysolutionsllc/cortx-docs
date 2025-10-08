# CI/CD Pipeline Setup - CORTX Platform

**Date**: 2025-10-08
**Owner**: GCP Deployment Ops
**Status**: Active

## Overview

This document describes the automated CI/CD pipeline configuration for test execution and coverage reporting across all CORTX platform services. The pipeline ensures code quality through automated testing, linting, type checking, and coverage reporting.

## Architecture

### Pipeline Structure

```
.github/workflows/
├── test-ai-broker.yml       # AI Broker service tests
├── test-compliance.yml      # Compliance service tests
├── test-gateway.yml         # Gateway service tests
├── test-identity.yml        # Identity service tests
├── test-ledger.yml          # Ledger service tests
├── test-ocr.yml             # OCR service tests
├── test-rag.yml             # RAG service tests
├── test-validation.yml      # Validation service tests
├── test-workflow.yml        # Workflow service tests
└── test-all-services.yml    # Orchestrator for all services
```

### Quality Gates

1. **Linting**: Ruff checks for code quality and style violations
2. **Type Checking**: Mypy verifies type annotations
3. **Formatting**: Black ensures consistent code formatting
4. **Testing**: Pytest runs unit and integration tests
5. **Coverage**: 80% minimum coverage threshold enforced
6. **Security**: Bandit scans for security vulnerabilities (pre-commit)

## Service-Specific Workflows

Each service has a dedicated workflow file that:

### Triggers

- **Push to main**: Runs tests on main branch commits
- **Pull requests**: Runs tests on PRs to main branch
- **Path filtering**: Only triggers when service files change

### Pipeline Steps

1. **Checkout code**: Clone repository
2. **Setup Python 3.11**: Configure Python environment with pip cache
3. **Install dependencies**: Install requirements.txt + requirements-dev.txt
4. **Run linting**: Execute ruff for code quality checks
5. **Run type checking**: Execute mypy for type validation
6. **Run tests**: Execute pytest with coverage
7. **Upload to Codecov**: Submit coverage data
8. **Upload artifacts**: Store coverage reports (30-day retention)
9. **Check threshold**: Fail if coverage below 80%

### Example Workflow

```yaml
name: Test Gateway Service

on:
  push:
    branches: [ main ]
    paths:
      - 'services/gateway/**'
      - '.github/workflows/test-gateway.yml'
  pull_request:
    branches: [ main ]
    paths:
      - 'services/gateway/**'
      - '.github/workflows/test-gateway.yml'

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: services/gateway

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests with pytest
        run: |
          pytest tests/ \
            --cov=app \
            --cov-report=xml \
            --cov-fail-under=80 \
            -v
```

## Test-All-Services Workflow

The `test-all-services.yml` orchestrates testing across all services:

### Features

1. **Matrix Strategy**: Runs all 9 services in parallel
2. **Aggregated Reporting**: Combines coverage from all services
3. **PR Comments**: Posts coverage summary on pull requests
4. **GitHub Summary**: Displays results in workflow UI
5. **Quality Gate**: Fails if any service below threshold
6. **Scheduled Runs**: Daily execution at 6 AM UTC

### Triggers

- **Push to main**: Any service file change
- **Pull requests**: Any service file change
- **Schedule**: Daily at 6 AM UTC
- **Manual**: Via workflow_dispatch

### Aggregated Report Format

```markdown
# CORTX Platform Test Coverage Report

Generated on: 2025-10-08 12:00:00 UTC

## Service Coverage Summary

| Service | Coverage | Status |
|---------|----------|--------|
| ai-broker | 85% | ✅ Pass |
| compliance | 82% | ✅ Pass |
| gateway | 87% | ✅ Pass |
| identity | 84% | ✅ Pass |
| ledger | 81% | ✅ Pass |
| ocr | 83% | ✅ Pass |
| rag | 79% | ❌ Below Threshold |
| validation | 86% | ✅ Pass |
| workflow | 88% | ✅ Pass |

## Overall Platform Coverage

- **Average Coverage**: 84%
- **Target Coverage**: 80%
- **Status**: ✅ Platform meets quality threshold
```

## Coverage Reporting

### Codecov Integration

Coverage data is uploaded to Codecov for tracking and visualization.

**Configuration**: `/codecov.yml`

#### Key Features

1. **Service Flags**: Individual tracking per service
2. **Component Management**: Separate status checks per service
3. **PR Comments**: Automated coverage reports on PRs
4. **Coverage Targets**: 80% minimum for all services
5. **Carryforward**: Preserve coverage between runs

#### Setup Requirements

1. Add `CODECOV_TOKEN` to GitHub repository secrets
2. Install Codecov GitHub app
3. Configure branch protection rules

### Artifacts

Coverage artifacts are stored for 30 days:

- `coverage.xml`: Machine-readable coverage data
- `htmlcov/`: Human-readable HTML reports

**Access**: Download from workflow run page

## Pre-Commit Hooks

Local development quality checks before commit.

**Configuration**: `/.pre-commit-config.yaml`

### Hooks Included

1. **black**: Python code formatting (line-length: 100)
2. **ruff**: Python linting with auto-fix
3. **mypy**: Python type checking
4. **isort**: Import sorting (black-compatible)
5. **bandit**: Security vulnerability scanning
6. **trailing-whitespace**: Remove trailing spaces
7. **end-of-file-fixer**: Ensure newline at EOF
8. **check-yaml**: YAML syntax validation
9. **check-json**: JSON syntax validation
10. **check-toml**: TOML syntax validation
11. **check-added-large-files**: Prevent large file commits
12. **check-merge-conflict**: Detect merge conflict markers
13. **detect-private-key**: Prevent credential leaks
14. **markdownlint**: Markdown linting and formatting
15. **hadolint**: Dockerfile linting

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### Usage

Hooks run automatically on `git commit`:

```bash
# Commit triggers pre-commit hooks
git commit -m "feat: add new feature"

# Skip hooks (not recommended)
git commit -m "feat: add new feature" --no-verify
```

### Configuration

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.8.0
    hooks:
      - id: black
        args: [--line-length=100]

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
```

## Service Requirements

Each service must have:

### File Structure

```
services/{service}/
├── app/                    # Application code
├── tests/                  # Test code
│   ├── __init__.py
│   ├── conftest.py        # Pytest fixtures
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── pyproject.toml         # Python project config
├── pytest.ini             # Pytest configuration
└── .coveragerc            # Coverage configuration
```

### Dependencies (requirements-dev.txt)

```txt
# Testing
pytest==8.3.2
pytest-asyncio>=0.21.0
pytest-cov==5.0.0
pytest-mock==3.14.0

# HTTP Testing
httpx==0.27.2

# Code Quality
ruff==0.5.6
mypy==1.11.2
black==24.8.0

# Coverage
coverage[toml]==7.6.0
```

### Pytest Configuration (pytest.ini)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=app
    --cov-report=term-missing
    --cov-report=xml
    --cov-report=html
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow-running tests
asyncio_mode = auto
```

### Coverage Configuration (.coveragerc)

```ini
[run]
source = app
omit =
    */tests/*
    */conftest.py
    */__pycache__/*
    */venv/*
    */.venv/*

[report]
precision = 2
show_missing = True
skip_covered = False
fail_under = 80

[html]
directory = htmlcov
```

### Ruff Configuration (pyproject.toml)

```toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
ignore = []
exclude = [
    ".git",
    "__pycache__",
    ".pytest_cache",
    "htmlcov",
    "*.egg-info",
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
"tests/*" = ["S101"]
```

## Quality Metrics

### Coverage Targets

| Component | Target | Threshold |
|-----------|--------|-----------|
| All Services | 80% | Hard Fail |
| Individual Service | 80% | Hard Fail |
| New Code (Patch) | 80% | Hard Fail |
| Platform Average | 80% | Soft Warn |

### Test Execution

- **Parallel Execution**: All 9 services run concurrently
- **Test Isolation**: Each service runs in separate job
- **Fast Feedback**: ~5-10 minutes per service
- **Daily Validation**: Scheduled runs detect regressions

### Success Criteria

A service passes CI if:

1. ✅ All tests pass
2. ✅ Coverage ≥ 80%
3. ✅ Linting passes (or warnings only)
4. ✅ Type checking passes (or warnings only)
5. ✅ No security vulnerabilities (critical/high)

## CI/CD Best Practices

### Development Workflow

1. **Create feature branch**

   ```bash
   git checkout -b feature/new-feature
   ```

2. **Write tests first** (TDD)

   ```bash
   # Write failing test
   pytest tests/test_new_feature.py -v
   ```

3. **Implement feature**

   ```python
   # Implement code to pass test
   ```

4. **Run pre-commit hooks**

   ```bash
   pre-commit run --all-files
   ```

5. **Run local tests**

   ```bash
   cd services/gateway
   pytest tests/ --cov=app -v
   ```

6. **Push and create PR**

   ```bash
   git push origin feature/new-feature
   # Create PR via GitHub UI
   ```

7. **Review CI results**
   - Check workflow status
   - Review coverage report
   - Address any failures

### Writing Quality Tests

#### Unit Test Example

```python
# tests/unit/test_service.py
import pytest
from app.services.workflow_service import WorkflowService

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_workflow_success(mocker):
    """Test successful workflow creation with mocked dependencies"""
    # Arrange
    mock_repo = mocker.Mock()
    service = WorkflowService(repository=mock_repo)

    # Act
    result = await service.create_workflow(
        pack_id="test.pack",
        version="1.0.0",
        tenant_id="tenant1"
    )

    # Assert
    assert result.pack_id == "test.pack"
    assert result.status == "pending"
    mock_repo.create.assert_called_once()
```

#### Integration Test Example

```python
# tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient

@pytest.mark.integration
def test_create_workflow_endpoint(client: TestClient, auth_headers: dict):
    """Test POST /v1/workflows endpoint"""
    # Arrange
    payload = {
        "pack_id": "test.pack",
        "version": "1.0.0",
        "input_data": {"key": "value"}
    }

    # Act
    response = client.post("/v1/workflows", json=payload, headers=auth_headers)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["pack_id"] == "test.pack"
    assert "id" in data
```

### Maintaining Coverage

#### Coverage by Test Type

```
Unit Tests:        60-70% coverage (fast, isolated)
Integration Tests: 20-25% coverage (API endpoints)
E2E Tests:         5-10% coverage (critical paths)
Total:             >80% coverage
```

#### Strategies

1. **Test Public APIs**: Focus on public methods and endpoints
2. **Mock External Dependencies**: Isolate code under test
3. **Test Edge Cases**: Cover error conditions and boundaries
4. **Avoid Testing Implementation**: Test behavior, not internals
5. **Refactor for Testability**: Keep functions small and focused

## Troubleshooting

### Common Issues

#### Coverage Below 80%

**Symptoms**: CI fails with coverage error

**Solutions**:

1. Identify untested code: `coverage report --show-missing`
2. Add unit tests for uncovered lines
3. Review test quality vs. quantity
4. Consider if code is testable

#### Flaky Tests

**Symptoms**: Tests pass/fail inconsistently

**Solutions**:

1. Add `pytest-xdist` for test isolation
2. Use `freezegun` for time-dependent tests
3. Mock external API calls with `respx`
4. Fix race conditions in async tests
5. Use `pytest.mark.flaky` for known issues

#### Slow Tests

**Symptoms**: Tests take >10 minutes

**Solutions**:

1. Use `pytest-xdist` for parallel execution
2. Mark slow tests: `@pytest.mark.slow`
3. Skip slow tests in CI: `pytest -m "not slow"`
4. Optimize database setup in fixtures
5. Use in-memory databases for tests

#### Type Checking Errors

**Symptoms**: mypy fails in CI

**Solutions**:

1. Add type hints to function signatures
2. Install type stubs: `pip install types-*`
3. Use `# type: ignore` for third-party issues
4. Configure mypy.ini for specific ignores

## Monitoring and Maintenance

### Weekly Tasks

- [ ] Review coverage trends in Codecov
- [ ] Address any failing scheduled runs
- [ ] Update dependencies via Dependabot
- [ ] Review and merge pre-commit hook updates

### Monthly Tasks

- [ ] Audit test execution times
- [ ] Review and update coverage targets
- [ ] Analyze flaky test patterns
- [ ] Update CI/CD documentation

### Quarterly Tasks

- [ ] Review test quality and coverage
- [ ] Update testing frameworks and tools
- [ ] Conduct CI/CD pipeline audit
- [ ] Review and optimize GitHub Actions usage

## Security Considerations

### Secrets Management

1. **CODECOV_TOKEN**: Stored in GitHub repository secrets
2. **GITHUB_TOKEN**: Automatically provided by GitHub Actions
3. **Never commit**: API keys, passwords, or tokens

### Dependency Security

1. **Dependabot**: Automated dependency updates
2. **Bandit**: Security vulnerability scanning
3. **Safety**: Check dependencies for known vulnerabilities
4. **SBOM**: Generate Software Bill of Materials

## References

### Documentation

- [Test Plan](/Users/michael/Development/sinergysolutionsllc/docs/tracking/CORTX_PLATFORM_QUALITY_HARDENING_TEST_PLAN.md)
- [Quality Assurance Guide](/.claude/agents/quality-assurance-lead.md)
- [pytest Documentation](https://docs.pytest.org/)
- [Codecov Documentation](https://docs.codecov.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pre-commit Documentation](https://pre-commit.com/)

### Related Files

- Workflow definitions: `/.github/workflows/test-*.yml`
- Pre-commit config: `/.pre-commit-config.yaml`
- Codecov config: `/codecov.yml`
- Service READMEs: `/services/*/README.md`

## Support

For issues with CI/CD pipelines:

1. Check workflow logs in GitHub Actions
2. Review this documentation
3. Consult Quality Assurance Lead
4. Create issue in repository

---

**Last Updated**: 2025-10-08
**Next Review**: 2025-11-08
**Version**: 1.0.0
