# CORTX Correct Architecture & Migration Plan

**Date:** 2025-10-08
**Issue Identified:** Service implementations incorrectly added to cortx-docs
**Status:** Migration Plan Ready

---

## Problem Statement

During the quality hardening initiative, service implementation code was accidentally created in `cortx-docs/services/*/app/`. This violates the intended architecture where:

- **cortx-docs** should contain: Documentation and OpenAPI specs ONLY
- **cortx-platform** should contain: Service implementations

---

## Correct Architecture

### Repository Purpose Matrix

| Repository | Purpose | Should Contain | Should NOT Contain |
|------------|---------|----------------|-------------------|
| **cortx-docs** | Documentation portal | • Documentation<br>• OpenAPI specs<br>• MkDocs config | • Service implementation<br>• Application code |
| **cortx-platform** | Service implementations | • services/*/app/<br>• Dockerfiles<br>• Tests<br>• CI/CD workflows | • Documentation<br>(kept in cortx-docs) |
| **Individual service repos**<br>(gateway, identity, etc.) | OpenAPI spec publication | • openapi.yaml<br>• README | • Implementation<br>• Tests |
| **cortx-sdks** | Client SDKs | • Python SDK<br>• TypeScript SDK | • Service implementation |
| **Suite repos**<br>(fedsuite, corpsuite, etc.) | Product modules | • Business logic modules<br>• Suite-specific code | • Platform services |

---

## Current State (Incorrect)

```
cortx-docs/
├── services/
│   ├── gateway/
│   │   ├── app/                    ❌ Should NOT be here
│   │   │   ├── main.py            ❌ Service implementation
│   │   │   ├── routers/           ❌ Application code
│   │   │   └── middleware/        ❌ Application code
│   │   ├── tests/                  ❌ Should NOT be here
│   │   ├── Dockerfile              ❌ Should NOT be here
│   │   ├── openapi.yaml            ✅ Correct
│   │   └── docs/                   ✅ Correct (service-specific docs)
│   └── identity/
│       ├── app/                    ❌ Should NOT be here
│       ├── tests/                  ❌ Should NOT be here
│       ├── Dockerfile              ❌ Should NOT be here
│       └── openapi.yaml            ✅ Correct
```

**Files Added Incorrectly (in commit 8b77110)**:

- All `services/*/app/` directories
- All `services/*/tests/` directories
- All `services/*/Dockerfile` files
- All `services/*/requirements.txt` files
- All `services/*/pytest.ini` files

---

## Target State (Correct)

### cortx-docs (Documentation Only)

```
cortx-docs/
├── docs/                           ✅ Documentation
│   ├── architecture/
│   ├── services/
│   └── operations/
├── services/
│   ├── gateway/
│   │   ├── openapi.yaml            ✅ Synced from gateway repo
│   │   ├── README.md               ✅ Service overview
│   │   └── docs/                   ✅ Service-specific docs (FDD, guides)
│   └── identity/
│       ├── openapi.yaml            ✅ Synced from identity repo
│       ├── README.md               ✅ Service overview
│       └── docs/                   ✅ Service-specific docs
├── .github/workflows/
│   ├── deploy-pages.yml            ✅ Docs deployment
│   ├── docs-ci.yml                 ✅ Docs validation
│   └── contracts-ci.yml            ✅ OpenAPI validation
├── scripts/
│   └── sync_openapi.sh             ✅ Sync specs from service repos
└── mkdocs.yml                      ✅ Docs site config
```

### cortx-platform (Service Implementations)

```
cortx-platform/
├── services/
│   ├── gateway/
│   │   ├── app/                    ✅ Service implementation
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   └── middleware/
│   │   ├── tests/                  ✅ Test suite
│   │   │   ├── unit/
│   │   │   ├── integration/
│   │   │   └── conftest.py
│   │   ├── Dockerfile              ✅ Container definition
│   │   ├── requirements.txt        ✅ Dependencies
│   │   ├── pytest.ini              ✅ Test config
│   │   └── pyproject.toml          ✅ Package config
│   ├── identity/
│   │   ├── app/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── ... (7 more services)
├── .github/workflows/
│   ├── test-gateway.yml            ✅ Service CI/CD
│   ├── test-identity.yml           ✅ Service CI/CD
│   └── test-all-services.yml       ✅ Platform CI/CD
├── docker-compose.yml              ✅ Local development
├── codecov.yml                     ✅ Coverage config
├── .pre-commit-config.yaml         ✅ Code quality
└── README.md                       ✅ Platform overview
```

---

## Migration Plan

### Phase 1: Move Code to cortx-platform

#### Step 1: Clone cortx-platform

```bash
cd /Users/michael/Development/sinergysolutionsllc
gh repo clone sinergysolutionsllc/cortx-platform
cd cortx-platform
```

#### Step 2: Copy Service Implementations

```bash
# Copy all service code from cortx-docs to cortx-platform
cd /Users/michael/Development/sinergysolutionsllc

# For each service, copy implementation files
for service in gateway identity ai-broker validation workflow compliance ledger ocr rag; do
  echo "Migrating $service..."

  # Create service directory in cortx-platform
  mkdir -p cortx-platform/services/$service

  # Copy implementation files
  cp -r cortx-docs/services/$service/app cortx-platform/services/$service/
  cp -r cortx-docs/services/$service/tests cortx-platform/services/$service/
  cp cortx-docs/services/$service/Dockerfile cortx-platform/services/$service/ 2>/dev/null || true
  cp cortx-docs/services/$service/requirements.txt cortx-platform/services/$service/
  cp cortx-docs/services/$service/requirements-dev.txt cortx-platform/services/$service/ 2>/dev/null || true
  cp cortx-docs/services/$service/pytest.ini cortx-platform/services/$service/
  cp cortx-docs/services/$service/pyproject.toml cortx-platform/services/$service/ 2>/dev/null || true
  cp cortx-docs/services/$service/Makefile cortx-platform/services/$service/ 2>/dev/null || true
  cp cortx-docs/services/$service/.dockerignore cortx-platform/services/$service/ 2>/dev/null || true

  echo "✅ $service migrated"
done
```

#### Step 3: Copy Platform Infrastructure

```bash
# Copy CI/CD workflows
cp -r cortx-docs/.github/workflows/test-*.yml cortx-platform/.github/workflows/

# Copy quality tooling
cp cortx-docs/codecov.yml cortx-platform/
cp cortx-docs/.pre-commit-config.yaml cortx-platform/

# Copy docker-compose
cp cortx-docs/docker-compose.yml cortx-platform/

# Copy documentation files
cp cortx-docs/CODECOV_SETUP_INSTRUCTIONS.md cortx-platform/
cp cortx-docs/PLATFORM_PRODUCTION_READY.md cortx-platform/
cp cortx-docs/QUALITY_HARDENING_COMPLETE.md cortx-platform/
cp cortx-docs/ACTION_ITEMS_COMPLETE.md cortx-platform/
```

#### Step 4: Commit to cortx-platform

```bash
cd cortx-platform

git checkout -b feat/migrate-all-services-from-docs

git add .

git commit -m "feat: migrate all 9 services from cortx-docs to cortx-platform

## Migration Summary

Migrates complete service implementations, tests, and CI/CD infrastructure
from cortx-docs (incorrect location) to cortx-platform (correct location).

### Services Migrated (9)
- gateway (17 test files, 94+ tests)
- identity (18 test files, 224 tests)
- ai-broker (7 test files, 145 tests)
- validation (6 test files, 109 tests)
- workflow (12 test files, 130 tests)
- compliance (15 test files, 157 tests)
- ledger (13 test files, 141 tests)
- ocr (9 test files, 138 tests)
- rag (7 test files, 210 tests)

### Infrastructure Migrated
- ✅ Service implementations (services/*/app/)
- ✅ Test suites (services/*/tests/)
- ✅ Dockerfiles and configs
- ✅ CI/CD workflows (10 GitHub Actions)
- ✅ Quality tooling (codecov, pre-commit)
- ✅ Docker Compose configuration

### Quality Metrics
- Test Coverage: ~85% (target: >80%)
- Total Test Cases: 1,348+
- CI/CD Workflows: 10
- Pre-commit Hooks: 18

### Architecture Correction

**Before**: Services incorrectly in cortx-docs (documentation repo)
**After**: Services correctly in cortx-platform (implementation repo)

## Testing

All tests ready to run:
\`\`\`bash
pytest services/ -v --cov
\`\`\`

## CI/CD Activation

1. Add CODECOV_TOKEN secret
2. Install pre-commit: \`pre-commit install\`
3. Push to trigger workflows

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin feat/migrate-all-services-from-docs
```

#### Step 5: Create Pull Request

```bash
gh pr create \
  --title "feat: Migrate All 9 Services from cortx-docs to cortx-platform" \
  --body "See commit message for full details. This corrects the architecture by moving service implementations to cortx-platform where they belong."
```

### Phase 2: Clean Up cortx-docs

#### Step 6: Remove Implementation Code from cortx-docs

```bash
cd /Users/michael/Development/sinergysolutionsllc/cortx-docs

git checkout -b cleanup/remove-service-implementations

# Remove all implementation code
for service in gateway identity ai-broker validation workflow compliance ledger ocr rag; do
  echo "Cleaning $service..."

  # Remove implementation files (keep only openapi.yaml and docs/)
  git rm -r services/$service/app 2>/dev/null || true
  git rm -r services/$service/tests 2>/dev/null || true
  git rm services/$service/Dockerfile 2>/dev/null || true
  git rm services/$service/requirements.txt 2>/dev/null || true
  git rm services/$service/requirements-dev.txt 2>/dev/null || true
  git rm services/$service/pytest.ini 2>/dev/null || true
  git rm services/$service/pyproject.toml 2>/dev/null || true
  git rm services/$service/Makefile 2>/dev/null || true
  git rm services/$service/.dockerignore 2>/dev/null || true
  git rm services/$service/TEST_IMPLEMENTATION_SUMMARY.md 2>/dev/null || true
  git rm services/$service/README.md 2>/dev/null || true

  # Keep only:
  # - services/$service/openapi.yaml
  # - services/$service/docs/

  echo "✅ $service cleaned"
done

# Remove platform infrastructure files
git rm .github/workflows/test-*.yml
git rm codecov.yml
git rm .pre-commit-config.yaml
git rm docker-compose.yml 2>/dev/null || true

# Remove migration/quality docs (now in cortx-platform)
git rm CODECOV_SETUP_INSTRUCTIONS.md
git rm PLATFORM_PRODUCTION_READY.md
git rm QUALITY_HARDENING_COMPLETE.md
git rm ACTION_ITEMS_COMPLETE.md
git rm CI_CD_ACTIVATION_RESULTS.md
git rm MIGRATION_GUIDE_TO_CORTX_PLATFORM.md
git rm FINAL_STATUS_SUMMARY.md
git rm CORRECT_ARCHITECTURE_AND_MIGRATION.md

git commit -m "chore: remove service implementations (migrated to cortx-platform)

Service implementations, tests, and CI/CD have been migrated to
cortx-platform repository where they belong.

cortx-docs now contains only:
- Documentation (docs/)
- OpenAPI specs (services/*/openapi.yaml)
- Service documentation (services/*/docs/)
- Documentation site config (mkdocs.yml)

Architecture corrected to match intended design."

git push origin cleanup/remove-service-implementations
```

#### Step 7: Update cortx-docs README

```bash
# Update README to point to cortx-platform for implementation
# (Manual edit to add reference to cortx-platform)

git add README.md
git commit -m "docs: update README to reference cortx-platform for implementations"
git push origin cleanup/remove-service-implementations
```

---

## Verification Checklist

### After Migration to cortx-platform

- [ ] All 9 services have `app/` directories in cortx-platform
- [ ] All 9 services have `tests/` directories in cortx-platform
- [ ] CI/CD workflows in cortx-platform/.github/workflows/
- [ ] docker-compose.yml in cortx-platform (root)
- [ ] codecov.yml in cortx-platform (root)
- [ ] .pre-commit-config.yaml in cortx-platform (root)
- [ ] Tests run successfully: `cd cortx-platform && pytest services/ -v`
- [ ] Docker Compose builds: `cd cortx-platform && docker-compose build`
- [ ] Add CODECOV_TOKEN to cortx-platform repo secrets

### After Cleanup in cortx-docs

- [ ] NO `app/` directories in cortx-docs/services/
- [ ] NO `tests/` directories in cortx-docs/services/
- [ ] NO `Dockerfile` files in cortx-docs/services/
- [ ] ONLY `openapi.yaml` and `docs/` in cortx-docs/services/*/
- [ ] Documentation builds: `cd cortx-docs && mkdocs build --strict`
- [ ] deploy-pages.yml workflow still exists (docs deployment)
- [ ] docs-ci.yml workflow still exists (docs validation)

---

## Timeline

**Estimated Time**: 3-4 hours

| Phase | Task | Time |
|-------|------|------|
| 1 | Clone and prepare cortx-platform | 15 min |
| 2 | Copy service implementations | 30 min |
| 3 | Copy infrastructure | 15 min |
| 4 | Commit and create PR | 15 min |
| 5 | Test in cortx-platform | 1 hour |
| 6 | Clean up cortx-docs | 30 min |
| 7 | Verify both repos | 30 min |
| 8 | Activate CI/CD | 30 min |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Tests fail after migration** | Low | Medium | Test locally before pushing |
| **Docker builds fail** | Low | Medium | Verify docker-compose.yml paths |
| **Lost work during cleanup** | Very Low | High | Create migration branch first |
| **CI/CD doesn't trigger** | Low | Low | Manually trigger workflows |

**Overall Risk: LOW** - Straightforward copy/move operation

---

## Post-Migration Architecture

### Repository Purposes

1. **cortx-docs**: Documentation portal only
   - MkDocs documentation
   - OpenAPI spec aggregation
   - Service documentation (FDDs, guides)

2. **cortx-platform**: Service implementations
   - All 9 microservices
   - Tests (1,348+ test cases)
   - CI/CD (10 workflows)
   - Docker Compose orchestration

3. **Individual service repos**: OpenAPI spec sources
   - Publish OpenAPI specs
   - Synced to cortx-docs via sync_openapi.sh

4. **cortx-sdks**: Client libraries
   - Python SDK
   - TypeScript SDK

5. **Suite repos**: Product modules
   - fedsuite, corpsuite, medsuite, govsuite
   - Business logic for specific domains

6. **cortx-e2e**: End-to-end testing
   - Playwright tests
   - User journey scenarios

---

## Next Steps

1. **Review this migration plan**
2. **Execute Phase 1** (migrate to cortx-platform)
3. **Test in cortx-platform** (run pytest, docker-compose)
4. **Execute Phase 2** (clean up cortx-docs)
5. **Activate CI/CD** in cortx-platform
6. **Update documentation** to reflect correct architecture

---

**Status**: Ready to execute
**Created**: 2025-10-08
**Priority**: High (corrects architectural violation)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
