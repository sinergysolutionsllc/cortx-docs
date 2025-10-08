# Migration Plan: `/modules/reconciliation` → Archive

**Date:** October 7, 2025
**Status:** ⚠️ **Blocked - Active Dependency**

---

## Current State

### Active Usage

The `cortx_recon` module from `/modules/reconciliation` is currently:

1. **Imported by Gateway Service**
   - File: `services/gateway/app/main.py:28`
   - Import: `from cortx_recon.api.router import router as recon_router`

2. **Mounted as Router**
   - File: `services/gateway/app/main.py:115`
   - Mount: `app.include_router(recon_router, prefix="/recon", tags=["Reconciliation"])`

3. **Provides Endpoint**
   - Route: `POST /recon/validate`
   - Function: Validates reconciliation payloads using JSON rules

### Module Contents

```
modules/reconciliation/
├── cortx_recon/
│   ├── api/router.py          # FastAPI router (POST /validate)
│   ├── engine/validator.py    # Validation orchestrator
│   ├── validators/            # Domain validators (TAS, period, etc.)
│   │   ├── tas.py
│   │   └── period.py
│   ├── models/request.py      # Pydantic models
│   └── ai/rag_provider.py     # OLD Gemini/FAISS RAG (deprecated)
└── README.md
```

---

## Why This is Legacy

1. **Old AI Stack**
   - Uses Google Gemini (platform now uses Claude/Anthropic)
   - Uses FAISS vectors (platform now uses pgvector)
   - Uses LangChain (may be superseded)

2. **Architectural Mismatch**
   - Validation logic should be in Validation service (8083)
   - Not following microservices pattern
   - Mixed with deprecated RAG implementation

3. **Duplicate Functionality**
   - Validation Service (8083) handles RulePack execution
   - This module provides redundant validation endpoint

---

## Migration Steps

### Phase 1: Assess Current Usage ✅

- [x] Identify all imports and references
- [x] Document active endpoints
- [x] Verify functionality overlap

### Phase 2: Remove Gateway Dependency (1 hour)

- [ ] Comment out import in `services/gateway/app/main.py:28`
- [ ] Comment out router mount in `services/gateway/app/main.py:115`
- [ ] Test Gateway startup without cortx_recon
- [ ] Verify no other services depend on `/recon` endpoint

### Phase 3: Decision Point

**Option A:** Migrate validation logic to Validation service

- Extract validators from `cortx_recon/validators/`
- Move to `services/validation/app/validators/` or `packages/cortx_rulepack_sdk/validators/`
- Update imports and tests
- Add equivalent endpoint to Validation service

**Option B:** Delete if functionality exists elsewhere

- Verify Validation service provides equivalent functionality
- Check if FedReconcile suite has its own reconciliation logic
- Confirm no unique business logic will be lost

### Phase 4: Archive and Clean Up

- [ ] Create archive directory
- [ ] Move modules/ to archive/modules_legacy/
- [ ] Add DEPRECATED.md explaining migration
- [ ] Update .gitignore to exclude archive/
- [ ] Remove from active codebase

---

## Risk Assessment

### Low Risk

- Module is isolated (only Gateway imports it)
- Functionality appears to be superseded by Validation service
- No other services depend on it

### Medium Risk

- May contain domain-specific validation rules for GTAS reconciliation
- Could have unique business logic not yet migrated

### Mitigation

- **Extract and preserve** any unique validators before deletion
- **Document** any GTAS-specific validation rules
- **Verify** with FedReconcile suite implementation

---

## Validation Before Deletion

Before archiving, verify:

1. **Gateway still works** without cortx_recon import
2. **Validation service** provides equivalent functionality via RulePack execution
3. **FedReconcile suite** has its own reconciliation logic in separate repo
4. **No unique business rules** are lost

---

## Recommended Action

1. **Immediate:** Comment out Gateway imports (non-breaking)
2. **Short-term:** Extract any unique validation logic to Validation service
3. **Archive:** Move to `archive/modules_legacy/` once verified safe
4. **Document:** Update migration notes in SESSION_SUMMARY

---

## Notes

- The `cortx_core` dependency in router.py also suggests this predates the current microservices architecture
- The RAG provider using Gemini confirms this is from an earlier platform iteration
- The validation engine pattern should be preserved in the Validation service if not already present

---

**Created:** 2025-10-07
**Author:** AI Documentation Agent
**Status:** Awaiting manual verification before archival
