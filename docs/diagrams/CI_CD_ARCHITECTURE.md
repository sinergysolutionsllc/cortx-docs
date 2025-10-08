# CI/CD Pipeline Architecture

**CORTX Platform Automated Testing and Coverage Pipeline**

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CORTX Platform CI/CD                            │
│                                                                         │
│  Developer → Pre-commit Hooks → Git Push → GitHub Actions → Codecov   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Architecture Diagram

```
                                CORTX Platform
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
              Local Development                  GitHub Repository
                    │                                   │
    ┌───────────────┴───────────────┐      ┌───────────┴───────────┐
    │                               │      │                       │
    │  1. Pre-commit Hooks          │      │  2. GitHub Actions    │
    │     • black (format)          │      │     • Test Workflows  │
    │     • ruff (lint)             │      │     • Coverage Upload │
    │     • mypy (types)            │      │     • Quality Gates   │
    │     • isort (imports)         │      │                       │
    │     • bandit (security)       │      │                       │
    │     • 13 more hooks...        │      │                       │
    │                               │      │                       │
    └───────────────┬───────────────┘      └───────────┬───────────┘
                    │                                   │
                    │ git commit                    git push
                    │                                   │
                    ▼                                   ▼
            ┌──────────────┐                  ┌──────────────────┐
            │ Local Tests  │                  │  CI/CD Pipeline  │
            │  • pytest    │                  │   9 Services     │
            │  • coverage  │                  │   Parallel Exec  │
            └──────────────┘                  └────────┬─────────┘
                                                       │
                                   ┌───────────────────┼───────────────────┐
                                   │                   │                   │
                              Test Results      Coverage Data        Artifacts
                                   │                   │                   │
                                   ▼                   ▼                   ▼
                            ┌────────────┐      ┌──────────┐      ┌──────────┐
                            │  GitHub    │      │ Codecov  │      │ GitHub   │
                            │  Checks    │      │ Dashboard│      │ Artifacts│
                            └────────────┘      └──────────┘      └──────────┘
```

## Workflow Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Trigger: Push or PR to main                         │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
            ┌────────────────────────────────────┐
            │  Path Filter: services/**          │
            │  Determine which services changed  │
            └────────────┬───────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
  Changed Services              test-all-services.yml
         │                               │
         ▼                               ▼
┌────────────────────┐         ┌──────────────────────┐
│ Individual Service │         │  Matrix Strategy:    │
│ Workflows          │         │  - ai-broker         │
│                    │         │  - compliance        │
│ Example:           │         │  - gateway           │
│ test-gateway.yml   │         │  - identity          │
│                    │         │  - ledger            │
│ Steps:             │         │  - ocr               │
│ 1. Checkout        │         │  - rag               │
│ 2. Setup Python    │         │  - validation        │
│ 3. Install deps    │         │  - workflow          │
│ 4. Lint (ruff)     │         │                      │
│ 5. Type check      │         │  All run in parallel │
│ 6. Run tests       │         └──────────┬───────────┘
│ 7. Upload coverage │                    │
│ 8. Check threshold │                    │
└─────────┬──────────┘                    │
          │                               │
          │    ┌──────────────────────────┘
          │    │
          ▼    ▼
    ┌─────────────────────────────┐
    │  All Services Complete      │
    │  (Success or Failure)       │
    └────────────┬────────────────┘
                 │
         ┌───────┴────────┐
         │                │
         ▼                ▼
  ┌──────────────┐  ┌─────────────────┐
  │ Aggregate    │  │ Quality Gate    │
  │ Results      │  │ Check           │
  │              │  │                 │
  │ - Download   │  │ If any service  │
  │   artifacts  │  │ fails:          │
  │ - Calculate  │  │   ❌ Fail build │
  │   average    │  │                 │
  │ - Generate   │  │ If all pass:    │
  │   summary    │  │   ✅ Pass build │
  │ - Post PR    │  └─────────────────┘
  │   comment    │
  └──────────────┘
```

## Service Test Workflow Detail

```
┌─────────────────────────────────────────────────────────────┐
│              Individual Service Test Workflow               │
│              (e.g., test-gateway.yml)                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  Step 1: Checkout Repository  │
            │  actions/checkout@v4          │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  Step 2: Setup Python 3.11    │
            │  actions/setup-python@v5      │
            │  • Enable pip cache           │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  Step 3: Install Dependencies │
            │  • requirements.txt           │
            │  • requirements-dev.txt       │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  Step 4: Run Linting (ruff)   │
            │  • Non-blocking warnings      │
            │  • Continue on error          │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  Step 5: Type Check (mypy)    │
            │  • Non-blocking warnings      │
            │  • Continue on error          │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  Step 6: Run Tests (pytest)   │
            │  • Execute all tests          │
            │  • Collect coverage           │
            │  • Generate XML + HTML        │
            │  • Fail if coverage < 80%     │
            └───────────────┬───────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
    ┌─────────────────────┐   ┌───────────────────┐
    │  Step 7: Upload     │   │  Step 8: Upload   │
    │  to Codecov         │   │  Artifacts        │
    │  • coverage.xml     │   │  • coverage.xml   │
    │  • Service flag     │   │  • htmlcov/       │
    │  • Component name   │   │  • 30-day retain  │
    └─────────────────────┘   └───────────────────┘
                │                       │
                └───────────┬───────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  Step 9: Check Threshold      │
            │  coverage report              │
            │  --fail-under=80              │
            │                               │
            │  ✅ Pass: ≥80%                │
            │  ❌ Fail: <80%                │
            └───────────────────────────────┘
```

## Coverage Reporting Flow

```
┌────────────────────────────────────────────────────────────┐
│                   Coverage Reporting Flow                  │
└────────────────────────────┬───────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │  pytest generates        │
              │  • coverage.xml          │
              │  • htmlcov/index.html    │
              └──────────┬───────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│  Upload to       │          │  Upload to       │
│  Codecov         │          │  GitHub Actions  │
│                  │          │  Artifacts       │
│  • Parse XML     │          │                  │
│  • Track changes │          │  • Store reports │
│  • Flag service  │          │  • 30-day access │
│  • Component map │          │  • Download link │
└────────┬─────────┘          └────────┬─────────┘
         │                             │
         ▼                             ▼
┌──────────────────┐          ┌──────────────────┐
│  Codecov         │          │  Artifacts       │
│  Dashboard       │          │  Storage         │
│                  │          │                  │
│  • Graphs        │          │  • Historical    │
│  • Trends        │          │  • Debugging     │
│  • Comparisons   │          │  • Audit trail   │
│  • Sunburst      │          └──────────────────┘
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  PR Integration  │
│                  │
│  • Status checks │
│  • Comments      │
│  • Coverage diff │
│  • File changes  │
└──────────────────┘
```

## Aggregated Report Generation

```
┌────────────────────────────────────────────────────────────┐
│        Aggregated Coverage Report (test-all-services)      │
└────────────────────────────┬───────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │  aggregate-results job   │
              │  Depends on: all tests   │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │  Download all artifacts  │
              │  • ai-broker coverage    │
              │  • compliance coverage   │
              │  • gateway coverage      │
              │  • ... 6 more services   │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │  Parse coverage.xml      │
              │  Extract line-rate       │
              │  Calculate percentages   │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │  Generate markdown       │
              │  • Service table         │
              │  • Status indicators     │
              │  • Average coverage      │
              │  • Quality threshold     │
              └──────────┬───────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│  GitHub Step     │          │  PR Comment      │
│  Summary         │          │  (if PR)         │
│                  │          │                  │
│  Visible in:     │          │  Posted to:      │
│  • Workflow UI   │          │  • Pull request  │
│  • Summary tab   │          │  • Discussion    │
└──────────────────┘          └──────────────────┘
         │
         ▼
┌──────────────────┐
│  Upload artifact │
│  • 90-day retain │
│  • Historical    │
└──────────────────┘
```

## Pre-commit Hooks Flow

```
┌────────────────────────────────────────────────────────────┐
│                    Developer Workflow                      │
└────────────────────────────┬───────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │  git add .               │
              │  git commit -m "..."     │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │  Pre-commit triggers     │
              │  .pre-commit-config.yaml │
              └──────────┬───────────────┘
                         │
         ┌───────────────┴───────────────────────────┐
         │                                           │
         ▼                                           ▼
┌──────────────────┐                      ┌──────────────────┐
│  Python Checks   │                      │  File Checks     │
│                  │                      │                  │
│  1. black        │                      │  6. whitespace   │
│  2. ruff         │                      │  7. EOF fixer    │
│  3. mypy         │                      │  8. YAML check   │
│  4. isort        │                      │  9. JSON check   │
│  5. bandit       │                      │  10. TOML check  │
│                  │                      │  11. large files │
│  ↓ Auto-fix      │                      │  12. conflicts   │
│  ↓ Re-stage      │                      │  13. case check  │
└────────┬─────────┘                      │  14. line ending │
         │                                │  15. private key │
         │                                └────────┬─────────┘
         │                                         │
         ├─────────────────────────────────────────┤
         │                                         │
         ▼                                         ▼
┌──────────────────┐                      ┌──────────────────┐
│  Doc Checks      │                      │  Container Check │
│                  │                      │                  │
│  16. markdownlint│                      │  18. hadolint    │
│  17. YAML format │                      │      (Dockerfile)│
└────────┬─────────┘                      └────────┬─────────┘
         │                                         │
         └─────────────────┬───────────────────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │  All Checks Pass?    │
                └──────────┬───────────┘
                           │
                  ┌────────┴────────┐
                  │                 │
                  ▼                 ▼
            ┌──────────┐      ┌──────────┐
            │   YES    │      │    NO    │
            │          │      │          │
            │ Proceed  │      │  Fix     │
            │ with     │      │  issues  │
            │ commit   │      │  retry   │
            └──────────┘      └──────────┘
```

## Trigger Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                       Workflow Triggers                         │
├─────────────────┬───────────────┬───────────────┬───────────────┤
│ Trigger Type    │ Individual    │ All Services  │ Pre-commit    │
│                 │ Service       │ Orchestrator  │ Hooks         │
├─────────────────┼───────────────┼───────────────┼───────────────┤
│ Push to main    │ ✅ (if path   │ ✅            │ ❌            │
│                 │    matches)   │               │               │
├─────────────────┼───────────────┼───────────────┼───────────────┤
│ Pull Request    │ ✅ (if path   │ ✅            │ ❌            │
│                 │    matches)   │               │               │
├─────────────────┼───────────────┼───────────────┼───────────────┤
│ Schedule        │ ❌            │ ✅ (daily)    │ ❌            │
│ (cron)          │               │               │               │
├─────────────────┼───────────────┼───────────────┼───────────────┤
│ Manual          │ ❌            │ ✅            │ ❌            │
│ (dispatch)      │               │               │               │
├─────────────────┼───────────────┼───────────────┼───────────────┤
│ git commit      │ ❌            │ ❌            │ ✅            │
│ (local)         │               │               │               │
└─────────────────┴───────────────┴───────────────┴───────────────┘
```

## Quality Gate Decision Tree

```
                     ┌─────────────────┐
                     │  Run All Tests  │
                     └────────┬────────┘
                              │
                     ┌────────▼────────┐
                     │  All Tests Pass? │
                     └────────┬────────┘
                              │
                  ┌───────────┴───────────┐
                  │                       │
                  ▼                       ▼
            ┌──────────┐            ┌──────────┐
            │   YES    │            │    NO    │
            └─────┬────┘            └─────┬────┘
                  │                       │
                  ▼                       ▼
      ┌─────────────────────┐   ┌──────────────────┐
      │ Coverage ≥ 80%?     │   │ ❌ FAIL BUILD    │
      └─────────┬───────────┘   │ Fix failing tests│
                │               └──────────────────┘
    ┌───────────┴───────────┐
    │                       │
    ▼                       ▼
┌─────────┐           ┌─────────┐
│   YES   │           │   NO    │
└────┬────┘           └────┬────┘
     │                     │
     ▼                     ▼
┌─────────────┐   ┌───────────────────┐
│ Linting OK? │   │ ❌ FAIL BUILD     │
└────┬────────┘   │ Increase coverage │
     │            └───────────────────┘
     ▼
┌───────────┐
│ ⚠️ Warn   │ (non-blocking)
│ ✅ Continue
└────┬──────┘
     │
     ▼
┌───────────────┐
│ Type Check OK?│
└────┬──────────┘
     │
     ▼
┌───────────┐
│ ⚠️ Warn   │ (non-blocking)
│ ✅ Continue
└────┬──────┘
     │
     ▼
┌──────────────────┐
│ ✅ PASS BUILD    │
│ All checks pass  │
│ Coverage ≥ 80%   │
└──────────────────┘
```

## Service Dependency Graph

```
┌────────────────────────────────────────────────────────────────┐
│                    Service Test Dependencies                   │
└────────────────────────────────────────────────────────────────┘

Each service test is INDEPENDENT (no dependencies between services):

ai-broker ──────┐
compliance ─────┤
gateway ────────┤
identity ───────┤
ledger ─────────┼──→ All run in parallel ──→ aggregate-results
ocr ────────────┤
rag ────────────┤
validation ─────┤
workflow ───────┘

Benefits:
  • Faster execution (parallel processing)
  • Independent failures (one failure doesn't block others)
  • Scalable (easy to add more services)
  • Isolated debugging (clear failure source)
```

## Coverage Threshold Enforcement

```
┌────────────────────────────────────────────────────────────────┐
│               Coverage Threshold Enforcement Points            │
└────────────────────────────────────────────────────────────────┘

1. Local Development (Pre-commit)
   └─→ pytest --cov=app --cov-fail-under=80
       ❌ Blocks commit if <80%

2. GitHub Actions (Per Service)
   └─→ pytest --cov=app --cov-fail-under=80
       ❌ Fails workflow if <80%

3. GitHub Actions (Final Check)
   └─→ coverage report --fail-under=80
       ❌ Double-check threshold

4. Codecov (Project Level)
   └─→ Project target: 80%
       ❌ Status check fails if <80%

5. Codecov (Patch Level)
   └─→ Patch target: 80% (new code)
       ❌ Status check fails if <80%

6. Codecov (Per Component)
   └─→ Each service target: 80%
       ❌ Component check fails if <80%

Result: Multiple layers of protection ensure coverage never drops below 80%
```

## Data Flow Diagram

```
┌───────────────────────────────────────────────────────────────────┐
│                          Data Flow                                │
└───────────────────────────────────────────────────────────────────┘

Source Code
    │
    ▼
┌─────────────┐
│ Test Suite  │
└──────┬──────┘
       │
       ▼
┌──────────────┐     coverage.py
│ pytest       │─────────────────┐
└──────┬───────┘                 │
       │                         ▼
       ├────────────────→ ┌──────────────┐
       │                  │ coverage.xml │
       │                  └──────┬───────┘
       │                         │
       ▼                         ├────→ Codecov
┌──────────────┐                 │     (cloud)
│ Test Results │                 │
│ (pass/fail)  │                 ├────→ GitHub
└──────┬───────┘                 │     Artifacts
       │                         │
       ├────────────────→ ┌──────▼───────┐
       │                  │ htmlcov/     │
       │                  │ (HTML report)│
       │                  └──────────────┘
       │
       ▼
┌──────────────────┐
│ GitHub Actions   │
│ Status Checks    │
│ (pass/fail)      │
└──────────────────┘
```

## Timeline View

```
┌───────────────────────────────────────────────────────────────────┐
│               Typical CI/CD Execution Timeline                    │
└───────────────────────────────────────────────────────────────────┘

T+0:00  Developer commits code (pre-commit hooks run locally)
  │     └─→ black, ruff, mypy, isort (~30 seconds)
  │
T+0:01  git push triggers GitHub Actions
  │
T+0:02  All 9 service workflows start in parallel
  │     ├─→ Checkout code
  │     ├─→ Setup Python + cache
  │     └─→ Install dependencies
  │
T+1:00  Dependencies installed (cached, fast)
  │
T+1:30  Linting and type checking complete
  │     ├─→ ruff check
  │     └─→ mypy
  │
T+2:00  Tests start running
  │     └─→ pytest with coverage
  │
T+4:00  Tests complete
  │     ├─→ Fastest service: ~3 min
  │     └─→ Slowest service: ~4 min
  │
T+4:30  Coverage upload complete
  │     ├─→ Codecov upload
  │     └─→ Artifact upload
  │
T+5:00  aggregate-results job starts
  │     ├─→ Download artifacts
  │     ├─→ Parse coverage
  │     ├─→ Generate summary
  │     └─→ Post PR comment
  │
T+6:00  quality-gate check runs
  │     └─→ Verify all services passed
  │
T+6:30  ✅ All workflows complete
        └─→ Green checkmark or red X
```

## References

- Full Documentation: `/docs/operations/CI_CD_SETUP.md`
- Implementation Summary: `/CI_CD_IMPLEMENTATION_SUMMARY.md`
- Setup Checklist: `/CI_CD_SETUP_CHECKLIST.md`
- Test Plan: `/docs/tracking/CORTX_PLATFORM_QUALITY_HARDENING_TEST_PLAN.md`

---

**Last Updated**: 2025-10-08
**Version**: 1.0.0
