# CI/CD Setup Checklist

**Quick Reference for Activating CORTX Platform CI/CD Pipeline**

## Prerequisites

- [ ] GitHub repository access with admin permissions
- [ ] Codecov account (<https://codecov.io>)
- [ ] Python 3.11+ installed locally

## 1. GitHub Repository Setup

### Secrets Configuration

- [ ] Navigate to: `Settings > Secrets and variables > Actions`
- [ ] Add new repository secret:
  - Name: `CODECOV_TOKEN`
  - Value: [Get from codecov.io after signup]

### Branch Protection Rules

- [ ] Navigate to: `Settings > Branches > Branch protection rules`
- [ ] Add rule for `main` branch:
  - [ ] Require status checks to pass before merging
  - [ ] Required checks:
    - [ ] `test (ai-broker)` from test-all-services.yml
    - [ ] `test (compliance)` from test-all-services.yml
    - [ ] `test (gateway)` from test-all-services.yml
    - [ ] `test (identity)` from test-all-services.yml
    - [ ] `test (ledger)` from test-all-services.yml
    - [ ] `test (ocr)` from test-all-services.yml
    - [ ] `test (rag)` from test-all-services.yml
    - [ ] `test (validation)` from test-all-services.yml
    - [ ] `test (workflow)` from test-all-services.yml
    - [ ] `codecov/project`
    - [ ] `codecov/patch`

## 2. Codecov Setup

### Account Setup

- [ ] Visit <https://codecov.io>
- [ ] Sign up with GitHub account
- [ ] Add `sinergysolutionsllc` organization

### Repository Configuration

- [ ] Enable repository in Codecov dashboard
- [ ] Copy repository token
- [ ] Add token to GitHub secrets (see step 1)
- [ ] Install Codecov GitHub App:
  - [ ] Visit <https://github.com/apps/codecov>
  - [ ] Install on `sinergysolutionsllc` repository
  - [ ] Grant required permissions

### Verify Integration

- [ ] Trigger a test workflow run
- [ ] Check coverage appears in Codecov dashboard
- [ ] Verify PR comment functionality

## 3. Local Development Setup

### Install Pre-commit

```bash
cd /Users/michael/Development/sinergysolutionsllc

# Install pre-commit tool
pip install pre-commit

# Install git hooks
pre-commit install

# Run on all files (first time)
pre-commit run --all-files
```

### Verify Installation

```bash
# Check hooks are installed
pre-commit --version

# Test a commit
git add .
git commit -m "test: verify pre-commit hooks"
```

## 4. Service Verification

### Check Requirements Files

For each service, verify these files exist:

```bash
# Run this script to check all services
for service in ai-broker compliance gateway identity ledger ocr rag validation workflow; do
  echo "=== Checking $service ==="

  # Check requirements-dev.txt
  if [ -f "services/$service/requirements-dev.txt" ]; then
    echo "✅ requirements-dev.txt exists"
  else
    echo "❌ requirements-dev.txt missing"
  fi

  # Check pytest.ini or pyproject.toml
  if [ -f "services/$service/pytest.ini" ] || [ -f "services/$service/pyproject.toml" ]; then
    echo "✅ pytest config exists"
  else
    echo "⚠️  pytest config missing"
  fi

  # Check tests directory
  if [ -d "services/$service/tests" ]; then
    echo "✅ tests/ directory exists"
  else
    echo "❌ tests/ directory missing"
  fi

  echo ""
done
```

### Create Missing Files

If any service is missing `requirements-dev.txt`:

```bash
# Create requirements-dev.txt for a service
cat > services/{SERVICE_NAME}/requirements-dev.txt << 'EOF'
# Testing Framework
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

# Coverage Reporting
coverage[toml]==7.6.0

# Type Stubs
types-requests==2.32.0
EOF
```

## 5. Test Workflows

### Trigger Manual Test Run

```bash
# Trigger test-all-services workflow
gh workflow run test-all-services.yml

# Check workflow status
gh run list --workflow=test-all-services.yml

# View workflow logs
gh run view --web
```

### Test Individual Service

```bash
# Trigger specific service test
gh workflow run test-gateway.yml

# Or push a commit to trigger automatically
git commit --allow-empty -m "test: trigger CI/CD pipeline"
git push origin main
```

### Verify Results

- [ ] All workflows appear in Actions tab
- [ ] Workflows run successfully
- [ ] Coverage reports generated
- [ ] Codecov receives coverage data
- [ ] PR comments work (test with a PR)

## 6. Service-by-Service Testing

Run tests locally for each service:

```bash
# Test ai-broker
cd services/ai-broker
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ --cov=app -v

# Test compliance
cd ../compliance
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ --cov=app -v

# Test gateway
cd ../gateway
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ --cov=app -v

# Test identity
cd ../identity
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ --cov=app -v

# Test ledger
cd ../ledger
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ --cov=app -v

# Test ocr
cd ../ocr
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ --cov=app -v

# Test rag
cd ../rag
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ --cov=app -v

# Test validation
cd ../validation
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ --cov=app -v

# Test workflow
cd ../workflow
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ --cov=app -v
```

## 7. Documentation Review

- [ ] Read full CI/CD setup guide: `docs/operations/CI_CD_SETUP.md`
- [ ] Review implementation summary: `CI_CD_IMPLEMENTATION_SUMMARY.md`
- [ ] Review test plan: `docs/tracking/CORTX_PLATFORM_QUALITY_HARDENING_TEST_PLAN.md`
- [ ] Review QA patterns: `.claude/agents/quality-assurance-lead.md`

## 8. Team Communication

### Notify Team

- [ ] Share CI/CD documentation links
- [ ] Explain coverage requirements (80% minimum)
- [ ] Demonstrate pre-commit hook usage
- [ ] Schedule training session if needed

### Update README

- [ ] Add CI/CD badge to main README.md
- [ ] Link to CI/CD documentation
- [ ] Add "Testing" section with quick start

Example badge:

```markdown
[![Tests](https://github.com/sinergysolutionsllc/sinergysolutionsllc/actions/workflows/test-all-services.yml/badge.svg)](https://github.com/sinergysolutionsllc/sinergysolutionsllc/actions/workflows/test-all-services.yml)
[![codecov](https://codecov.io/gh/sinergysolutionsllc/sinergysolutionsllc/branch/main/graph/badge.svg)](https://codecov.io/gh/sinergysolutionsllc/sinergysolutionsllc)
```

## 9. Monitoring Setup

### GitHub Actions

- [ ] Enable email notifications for workflow failures
- [ ] Set up Slack integration (optional)
- [ ] Configure workflow approval requirements (optional)

### Codecov

- [ ] Set up email notifications
- [ ] Configure Slack integration (optional)
- [ ] Enable weekly coverage reports

### Scheduled Checks

- [ ] Verify daily scheduled workflow runs
- [ ] Review coverage trends weekly
- [ ] Address any flaky tests

## 10. Troubleshooting

### If workflows fail

1. Check workflow logs in Actions tab
2. Verify all required files exist
3. Test locally first: `pytest tests/ --cov=app -v`
4. Review error messages carefully
5. Consult `docs/operations/CI_CD_SETUP.md` troubleshooting section

### If coverage is below 80%

1. Run: `pytest --cov=app --cov-report=html`
2. Open: `htmlcov/index.html`
3. Identify untested lines
4. Add tests to increase coverage
5. Verify locally before pushing

### If pre-commit hooks fail

1. Run: `pre-commit run --all-files`
2. Fix reported issues
3. Re-stage files: `git add .`
4. Commit again
5. Use `--no-verify` only for emergencies

## 11. Final Verification

### Checklist

- [ ] All 10 workflow files created
- [ ] Pre-commit hooks installed and working
- [ ] Codecov integration active
- [ ] Branch protection rules configured
- [ ] All services have tests passing
- [ ] Coverage reports generating
- [ ] Team members notified
- [ ] Documentation accessible

### Test Complete Flow

1. Create feature branch
2. Make code change
3. Add tests (maintain >80% coverage)
4. Run pre-commit hooks
5. Push branch
6. Create PR
7. Verify CI passes
8. Check coverage report in PR
9. Merge when all checks pass

## Support

For issues or questions:

1. Check workflow logs in GitHub Actions
2. Review CI/CD documentation
3. Consult Quality Assurance Lead
4. Create issue in repository

## Quick Links

- **Workflows**: `.github/workflows/test-*.yml`
- **Pre-commit Config**: `.pre-commit-config.yaml`
- **Codecov Config**: `codecov.yml`
- **Documentation**: `docs/operations/CI_CD_SETUP.md`
- **Summary**: `CI_CD_IMPLEMENTATION_SUMMARY.md`

---

**Last Updated**: 2025-10-08
**Version**: 1.0.0

Once all items are checked, your CI/CD pipeline is fully operational!
