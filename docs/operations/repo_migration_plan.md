# CORTX Repository Migration Plan

**Date:** 2025-10-08
**Tech Lead Architect:** AI Agent
**Status:** Ready for Execution
**Reference:** repo_target_map.yml

---

## Executive Summary

This plan migrates the current workspace from a **hybrid monorepo** structure (cortx-docs with embedded service code) to a **clean multi-repo architecture** per REPO_INSTRUCTION.md. The migration preserves git history, establishes independent service repos, and creates proper separation between platform services, suites, packs, and documentation.

**Key Objectives:**

1. Extract 9 service implementations from `/services/` to individual repos
2. Clean up cortx-docs to be documentation-only
3. Create cortx-ci and cortx-infra repositories
4. Establish reusable CI/CD workflows
5. Maintain zero downtime for development

---

## Current State Analysis

### What We Have

```
/Users/michael/Development/sinergysolutionsllc/ (cortx-docs repo)
├── services/                    ❌ Service implementations (wrong location)
│   ├── gateway/app/
│   ├── identity/app/
│   └── ... (9 services with code + tests)
├── docs/                        ✅ Documentation (correct)
├── cortx-platform/              ⚠️  Cloned repo (only has gateway)
├── cortx-sdks/                  ✅ Cloned repo (separate)
├── cortx-packs/                 ✅ Cloned repo (separate)
├── cortx-designer/              ✅ Cloned repo (separate)
├── cortx-e2e/                   ✅ Cloned repo (separate)
├── fedsuite/                    ✅ Cloned repo (separate)
├── corpsuite/                   ✅ Cloned repo (separate)
├── medsuite/                    ✅ Cloned repo (separate)
└── govsuite/                    ✅ Cloned repo (separate)
```

### The Problem

**Service code is in cortx-docs**, violating the architecture:

- Per `services/README.md` (before quality hardening): "**DO NOT** add service implementation code to this directory"
- Per REPO_INSTRUCTION.md: cortx-docs should be "Public portal repo. **No service code here**"

**Root Cause:** During quality hardening (commit 8b77110), service implementations + tests were added to cortx-docs/services/ instead of individual repos.

---

## Target State

### What We Want

```
Organization: sinergysolutionsllc/

├── cortx-gateway/               ✅ Individual service repo
│   ├── app/
│   ├── tests/
│   ├── openapi/
│   ├── infra/Dockerfile
│   └── .github/workflows/ci.yml

├── cortx-identity/              ✅ Individual service repo
├── cortx-validation/            ✅ Individual service repo
├── cortx-workflow/              ✅ Individual service repo
├── cortx-compliance/            ✅ Individual service repo
├── cortx-ai-broker/             ✅ Individual service repo
├── cortx-rag/                   ✅ Individual service repo
├── cortx-ocr/                   ✅ Individual service repo
├── cortx-ledger/                ✅ Individual service repo

├── cortx-docs/                  ✅ Documentation only
│   ├── docs/
│   ├── docs/services/           # Service docs (no code)
│   ├── mkdocs.yml
│   └── scripts/sync_openapi.sh

├── cortx-ci/                    ✅ Reusable CI workflows
├── cortx-infra/                 ✅ Terraform + Helm
├── cortx-sdks/                  ✅ Client libraries
├── cortx-packs/                 ✅ RulePacks + WorkflowPacks
├── cortx-designer/              ✅ Visual builder
├── cortx-e2e/                   ✅ Integration tests
└── [suites]/                    ✅ Domain applications
```

---

## Migration Strategy

### Phase-by-Phase Approach

We'll use a **phased, verifiable migration** to minimize risk:

1. **Create new service repos** (empty, with proper structure)
2. **Copy service code** from cortx-docs/services/ to new repos
3. **Add CI/CD** to each service repo
4. **Verify** each service builds and tests pass
5. **Clean up** cortx-docs after all services verified
6. **Final cutover** once all green

### Why Not Git Subtree Split?

**Decision:** Use **copy + git history reference** instead of git subtree split

**Reasoning:**

1. Service code was only added in 1 commit (8b77110)
2. No meaningful history to preserve (all added at once)
3. Simpler and safer than complex git history surgery
4. Can reference original commit in new repos

**Alternative if needed:** If stakeholders require preserved history, we can use git filter-repo post-migration.

---

## Detailed Migration Steps

### Pre-Flight Checklist

```bash
# 1. Create backup branch
cd /Users/michael/Development/sinergysolutionsllc
git checkout -b pre-migration-backup-2025-10-08
git push origin pre-migration-backup-2025-10-08

# 2. Return to main
git checkout main

# 3. Verify all existing repos are clean
for repo in cortx-*/  fedsuite/ corpsuite/ medsuite/ govsuite/; do
  echo "=== $repo ==="
  cd "$repo"
  git status --short
  cd ..
done

# 4. Verify we have org admin access
gh auth status
gh repo list sinergysolutionsllc --limit 5
```

---

### Step 1: Create cortx-ci Repository

**Purpose:** Reusable CI/CD workflows for all repos

```bash
# Create repo
gh repo create sinergysolutionsllc/cortx-ci \
  --public \
  --description "CORTX reusable CI/CD workflows" \
  --clone

cd cortx-ci

# Create structure
mkdir -p .github/workflows

# Add README
cat > README.md <<'EOF'
# CORTX CI/CD Workflows

Reusable GitHub Actions workflows for the CORTX platform.

## Workflows

- `reusable-python-service.yml` - Python/FastAPI services
- `reusable-node-frontend.yml` - Next.js/React frontends
- `reusable-openapi-publish.yml` - OpenAPI spec validation and publishing
- `reusable-docker-build-scan.yml` - Docker build + Trivy scan
- `reusable-helm-deploy.yml` - Helm deployment
- `reusable-sdk-publish.yml` - SDK publishing (PyPI/npm)
- `reusable-pack-validate.yml` - RulePack/WorkflowPack validation
- `reusable-e2e-run.yml` - E2E test execution

## Usage

See individual workflow files for input parameters.
EOF

git add .
git commit -m "chore: initialize cortx-ci repository structure"
git push origin main

cd ..
```

---

### Step 2: Create cortx-infra Repository

**Purpose:** Infrastructure as Code (Terraform, Helm, policies)

```bash
# Create repo
gh repo create sinergysolutionsllc/cortx-infra \
  --public \
  --description "CORTX infrastructure as code (Terraform, Helm, policies)" \
  --clone

cd cortx-infra

# Copy existing infra from workspace
cp -r ../infra/* ./

# Create structure
mkdir -p terraform/envs/{dev,stage,prod}
mkdir -p helm/charts
mkdir -p policies/{opa,cloud-armor}

# Add README
cat > README.md <<'EOF'
# CORTX Infrastructure

Infrastructure as Code for the CORTX platform.

## Structure

- `terraform/` - GCP resources (GKE, Cloud SQL, Redis, etc.)
- `helm/` - Kubernetes Helm charts
- `policies/` - OPA/Gatekeeper and Cloud Armor policies

## Deployment

See `docs/DEPLOYMENT.md` for deployment procedures.
EOF

git add .
git commit -m "chore: initialize cortx-infra with existing infrastructure"
git push origin main

cd ..
```

---

### Step 3: Create Individual Service Repositories

For each of the 9 services, we'll:

1. Create the repo
2. Set up proper structure per REPO_INSTRUCTION.md
3. Copy service code
4. Add CI workflow caller
5. Verify build and tests

**Template Script:**

```bash
#!/bin/bash
# migrate_service.sh - Migrate one service from cortx-docs to its own repo

SERVICE_NAME=$1  # e.g., "gateway"
SERVICE_FULLNAME="cortx-${SERVICE_NAME}"

echo "=== Migrating ${SERVICE_FULLNAME} ==="

# 1. Create repo
gh repo create "sinergysolutionsllc/${SERVICE_FULLNAME}" \
  --public \
  --description "CORTX ${SERVICE_NAME} service" \
  --clone

cd "${SERVICE_FULLNAME}"

# 2. Create structure
mkdir -p app
mkdir -p tests/{unit,integration,contract}
mkdir -p openapi
mkdir -p infra
mkdir -p scripts
mkdir -p .github/workflows

# 3. Copy service code from cortx-docs
cp -r "../../services/${SERVICE_NAME}/app/"* ./app/
cp -r "../../services/${SERVICE_NAME}/tests/"* ./tests/

# 4. Move openapi.yaml to openapi/ directory
if [ -f "../../services/${SERVICE_NAME}/openapi.yaml" ]; then
  cp "../../services/${SERVICE_NAME}/openapi.yaml" ./openapi/
fi

# 5. Move Dockerfile to infra/
if [ -f "../../services/${SERVICE_NAME}/Dockerfile" ]; then
  cp "../../services/${SERVICE_NAME}/Dockerfile" ./infra/
fi

# 6. Copy dependencies
cp "../../services/${SERVICE_NAME}/requirements.txt" ./ 2>/dev/null || true
cp "../../services/${SERVICE_NAME}/requirements-dev.txt" ./ 2>/dev/null || true
cp "../../services/${SERVICE_NAME}/pytest.ini" ./ 2>/dev/null || true
cp "../../services/${SERVICE_NAME}/pyproject.toml" ./ 2>/dev/null || true
cp "../../services/${SERVICE_NAME}/.dockerignore" ./ 2>/dev/null || true

# 7. Create README
cat > README.md <<EOF
# CORTX ${SERVICE_NAME^} Service

**Purpose:** [Service description from docs]

## Quick Start

\`\`\`bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python -m app.main

# Run tests
pytest tests/ -v --cov=app
\`\`\`

## API Documentation

See \`openapi/openapi.yaml\` for the OpenAPI specification.

## Documentation

Full documentation: https://sinergysolutionsllc.github.io/cortx-docs/services/${SERVICE_NAME}/
EOF

# 8. Create CI workflow caller
cat > .github/workflows/ci.yml <<'EOFCI'
name: CI

on:
  pull_request:
  push:
    branches: [main]
    tags: ['v*.*.*']

jobs:
  service-ci:
    uses: sinergysolutionsllc/cortx-ci/.github/workflows/reusable-python-service.yml@main
    with:
      service_name: "${SERVICE_NAME}"
      publish_openapi: true
      coverage_threshold: 80
    secrets: inherit
EOFCI

# 9. Create CODEOWNERS
cat > CODEOWNERS <<'EOFOWNERS'
# CORTX Service Owners
* @sinergysolutionsllc/cortx-platform-team

/openapi/** @sinergysolutionsllc/api-leads
/infra/** @sinergysolutionsllc/platform-ops
EOFOWNERS

# 10. Initial commit
git add .
git commit -m "feat: initialize ${SERVICE_FULLNAME} service

Migrated from cortx-docs/services/${SERVICE_NAME}/.

## Contents
- Service implementation (app/)
- Comprehensive test suite (tests/)
- OpenAPI specification (openapi/)
- Docker configuration (infra/)
- CI/CD workflows

## Quality Metrics (from cortx-docs)
- Test Coverage: >80%
- Tests: [count from cortx-docs]

## Migration
Source: sinergysolutionsllc/cortx-docs commit 8b77110
Migration Date: 2025-10-08

Co-Authored-By: Claude <noreply@anthropic.com>"

# 11. Push
git push origin main

echo "✅ ${SERVICE_FULLNAME} repository created and initialized"

cd ..
```

**Execute for all 9 services:**

```bash
cd /Users/michael/Development/sinergysolutionsllc

for service in gateway identity validation workflow compliance ai-broker rag ocr ledger; do
  ./migrate_service.sh "$service"
  sleep 2  # Rate limiting
done
```

---

### Step 4: Verify Each Service

After migration, verify each service:

```bash
#!/bin/bash
# verify_service.sh - Verify migrated service works

SERVICE_NAME=$1
SERVICE_FULLNAME="cortx-${SERVICE_NAME}"

cd "${SERVICE_FULLNAME}"

echo "=== Verifying ${SERVICE_FULLNAME} ==="

# 1. Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q

# 2. Run tests
echo "Running tests..."
pytest tests/ -v --cov=app --cov-report=term-missing

# 3. Check OpenAPI
echo "Validating OpenAPI..."
if [ -f "openapi/openapi.yaml" ]; then
  echo "✅ OpenAPI spec exists"
else
  echo "❌ OpenAPI spec missing"
fi

# 4. Check Dockerfile
echo "Checking Dockerfile..."
if [ -f "infra/Dockerfile" ]; then
  echo "✅ Dockerfile exists"
else
  echo "❌ Dockerfile missing"
fi

echo "=== Verification complete for ${SERVICE_FULLNAME} ==="

cd ..
```

**Run verification:**

```bash
for service in gateway identity validation workflow compliance ai-broker rag ocr ledger; do
  ./verify_service.sh "$service" | tee "verify-${service}.log"
done
```

---

### Step 5: Clean Up cortx-docs

**Only after all 9 services are verified and green!**

```bash
cd /Users/michael/Development/sinergysolutionsllc

git checkout -b cleanup/remove-service-implementations

# Remove service implementation code
for service in gateway identity validation workflow compliance ai-broker rag ocr ledger; do
  echo "Cleaning services/${service}..."

  # Remove implementation files
  git rm -r "services/${service}/app" 2>/dev/null || true
  git rm -r "services/${service}/tests" 2>/dev/null || true
  git rm -r "services/${service}/clients" 2>/dev/null || true
  git rm "services/${service}/Dockerfile" 2>/dev/null || true
  git rm "services/${service}/requirements.txt" 2>/dev/null || true
  git rm "services/${service}/requirements-dev.txt" 2>/dev/null || true
  git rm "services/${service}/pytest.ini" 2>/dev/null || true
  git rm "services/${service}/pyproject.toml" 2>/dev/null || true
  git rm "services/${service}/.dockerignore" 2>/dev/null || true
  git rm "services/${service}/Makefile" 2>/dev/null || true
  git rm "services/${service}/TEST_IMPLEMENTATION_SUMMARY.md" 2>/dev/null || true
  git rm -r "services/${service}/.ruff_cache" 2>/dev/null || true
  git rm -r "services/${service}/__pycache__" 2>/dev/null || true
  git rm -r "services/${service}/htmlcov" 2>/dev/null || true
  git rm -r "services/${service}/*.egg-info" 2>/dev/null || true

  # Keep only:
  # - services/${service}/openapi.yaml (if exists)
  # - services/${service}/docs/

  echo "✅ ${service} cleaned"
done

# Remove test infrastructure from root
git rm .github/workflows/test-*.yml 2>/dev/null || true
git rm codecov.yml 2>/dev/null || true
git rm .pre-commit-config.yaml 2>/dev/null || true
git rm docker-compose.yml 2>/dev/null || true

# Remove migration documentation
git rm CODECOV_SETUP_INSTRUCTIONS.md 2>/dev/null || true
git rm PLATFORM_PRODUCTION_READY.md 2>/dev/null || true
git rm QUALITY_HARDENING_COMPLETE.md 2>/dev/null || true
git rm ACTION_ITEMS_COMPLETE.md 2>/dev/null || true
git rm CI_CD_ACTIVATION_RESULTS.md 2>/dev/null || true
git rm MIGRATION_GUIDE_TO_CORTX_PLATFORM.md 2>/dev/null || true
git rm FINAL_STATUS_SUMMARY.md 2>/dev/null || true
git rm CORRECT_ARCHITECTURE_AND_MIGRATION.md 2>/dev/null || true
git rm FINAL_CORRECT_ARCHITECTURE.md 2>/dev/null || true

# Commit cleanup
git commit -m "chore: remove service implementations (migrated to individual repos)

All service implementations have been migrated to individual repositories:
- cortx-gateway
- cortx-identity
- cortx-validation
- cortx-workflow
- cortx-compliance
- cortx-ai-broker
- cortx-rag
- cortx-ocr
- cortx-ledger

cortx-docs now contains only:
- Documentation (docs/)
- OpenAPI specs (services/*/openapi.yaml) [synced from service repos]
- Service documentation (services/*/docs/)
- Documentation site configuration

Architecture corrected per REPO_INSTRUCTION.md:
- cortx-docs: Documentation portal ONLY
- Individual service repos: Service implementations
- cortx-ci: Reusable CI/CD workflows
- cortx-infra: Infrastructure as Code

Migration completed: 2025-10-08"

# Push
git push origin cleanup/remove-service-implementations

# Create PR
gh pr create \
  --title "chore: Clean up cortx-docs after service migration" \
  --body "Removes service implementations from cortx-docs after successful migration to individual repos. See commit message for details."
```

---

## Risk Mitigation

### Risk 1: Service Dependencies Break

**Mitigation:**

- Keep services running from cortx-docs during migration
- Only deploy new service repos to dev environment initially
- Use feature flags for gradual cutover

### Risk 2: CI/CD Disruption

**Mitigation:**

- cortx-ci repo created first with all reusable workflows
- Test CI in service repos before removing from cortx-docs
- Maintain parallel CI until cutover

### Risk 3: OpenAPI Sync Breaks

**Mitigation:**

- scripts/sync_openapi.sh updated to pull from new service repos
- Document new sync process
- Test sync before final cleanup

### Risk 4: Developer Confusion

**Mitigation:**

- Clear documentation in each repo README
- Migration guide in cortx-docs
- Slack announcement with new workflow

---

## Rollback Strategy

If migration fails at any step:

```bash
# 1. Check out pre-migration backup
cd /Users/michael/Development/sinergysolutionsllc
git checkout pre-migration-backup-2025-10-08

# 2. Verify services still work
for service in gateway identity validation workflow compliance ai-broker rag ocr ledger; do
  cd "services/${service}"
  pytest tests/ -v
  cd ../..
done

# 3. Delete failed service repos (if needed)
gh repo delete sinergysolutionsllc/cortx-gateway --yes
# ... repeat for each failed repo

# 4. Return to main
git checkout main
```

---

## Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Pre-flight checks | 30 min | None |
| Create cortx-ci | 1 hour | None |
| Create cortx-infra | 30 min | None |
| Migrate 9 services | 3-4 hours | cortx-ci created |
| Verify all services | 2 hours | All services migrated |
| Clean up cortx-docs | 1 hour | All services verified |
| Documentation updates | 1 hour | Cleanup complete |
| **Total** | **8-10 hours** | Sequential execution |

**Recommended:** Execute over 2 days with verification gates between major phases.

---

## Success Criteria

- [ ] All 9 service repos created and accessible
- [ ] Each service repo has proper structure (app/, tests/, openapi/, infra/)
- [ ] All service tests pass (pytest green)
- [ ] CI workflows configured and passing
- [ ] cortx-docs cleaned (no service code)
- [ ] OpenAPI sync working from service repos to cortx-docs
- [ ] cortx-ci repository created with reusable workflows
- [ ] cortx-infra repository created with infrastructure code
- [ ] Developer documentation updated
- [ ] No broken links in documentation

---

## Post-Migration Tasks

1. **Update Developer Onboarding**
   - Document new multi-repo workflow
   - Update clone/setup instructions
   - Create workspace setup script

2. **Configure Branch Protection**
   - Enable required status checks
   - Require PR reviews
   - Enforce CODEOWNERS

3. **Set Up Codecov** (if using)
   - Add CODECOV_TOKEN to each service repo
   - Configure coverage thresholds (80%)

4. **Update CI/CD Docs**
   - Document reusable workflow usage
   - Add deployment procedures
   - Create runbooks

5. **Announce Migration**
   - Slack/email to team
   - Migration guide link
   - Office hours for questions

---

## Verification Gate: Phase 0 Complete

**Deliverables:**

- ✅ `docs/operations/repo_target_map.yml` - Created
- ✅ `docs/operations/repo_migration_plan.md` - This document

**Conflicts Identified:**

- None. All paths cleanly map to target repos.

**Risks Documented:**

- High: Git history preservation (mitigated with copy approach)
- Medium: CI/CD transition (mitigated with parallel CI)
- Low: Developer workflow changes (mitigated with docs)

**Next Step:** Proceed to Phase 1 (Functional Boundaries) for stakeholder approval before executing migration.

---

**Status:** ✅ Phase 0 Complete - Ready for Tech Lead Approval
