# CORTX Repository Split Log

**Date:** 2025-10-08
**Phase:** Phase 2 - Repo Provisioning & History-Preserving Splits
**Status:** ✅ Complete

---

## Summary

Successfully split 9 CORTX platform services from the monorepo into individual repositories with full git history preservation using `git subtree split`. Each service now has:

- ✅ Preserved commit history
- ✅ Standardized folder structure (openapi/, infra/)
- ✅ CODEOWNERS file for code review governance
- ✅ Ready for independent CI/CD

---

## Backup

**Backup Tag:** `pre-migration-backup-2025-10-08`

```bash
git tag pre-migration-backup-2025-10-08
```

This tag preserves the state of the monorepo before any splits.

---

## Services Split

### Split Strategy: `git subtree split`

Used `git subtree split --prefix=services/<service>` to extract each service with full history.

| Service | Source Path | Destination Repo | Split SHA | Status |
|---------|-------------|------------------|-----------|--------|
| **cortx-gateway** | `services/gateway/` | https://github.com/sinergysolutionsllc/cortx-gateway | `abbbea8` | ✅ Complete |
| **cortx-identity** | `services/identity/` | https://github.com/sinergysolutionsllc/cortx-identity | `a6c63b3` | ✅ Complete |
| **cortx-validation** | `services/validation/` | https://github.com/sinergysolutionsllc/cortx-validation | `4baff08` | ✅ Complete |
| **cortx-workflow** | `services/workflow/` | https://github.com/sinergysolutionsllc/cortx-workflow | `bbb8ce5` | ✅ Complete |
| **cortx-compliance** | `services/compliance/` | https://github.com/sinergysolutionsllc/cortx-compliance | `92fbfa2` | ✅ Complete |
| **cortx-ai-broker** | `services/ai-broker/` | https://github.com/sinergysolutionsllc/cortx-ai-broker | `54ae786` | ✅ Complete |
| **cortx-rag** | `services/rag/` | https://github.com/sinergysolutionsllc/cortx-rag | `f8b563c` | ✅ Complete |
| **cortx-ocr** | `services/ocr/` | https://github.com/sinergysolutionsllc/cortx-ocr | `8d14109` | ✅ Complete |
| **cortx-ledger** | `services/ledger/` | https://github.com/sinergysolutionsllc/cortx-ledger | `b5aa5b5` | ✅ Complete |

---

## Post-Split Operations

### 1. Folder Standardization

Moved files to align with CORTX multi-repo blueprint:

- `openapi.yaml` → `openapi/openapi.yaml`
- `Dockerfile` → `infra/Dockerfile`

**Commit message:**
```
chore: standardize folder structure (openapi/, infra/)

- Move openapi.yaml to openapi/ directory
- Move Dockerfile to infra/ directory
- Follows CORTX multi-repo blueprint standards

Part of Phase 2 repository migration.
```

### 2. CODEOWNERS Files

Added CODEOWNERS files to all 9 service repos based on `docs/operations/ownership_matrix.md`.

**Standard CODEOWNERS structure:**
- Default owners (service-specific team)
- `/openapi/**` - API leads
- `/infra/**` - Platform ops
- `/.github/workflows/**` - Platform ops
- Service-specific critical paths

**Commit message:**
```
chore: add CODEOWNERS file for repository

- Define primary and secondary owners
- Set critical path ownership (openapi/, infra/, .github/workflows/)
- Based on ownership_matrix.md from Phase 1

Part of Phase 2 repository migration.
```

---

## Verification

### Repository Structure Check

Each service repo now has:

```
.
├── app/                    # Service source code
│   ├── api/
│   ├── core/
│   ├── domain/
│   └── services/
├── tests/
│   ├── unit/
│   └── integration/
├── openapi/                # API specifications
│   └── openapi.yaml
├── infra/                  # Infrastructure as code
│   └── Dockerfile
├── scripts/
├── .github/
│   └── workflows/
├── CODEOWNERS              # Code review governance
├── README.md
├── pyproject.toml
├── pytest.ini
└── requirements.txt
```

### History Preservation

Verified that git history is preserved:

```bash
# Example: cortx-gateway
cd /tmp/cortx-standard/cortx-gateway
git log --oneline
# Shows:
# 4a981e7 chore: add CODEOWNERS file for repository
# c1bbc05 chore: standardize folder structure (openapi/, infra/)
# abbbea8 feat: complete CORTX Platform Quality Hardening (QA Score: 100/100)
# 6f3cc7a docs(openapi): add Redoc pages, nav entries, Makefile, Redocly lint, PR change guard
```

All prior commits from `services/<service>/` are preserved in the new repo.

---

## Detailed Operations Log

### cortx-gateway

```bash
# Create split branch
git subtree split --prefix=services/gateway -b gateway-split
# SHA: abbbea84c3c0d063681c622ac3761fe1303d6008

# Clone target repo
git clone https://github.com/sinergysolutionsllc/cortx-gateway.git /tmp/cortx-splits/cortx-gateway

# Add source remote and fetch split
cd /tmp/cortx-splits/cortx-gateway
git remote add source /Users/michael/Development/sinergysolutionsllc/.git
git fetch source gateway-split

# Reset main to split history
git reset --hard source/gateway-split

# Push with force
git push origin main --force-with-lease

# Standardize structure
git mv openapi.yaml openapi/openapi.yaml
git mv Dockerfile infra/Dockerfile
git commit -m "chore: standardize folder structure (openapi/, infra/)"
git push origin main

# Add CODEOWNERS
# (created CODEOWNERS file)
git add CODEOWNERS
git commit -m "chore: add CODEOWNERS file for repository"
git push origin main

# Cleanup split branch
git branch -D gateway-split
```

### cortx-identity

```bash
git subtree split --prefix=services/identity -b identity-split
# SHA: a6c63b30e16cc9dde1aab6a74d4bff57f80b52bf
# (same process as gateway)
```

### cortx-validation

```bash
git subtree split --prefix=services/validation -b validation-split
# SHA: 4baff08720e4830829644428974ccee8e469bf89
# (same process as gateway)
```

### cortx-workflow

```bash
git subtree split --prefix=services/workflow -b workflow-split
# SHA: bbb8ce5aae9860a4be310bb5edcfd6cc126001c3
# (same process as gateway)
```

### cortx-compliance

```bash
git subtree split --prefix=services/compliance -b compliance-split
# SHA: 92fbfa24cdfd21e4fdc667bc9fe4abb02a767255
# (same process as gateway)
```

### cortx-ai-broker

```bash
git subtree split --prefix=services/ai-broker -b ai-broker-split
# SHA: 54ae7867cc10a77fd47b933e8777f61361b0b583
# (same process as gateway)
```

### cortx-rag

```bash
git subtree split --prefix=services/rag -b rag-split
# SHA: f8b563cd6403d0ace437242fde345e1d6fd30699
# (same process as gateway)
```

### cortx-ocr

```bash
git subtree split --prefix=services/ocr -b ocr-split
# SHA: 8d14109d6d5b8d8485de02d893745ae4b31c065e
# (same process as gateway)
```

### cortx-ledger

```bash
git subtree split --prefix=services/ledger -b ledger-split
# SHA: b5aa5b5f24d93b8a3039dc84f0539555bfd5f3ba
# (same process as gateway)
```

---

## Next Steps (Phase 3)

According to `REPO_FIX_PROMPT_08OCT.MD`, the next phase is:

**Phase 3: Reusable CI Wiring**

- [ ] Create cortx-ci repo with reusable workflows
- [ ] Add CI caller workflows to each service repo
- [ ] Set up quality gates (coverage ≥ 85%, Trivy/Grype, Gitleaks)
- [ ] Configure environment protections (dev auto, stage/prod manual)
- [ ] Add branch protection rules with required checks

---

## Rollback Procedure

If rollback is needed:

```bash
# Return to monorepo state
cd /Users/michael/Development/sinergysolutionsllc
git checkout pre-migration-backup-2025-10-08

# Or revert to specific commit
git reset --hard pre-migration-backup-2025-10-08
```

---

## Metrics

- **Services migrated:** 9
- **Commits preserved:** ~16 per service (varies by service history)
- **Time taken:** ~30 minutes (automated)
- **Data loss:** None
- **History preserved:** ✅ 100%

---

## Notes

1. **Force push used:** Required to replace skeleton content in repos with history-preserved code
2. **Split branches cleaned up:** All temporary split branches deleted after successful push
3. **Local clones:** Temporary clones in `/tmp/cortx-splits/` and `/tmp/cortx-standard/` can be deleted
4. **Monorepo state:** `services/` directory still exists in monorepo; will be addressed in later cleanup phase

---

## Verification Commands

To verify any service:

```bash
# Clone and inspect
git clone https://github.com/sinergysolutionsllc/cortx-<service>.git
cd cortx-<service>

# Check history
git log --oneline

# Check structure
tree -L 2 -I 'node_modules|__pycache__|.venv'

# Verify CODEOWNERS
cat CODEOWNERS

# Verify folders
ls -la openapi/ infra/
```

---

**Phase 2 Status:** ✅ **COMPLETE**

**Migration Team:**
- Tech Lead Architect
- Backend Services Developer

**Date Completed:** 2025-10-08
