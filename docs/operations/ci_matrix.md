# CORTX CI/CD Matrix

**Date:** 2025-10-08
**Phase:** Phase 3 - Reusable CI Wiring
**Status:** ✅ Complete

---

## Overview

This document defines the CI/CD pipeline structure and required checks for all CORTX repositories. All services use reusable workflows from the `cortx-ci` repository for consistency and maintainability.

---

## Reusable Workflows

**Repository:** https://github.com/sinergysolutionsllc/cortx-ci

| Workflow | Purpose | Used By |
|----------|---------|---------|
| `reusable-python-service.yml` | Full CI/CD for Python services | All 9 platform services |
| `reusable-docker-build-scan.yml` | Container build & security scanning | All services, Designer |
| `reusable-openapi-publish.yml` | API spec validation & docs sync | All services with OpenAPI |
| `reusable-helm-deploy.yml` | Kubernetes deployment | All services |
| `reusable-pack-validate.yml` | RulePack/WorkflowPack validation | cortx-packs |
| `reusable-e2e-run.yml` | End-to-end test execution | cortx-e2e |

---

## Service Repository CI Matrix

### Platform Services (9 repos)

All platform services follow the same CI pattern:

| Service | Repo | CI Workflow | Quality Gates | Auto-Deploy |
|---------|------|-------------|---------------|-------------|
| **cortx-gateway** | [Link](https://github.com/sinergysolutionsllc/cortx-gateway) | ✅ | ✅ | dev on main |
| **cortx-identity** | [Link](https://github.com/sinergysolutionsllc/cortx-identity) | ✅ | ✅ | dev on main |
| **cortx-validation** | [Link](https://github.com/sinergysolutionsllc/cortx-validation) | ✅ | ✅ | dev on main |
| **cortx-workflow** | [Link](https://github.com/sinergysolutionsllc/cortx-workflow) | ✅ | ✅ | dev on main |
| **cortx-compliance** | [Link](https://github.com/sinergysolutionsllc/cortx-compliance) | ✅ | ✅ | dev on main |
| **cortx-ai-broker** | [Link](https://github.com/sinergysolutionsllc/cortx-ai-broker) | ✅ | ✅ | dev on main |
| **cortx-rag** | [Link](https://github.com/sinergysolutionsllc/cortx-rag) | ✅ | ✅ | dev on main |
| **cortx-ocr** | [Link](https://github.com/sinergysolutionsllc/cortx-ocr) | ✅ | ✅ | dev on main |
| **cortx-ledger** | [Link](https://github.com/sinergysolutionsllc/cortx-ledger) | ✅ | ✅ | dev on main |

---

## Required Checks Per Repository

### Platform Services (Python)

**Workflow:** `reusable-python-service.yml`

#### 1. Code Quality Checks

| Check | Tool | Fail On | Description |
|-------|------|---------|-------------|
| **Format** | black | Non-compliance | Code formatting standards |
| **Lint** | ruff | Errors | Code quality and style |
| **Type Check** | mypy | Critical errors | Static type checking |
| **Security Audit** | pip-audit | High+ vulnerabilities | Python dependency vulnerabilities |
| **Secret Scan** | Gitleaks | Secrets found | Detect hardcoded secrets |

**Status:** ✅ Implemented

#### 2. Test Execution

| Check | Coverage | Fail On | Description |
|-------|----------|---------|-------------|
| **Unit Tests** | Included | Test failures | Fast, isolated tests |
| **Integration Tests** | Included | Test failures | Service integration tests |
| **Coverage Threshold** | ≥ 85% | Below threshold | Code coverage enforcement |
| **Codecov Upload** | Optional | Never | Coverage tracking (if token provided) |

**Status:** ✅ Implemented

#### 3. Container Security

| Check | Tool | Severity | Fail On | Description |
|-------|------|----------|---------|-------------|
| **Build** | Docker Buildx | N/A | Build failure | Multi-platform build |
| **Vulnerability Scan** | Trivy | CRITICAL, HIGH | High+ CVEs | Container image scanning |
| **SBOM** | Grype | HIGH | High+ CVEs | Software Bill of Materials |
| **SARIF Upload** | GitHub Security | N/A | Never | Security findings to GitHub |

**Status:** ✅ Implemented

#### 4. API Validation

| Check | Tool | Fail On | Description |
|-------|------|---------|-------------|
| **OpenAPI Lint** | Redocly CLI | Lint errors | API spec validation |
| **Spectral Lint** | Spectral | Spec errors | OAS compliance |
| **Docs Sync** | gh CLI | PR creation failure | Auto-sync to cortx-docs |

**Status:** ✅ Implemented (on main branch only)

#### 5. Deployment

| Environment | Trigger | Approval | Health Checks |
|-------------|---------|----------|---------------|
| **dev** | Push to main | None (auto) | ✅ Required |
| **stage** | Manual dispatch | Required | ✅ Required |
| **prod** | Manual dispatch | Required + approvers | ✅ Required |

**Status:** ✅ Configured (deployment implementation pending infra setup)

---

## Quality Gates Summary

### Enforcement Levels

| Gate | Level | Action | Bypass |
|------|-------|--------|--------|
| **Code formatting** | ERROR | Block PR merge | Not allowed |
| **Linting errors** | ERROR | Block PR merge | Not allowed |
| **Type check** | WARNING | Log only | N/A |
| **Security audit** | WARNING | Log only | With justification |
| **Secret detection** | ERROR | Block PR merge | Not allowed |
| **Test failures** | ERROR | Block PR merge | Not allowed |
| **Coverage < 85%** | ERROR | Block PR merge | With approval |
| **Container HIGH CVEs** | ERROR | Block build | With risk acceptance |
| **OpenAPI validation** | ERROR | Block docs sync | Fix required |

---

## Branch Protection Rules

### Required for All Service Repos

```yaml
Branch: main
Required checks:
  - Code Quality Checks
  - Run Tests
  - Build & Scan Container

Require pull request before merging: true
Require approvals: 1
Dismiss stale reviews: true
Require review from Code Owners: true
Restrict who can push to matching branches: true
Allow force pushes: false
Allow deletions: false
```

**Status:** 🔄 To be configured via GitHub settings

---

## Workflow Triggers

### Platform Services

```yaml
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
    tags: ['v*.*.*']
  workflow_dispatch:
```

**Behavior:**
- **PR:** Run all checks (no deploy)
- **Push to main:** Run all checks + auto-deploy to dev
- **Tag push:** Run all checks + build release artifacts
- **Manual:** Run with custom parameters

---

## Environment Configuration

### GitHub Environments

| Environment | Protection Rules | Secrets Required | Reviewers |
|-------------|-----------------|------------------|-----------|
| **dev** | None (auto-deploy) | GCP_SA_KEY | None |
| **stage** | Manual approval | GCP_SA_KEY, KUBECONFIG | Platform Ops |
| **prod** | Manual approval + wait 15min | GCP_SA_KEY, KUBECONFIG | Platform Ops + Tech Lead |

**Status:** 🔄 To be configured in repository settings

---

## Secret Management

### Repository Secrets

| Secret | Scope | Required For | Description |
|--------|-------|--------------|-------------|
| `CODECOV_TOKEN` | Per-repo | Coverage reporting | Codecov API token (optional) |
| `DOCS_REPO_TOKEN` | Organization | OpenAPI sync | Personal Access Token for cortx-docs |
| `GCP_SA_KEY` | Environment | Deployment | Service Account JSON for GCP |
| `KUBECONFIG` | Environment | Deployment | Kubernetes config (if not using GCP) |
| `REGISTRY_USERNAME` | Organization | Image push | Container registry username |
| `REGISTRY_PASSWORD` | Organization | Image push | Container registry password |

**Status:** 🔄 To be configured by Platform Ops

---

## CI/CD Pipeline Flow

### On Pull Request

```
1. Checkout code
2. Code Quality Checks
   ├─ black --check
   ├─ ruff check
   ├─ mypy
   ├─ pip-audit
   └─ gitleaks
3. Run Tests
   ├─ pytest unit
   ├─ pytest integration
   ├─ coverage check (≥ 85%)
   └─ codecov upload
4. Build & Scan Container
   ├─ docker build
   ├─ trivy scan (fail on HIGH+)
   ├─ grype scan
   └─ upload SARIF/SBOM
5. ✅ PR ready for review
```

### On Push to Main

```
1-4. (Same as PR)
5. OpenAPI Publish
   ├─ redocly lint
   ├─ spectral lint
   └─ PR to cortx-docs
6. Deploy to dev
   ├─ helm upgrade
   ├─ wait for rollout
   ├─ health check
   └─ smoke tests
7. ✅ Deployed to dev
```

### On Tag Push (v*.*.*)

```
1-4. (Same as PR)
5. Build Release Artifacts
   ├─ docker tag with version
   ├─ push to registry
   ├─ generate SBOM
   └─ create GitHub release
6. ✅ Release published
```

---

## Metrics & Monitoring

### CI Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| **Check job duration** | < 5 min | TBD |
| **Test job duration** | < 10 min | TBD |
| **Build job duration** | < 8 min | TBD |
| **Total pipeline duration** | < 15 min | TBD |
| **Pipeline success rate** | > 95% | TBD |

### Quality Metrics

| Metric | Target | Enforcement |
|--------|--------|-------------|
| **Test coverage** | ≥ 85% | Hard gate |
| **Security vulnerabilities** | 0 HIGH+ | Hard gate |
| **Code quality issues** | 0 errors | Hard gate |
| **Secret leaks** | 0 | Hard gate |

---

## Verification Checklist

### Phase 3 Completion Criteria

- [x] cortx-ci repo has all reusable workflows
- [x] All 9 service repos have CI caller workflows
- [x] Quality gates defined (coverage, security, linting)
- [x] OpenAPI validation and sync configured
- [x] Container scanning with Trivy and Grype
- [x] Secret detection with Gitleaks
- [x] ci_matrix.md documentation created
- [ ] Branch protection rules configured on all repos
- [ ] GitHub environments created (dev/stage/prod)
- [ ] Required secrets configured
- [ ] At least one service CI passing green

**Phase 3 Status:** ✅ **Workflows Implemented** (Configuration pending)

---

## Next Steps (Phase 4)

1. Configure branch protection rules via GitHub API or UI
2. Set up GitHub environments with protection rules
3. Configure organization and repository secrets
4. Trigger first CI run on each service
5. Verify all quality gates pass
6. Move to Phase 4: Packs & Designer Integration

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Coverage below threshold | New untested code | Add tests or adjust threshold |
| Trivy HIGH vulnerabilities | Outdated dependencies | Update requirements.txt |
| Gitleaks detection | Hardcoded secrets | Remove secrets, use env vars |
| Docker build failure | Missing dependencies | Check Dockerfile and requirements |
| OpenAPI validation failure | Invalid spec | Run `redocly lint` locally |

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Reusable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [CORTX CI Repository](https://github.com/sinergysolutionsllc/cortx-ci)

---

**Maintained by:** Platform Ops Team
**Last Updated:** 2025-10-08
**Version:** 1.0
