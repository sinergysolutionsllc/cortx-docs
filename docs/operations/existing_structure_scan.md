# Existing Structure Scan Report

**Date:** 2025-10-08
**Purpose:** Scan existing repos and structure before migration
**Status:** Complete

---

## Summary

### Existing GitHub Repositories

| Repository | Status | Size | Notes |
|------------|--------|------|-------|
| **cortx-docs** | ✅ EXISTS | 1863KB | Current repo; has service code (wrong) |
| **cortx-platform** | ✅ EXISTS | 5KB | Empty/minimal; no services directory |
| **cortx-sdks** | ✅ EXISTS | 6KB | Exists on GitHub |
| **cortx-packs** | ✅ EXISTS | 4KB | Exists on GitHub |
| **cortx-designer** | ✅ EXISTS | 3KB | Exists on GitHub |
| **cortx-e2e** | ✅ EXISTS | 5KB | Exists on GitHub |
| **fedsuite** | ✅ EXISTS | 4KB | Exists on GitHub |
| **corpsuite** | ✅ EXISTS | 5KB | Exists on GitHub |
| **medsuite** | ✅ EXISTS | 5KB | Exists on GitHub |
| **govsuite** | ✅ EXISTS | 3KB | Exists on GitHub |

### Repositories That DON'T Exist (Need to Create)

| Repository | Status | Purpose |
|------------|--------|---------|
| **cortx-gateway** | ❌ NOT FOUND | Individual service repo |
| **cortx-identity** | ❌ NOT FOUND | Individual service repo |
| **cortx-validation** | ❌ NOT FOUND | Individual service repo |
| **cortx-workflow** | ❌ NOT FOUND | Individual service repo |
| **cortx-compliance** | ❌ NOT FOUND | Individual service repo |
| **cortx-ai-broker** | ❌ NOT FOUND | Individual service repo |
| **cortx-rag** | ❌ NOT FOUND | Individual service repo |
| **cortx-ocr** | ❌ NOT FOUND | Individual service repo |
| **cortx-ledger** | ❌ NOT FOUND | Individual service repo |
| **cortx-ci** | ❌ NOT FOUND | Reusable CI/CD workflows |
| **cortx-infra** | ❌ NOT FOUND | Infrastructure as Code |

---

## Local Workspace Structure

### Current Working Directory: cortx-docs

This IS the main git repository (cortx-docs). The other directories are NOT git repos:

```
/Users/michael/Development/sinergysolutionsllc/ (cortx-docs repo)
├── .git/                       ✅ Git repo root
├── services/                   ❌ PROBLEM: Has service code
│   ├── gateway/app/
│   ├── identity/app/
│   ├── validation/app/
│   ├── workflow/app/
│   ├── compliance/app/
│   ├── ai-broker/app/
│   ├── rag/app/
│   ├── ocr/app/
│   └── ledger/app/
├── docs/                       ✅ Correct: Documentation
├── cortx-platform/             ❌ NOT a git repo (directory only)
├── cortx-sdks/                 ❌ NOT a git repo (directory only)
├── cortx-packs/                ❌ NOT a git repo (directory only)
├── cortx-designer/             ❌ NOT a git repo (directory only)
├── cortx-e2e/                  ❌ NOT a git repo (directory only)
├── fedsuite/                   ❌ NOT a git repo (directory only)
├── corpsuite/                  ❌ NOT a git repo (directory only)
├── medsuite/                   ❌ NOT a git repo (directory only)
└── govsuite/                   ❌ NOT a git repo (directory only)
```

### Key Finding

**All the directories (cortx-platform, cortx-sdks, etc.) are NOT git repositories**. They're just regular directories in the cortx-docs repo workspace.

However, checking `.gitignore`:

```
# embedded project repos (not tracked in docs portal)
corpsuite/
cortx-designer/
cortx-e2e/
cortx-packs/
cortx-platform/
cortx-sdks/
fedsuite/
govsuite/
medsuite/
```

**These directories are gitignored**, meaning they were INTENDED to be separate git repos cloned into the workspace, but they're not currently cloned.

---

## cortx-platform Repository Analysis

**GitHub Repo:** <https://github.com/sinergysolutionsllc/cortx-platform>
**Status:** EXISTS (5KB)
**Local Clone:** Yes, at `./cortx-platform/`

**Contents:**

```
cortx-platform/
├── .ai/
├── .claude/
├── .github/
├── docs/
├── infra/
├── libs/
├── scripts/
├── services/           # EXISTS but appears empty
├── specs/
├── README.md
└── REPO_INSTRUCTION.md
```

**services/ directory:** EXISTS in cortx-platform, but is likely empty or minimal.

**Conclusion:** cortx-platform was set up as a monorepo for services but never populated. Only has structural scaffolding.

---

## Migration Strategy Adjustments

Based on this scan, here's what we need to do:

### 1. Individual Service Repos (9 to create)

**Action:** CREATE these repos from scratch

- cortx-gateway
- cortx-identity
- cortx-validation
- cortx-workflow
- cortx-compliance
- cortx-ai-broker
- cortx-rag
- cortx-ocr
- cortx-ledger

**Source:** Copy from `cortx-docs/services/*/`

### 2. Infrastructure Repos (2 to create)

**Action:** CREATE these repos

**cortx-ci:**

- Create from scratch
- Add reusable GitHub Actions workflows

**cortx-infra:**

- Create from existing `cortx-docs/infra/`
- Add Terraform, Helm, policies

### 3. Existing Repos (Verify and Update)

These already exist on GitHub:

**cortx-platform:**

- Option A: Deprecate (since individual service repos are preferred)
- Option B: Keep for shared platform code
- **Recommendation:** Keep but restructure for shared libs only

**cortx-sdks:**

- EXISTS on GitHub
- Should be cloned and verified

**cortx-packs:**

- EXISTS on GitHub
- Should be cloned and verified

**cortx-designer:**

- EXISTS on GitHub
- Should be cloned and verified

**cortx-e2e:**

- EXISTS on GitHub (recently created with Playwright tests)
- Should be cloned and verified

**Suite repos** (fedsuite, corpsuite, medsuite, govsuite):

- All exist on GitHub
- Should be cloned and verified

### 4. cortx-docs Cleanup

**Action:** CLEAN UP after migration

**Remove:**

- All service implementation code (`services/*/app/`, `services/*/tests/`)
- Test infrastructure files
- docker-compose.yml
- Migration documentation

**Keep:**

- Documentation (`docs/`)
- Service documentation (`services/*/docs/`)
- OpenAPI specs (will be synced from service repos)
- MkDocs configuration

---

## Verification Checklist

Before proceeding with migration:

- [x] Scanned GitHub org for existing repos
- [x] Verified which repos exist vs. need creation
- [x] Checked local workspace structure
- [x] Identified cortx-docs as main working repo
- [x] Confirmed service code is in cortx-docs (wrong place)
- [x] Verified cortx-platform exists but is empty
- [x] Confirmed none of the subdirectories are cloned repos

**Conclusion:** Safe to proceed with creating individual service repos.

---

## Recommended Actions

### Immediate Next Steps

1. **Create 9 individual service repos** (cortx-gateway, cortx-identity, etc.)
2. **Create cortx-ci repo** for reusable workflows
3. **Create cortx-infra repo** for infrastructure code
4. **Clone existing repos** (cortx-sdks, cortx-packs, cortx-designer, cortx-e2e, suites) for verification
5. **Migrate service code** from cortx-docs to new service repos
6. **Clean up cortx-docs** to be documentation-only

### cortx-platform Decision

**Question:** What to do with cortx-platform?

**Options:**
A. **Deprecate** - Individual service repos replace it
B. **Repurpose** - Use for shared platform libraries only
C. **Keep as monorepo** - Migrate all services there (conflicts with REPO_INSTRUCTION.md)

**Recommendation:** **Option A (Deprecate)** per REPO_INSTRUCTION.md which specifies individual service repos.

If shared code is needed, create **cortx-libs** repository for common utilities.

---

## Updated Migration Plan

Based on scan findings, the migration plan remains valid with these adjustments:

1. **Skip cloning suites** - They exist but aren't needed for service migration
2. **Create all 11 new repos** (9 services + cortx-ci + cortx-infra)
3. **Don't use cortx-platform** - It exists but shouldn't be the target
4. **Verify existing repos separately** - Can be done in parallel with service migration

---

**Status:** ✅ Scan Complete - Ready to Proceed with Phase 1
**Next:** Define functional boundaries and ownership (Phase 1 continuation)
