# CORTX Ecosystem Refactoring Analysis
**Date:** 2025-10-01
**Status:** Draft
**Team:** Tech Architect, Backend Services Dev, Functional Lead

---

## Executive Summary

This document provides a comprehensive analysis of the CORTX ecosystem refactoring effort, examining:
1. **Platform Centralization**: What services should be centralized in cortx-platform
2. **Module Boundaries**: Where each module should live in the new structure
3. **Shared Code Extraction**: What common code should be extracted into SDKs/packages

### Key Findings (In Progress)
- **High Code Duplication**: Auth, AI/RAG, validation, config, logging duplicated across 7+ repos
- **Unclear Boundaries**: Platform services vs module code mixed together
- **Multiple FedTransform versions**: Need to consolidate Asset Development and Development copies
- **Greenlight duplicates**: Two versions at different locations

---

## 1. TECH ARCHITECT PERSPECTIVE: Platform Centralization

### Analysis Methodology
Review each repository to identify:
- Authentication & authorization code → **Identity Service (8082)**
- AI/RAG services → **AI Broker Service (8085)**
- Validation engines → **Validation Service (8083)**
- Workflow orchestration → **Workflow Service (8130)**
- Compliance/audit logging → **Compliance Service (8135)**
- Configuration management → **Platform-level**
- Common middleware → **Gateway Service (8080)**

### 1.1 Authentication & Authorization Code

#### Current State
**Locations identified:**
```
cortx-suites/fedsuite/auth/
├── jwt_auth.py
├── federated_auth.py
├── federated_auth_fastapi.py
└── session_manager.py

cortx-suites/fedsuite/middleware/
└── auth_fastapi.py

cortx-propverify/backend/common/
├── auth.py
└── tokens.py

deprecated-cortx-development/app/auth/
├── federated_auth.py
└── session_manager.py
```

#### Recommendation
**Target**: cortx-platform Identity Service (port 8082)

**Files to centralize:**
- JWT validation & token generation
- Session management
- Federated auth (OAuth/OIDC)
- RBAC enforcement

**Keep in modules:**
- Module-specific permission checks
- Custom auth decorators (if module-specific roles exist)

**Priority:** **HIGH** - Foundational service

---

### 1.2 AI/RAG Services

#### Current State
**Locations identified:**
```
cortx-suites/fedsuite/ai/
├── ai_helper.py
├── ai_rag_engine.py
├── compliance_assistant.py
├── correction_generator.py
├── explanation_engine.py
├── intelligent_corrections.py
├── sync_rag_wrapper.py

cortx-platform/modules/reconciliation/cortx_recon/ (?)

cortx-propverify/backend/ai_svc/
├── app/
├── clients/
└── pii_detector.py

FedTransform/backend/
├── ai_service.py
├── ai_service_ollama.py
├── ai_service_smart.py
├── embedding_service.py
├── ai_rag_engine.py (?)

deprecated-cortx-development/app/ai/
└── (similar files)
```

#### Recommendation
**Target**: 
- **cortx-platform AI Broker Service (port 8085)** for model routing, safety, and provider policy, and 
- **cortx-platform RAG Service (port 8138)** for ingestion, chunking, embeddings, and hierarchical retrieval.

**Core services to centralize (split of concerns):**
- **AI Broker (8085):** Provider allowlist, model routing (Gemini/Claude/GPT-4), safety/PII redaction, prompt template library, response caching.
- **RAG (8138):** Vector store admin (pgvector), document ingestion (upload + crawl), semantic chunking, embedding generation, **4-level hierarchical retrieval** (Platform → Suite → Module → Entity) with specificity boosts.

**Module-specific AI code to keep:**
- Domain-specific prompt templates
- Module-specific fine-tuning or model selection logic
- Specialized correction generators (GTAS vs HIPAA vs PropVerify)
- Module-scoped knowledge seeds (stored under Module/Suite scopes in RAG)

**Priority:** **HIGH** - Heavy duplication

**Outcome of refactor:** All modules call the **AI Broker** for generation and the **RAG Service** for retrieval; no module maintains its own embeddings or ad-hoc vector DB.

---

### 1.3 Validation Engines

#### Current State
**Locations identified:**
```
cortx-suites/fedsuite/utils/
├── validation_engine.py
├── treasury_validation_engine.py
├── validation_logic.py

cortx-suites/fedsuite/security/
└── safe_rule_engine.py

cortx-propverify/backend/validation_svc/
├── app/
└── clients/

compliance-scanner/scanner/
└── engine.py
```

#### Recommendation
**Target**: cortx-platform Validation Service (port 8083)

**Core engine to centralize:**
- RulePack execution engine (safe operators)
- Rule parsing and validation
- Batch validation
- Result aggregation

**Module-specific validators to keep:**
- Domain-specific validation logic (GTAS rules, HIPAA rules, SDAT rules)
- These become **RulePacks** stored in cortx-packs repository

**Priority:** **MEDIUM** - Core platform capability

---

### 1.4 Workflow Orchestration

#### Current State
**Locations identified:**
```
cortx-propverify/backend/workflow_svc/
├── app/
└── clients/

cortx-suites/fedsuite/ (various workflow-related files)
└── cross_suite_integration.py
```

#### Recommendation
**Target**: cortx-platform Workflow Service (port 8130)

**Core orchestration to centralize:**
- WorkflowPack execution engine
- Step sequencing (parallel, sequential)
- Saga pattern for distributed transactions
- State machine management
- Human-in-the-loop approval gates

**Module-specific workflows to keep:**
- Specific workflow definitions (stored as WorkflowPacks in cortx-packs)
- Module-specific step implementations

**Priority:** **MEDIUM** - Platform core

---

### 1.5 Compliance & Audit Logging

#### Current State
**Locations identified:**
```
cortx-suites/fedsuite/utils/
└── audit_compliance.py

cortx-suites/fedsuite/middleware/
└── logging_fastapi.py

cortx-platform (currently no dedicated compliance service)
```

#### Recommendation
**Target**: cortx-platform Compliance Service (port 8135)

**Core compliance features to centralize:**
- Immutable audit trail
- NIST 800-53 control evidence collection
- Compliance report generation (FedRAMP, HIPAA, SOC 2)
- Log aggregation and retention

**Companion Service:** Promote **Ledger Service (8136)** for append-only, hash-chained compliance evidence shared across suites.

**Priority:** **HIGH** - Regulatory requirement

---

### 1.6 Configuration Management

#### Current State
**Locations identified:**
```
cortx-suites/fedsuite/config/
├── config.py
├── policies/
└── schemas/

cortx-propverify/backend/common/
└── config.py

FedTransform/backend/
└── database.py (config patterns)

greenlight/packages/config/
├── company.yml
├── keywords.yml
└── scoring.yml
```

#### Recommendation
**Target**: cortx-platform Schema Service (port 8084) + Config package

**Core config to centralize:**
- Environment-based settings (Pydantic Settings pattern)
- Secret management (GCP Secret Manager integration)
- Multi-tenant configuration
- Schema registry

**Module-specific config to keep:**
- Module-specific settings
- Domain configuration files (e.g., greenlight scoring.yml)

**Priority:** **MEDIUM**

---

### 1.7 Common Middleware

---
### 1.8 OCR Service (NEW)

#### Recommendation
**Target**: **cortx-platform OCR Service (port 8137)**

**Rationale:** OCR is a cross-cutting concern needed by PropVerify (land records), FedTransform (legacy reports), and future Claims modules. Centralizing it avoids duplicate engines and normalizes extraction outputs into a shared `DocumentExtraction` schema for downstream RAG ingestion.

#### Current State
**Locations identified:**
```
cortx-suites/fedsuite/middleware/
├── auth_fastapi.py
└── logging_fastapi.py

cortx-suites/fedsuite/security/
├── cors_config.py
├── rate_limiter.py
└── secret_manager.py

cortx-propverify/backend/common/
├── middleware.py
├── logging.py
└── metrics.py
```

#### Recommendation
**Target**: cortx-platform Gateway Service (port 8080) + common package

**Core middleware to centralize:**
- Request logging
- CORS configuration
- Rate limiting
- Circuit breaker
- Request/response transformation

**Priority:** **HIGH** - Gateway is the entry point

---

## 2. BACKEND SERVICES DEVELOPER PERSPECTIVE: Code Structure

### Analysis Methodology
Examine actual code patterns, dependencies, and implementation details to determine:
- Code quality and maintainability
- Duplication vs variation
- Migration complexity
- Breaking changes

### 2.1 Common Utilities Analysis

#### File Helpers & Utilities
**Current locations:**
```
cortx-suites/fedsuite/utils/
├── file_helpers.py
├── json_sanitizer.py
├── port_finder.py
├── suppress_warnings.py
├── amounts.py

deprecated-cortx-development/app/utils/
├── file_helpers.py
├── logging.py
├── suppress_warnings.py
```

**Recommendation:**
Extract to `cortx-platform/packages/cortx_core/utils/`

---

### 2.2 Data Models & Schemas

**Current state:** Pydantic models and SQLAlchemy models scattered across repos

**Recommendation:**
- **cortx-sdks/sdk-python/cortx_sdk/models/** - Shared Pydantic schemas
- Each service maintains its own SQLAlchemy models (tenant-isolated)

---

### 2.3 Frontend Components

**Current state:**
```
cortx-platform/frontend/src/components/ (some components)
cortx-designer/frontend/src/components/ (different components)
cortx-propverify/ (has frontend but no shared component library)
```

**Recommendation:**
Create `cortx-platform/packages/ui-components` (React component library)

---

## 3. FUNCTIONAL LEAD PERSPECTIVE: Module Boundaries

### Analysis Methodology
Define clear boundaries for each module based on:
- Business domain
- User personas
- Data ownership
- Compliance requirements

### 3.1 FedSuite Modules

#### FedReconcile
**Current location:** `/Users/michael/Development/cortx-suites/fedsuite/`

**Business purpose:** GTAS trial balance reconciliation with Treasury ATB

**Recommended location:** `fedsuite/modules/fedreconcile/`

**Structure:**
```
fedsuite/
├── modules/
│   └── fedreconcile/
│       ├── src/
│       │   ├── reconciliation_engine.py
│       │   ├── gtas_parser.py
│       │   ├── tb_parser.py
│       │   └── diagnostic_engine.py
│       ├── rulepacks/ (GTAS-specific rules)
│       ├── workflows/ (GTAS-specific workflows)
│       ├── tests/
│       └── README.md
└── services/ (suite-level infrastructure)
    └── api.py
```

---

#### FedTransform
**Current locations:**
- `/Volumes/Dev Volume/Asset Development/FedTransform`
- `/Volumes/Dev Volume/Development/FedTransform`

**Business purpose:** Transform legacy data formats to FBDI-ready datasets for Oracle Cloud

**Recommended location:** `fedsuite/modules/fedtransform/`

**Action required:** Consolidate the two versions (likely Asset Development is newer based on timestamps)

---

### 3.2 CorpSuite Modules

#### PropVerify
**Current location:** `/Users/michael/Development/cortx-propverify`

**Business purpose:** Maryland land records title verification

**Recommended location:** `corpsuite/modules/propverify/`

**Notes:** Currently has full microservices structure (5 services). Evaluate which services are truly module-specific vs should use platform services.

---

#### Greenlight
**Current locations:**
- `/Users/michael/Development/greenlight`
- `/Volumes/Dev Volume/sinergy_dev/greenlight`

**Business purpose:** Vendor/go-to-market opportunity triage (SAM, eVA)

**Recommended location:** `corpsuite/modules/greenlight/`

**Action required:** Consolidate two versions

---

#### InvestmAit (OffermAit)
**Current location:** `/Users/michael/Development/OffermAit`

**Business purpose:** Real estate investment analysis (P/L, sensitivity)

**Recommended location:** `corpsuite/modules/investmait/`

**Notes:** Rename from OffermAit to InvestmAit for consistency

---

### 3.3 Cross-Vertical Module

#### Compliance Scanner
**Current location:** `/Users/michael/Development/compliance-scanner`

**Business purpose:** Static code analysis for FedRAMP/HIPAA/NIST compliance

**Question:** Is this a platform-level service or a module?

**Recommendation:** **Platform-level tool** - Move to `cortx-platform/tools/compliance-scanner/`

**Rationale:** Used across all suites for code compliance checking

---

## 4. KEY ARCHITECTURAL DECISIONS (RESOLVED)

### Decision 1: PropVerify Microservices ✅
**Decision:** Promote shared capabilities to platform and deprecate duplicates.

**Services to deprecate (use platform instead):**
- ❌ **ai_svc** → Use cortx-platform **AI Broker (8085)**
- ❌ **validation_svc** → Use cortx-platform **Validation Service (8083)**
- ❌ **workflow_svc** → Use cortx-platform **Workflow Service (8130)**

**Capabilities promoted to platform (immediately):**
- ✅ **OCR Service (8137)** – Centralized OCR (Tesseract + optional DocAI), outputs normalized `DocumentExtraction`
- ✅ **Ledger Service (8136)** – Append-only, SHA-256 hash-chained evidence for compliance across suites
- ✅ **RAG Service (8138)** – Centralized ingestion, embeddings, and **hierarchical retrieval** (Platform/Suite/Module/Entity)

**Module keeps (PropVerify-specific):**
- Maryland SDAT/MDLandRec **adapters** (ingestion connectors) living under `corpsuite/modules/propverify/ingestion/`
- Domain-specific RulePacks & WorkflowPacks

---

### Decision 2: FedTransform Consolidation ✅
**Decision:** Use `/Volumes/Dev Volume/Development/FedTransform` as canonical

**Rationale:** This version was being updated to align with UI Modernization Guide

**Action items:**
1. Copy Development version to target location
2. Update UI components to match UI_MODERNIZATION_GUIDE.md (Sinergy branding)
3. Archive Asset Development version
4. Verify UI components use:
   - Sinergy Teal (#00C2CB) and Federal Navy (#2D5972)
   - Space Grotesk (headings), DM Sans (buttons), IBM Plex Sans (body)
   - SS_Logo_Transparent.png branding
5. Extract existing FedTransform RAG scaffolding into platform **RAG Service (8138)**; keep module ontologies as Module-scope seeds.

---

### Decision 3: Suite-Level Architecture ✅

### Decision 4: Hierarchical RAG Service ✅
**Decision:** Extract RAG from FedTransform and centralize as **svc-rag (8138)** with 4-level scoping (Platform, Suite, Module, Entity) and specificity-boosted retrieval.
**Consequences:** Designer and all suites reference a single retrieval API; modules contribute scoped knowledge; AI Broker provides embeddings behind policy.

### Decision 5: Environment Strategy ✅
**Decision:** Adopt three-tier promotion (**dev → staging → prod**) with Vertex AI as primary provider; OpenAI permitted only in dev via broker flags; Cloud Run runtime; Cloud SQL + pgvector; Memorystore Redis Streams.
**Consequences:** Consistent compliance posture; simple demo checkpoints; portable AI providers behind the broker abstraction.

**Decision:** Domain-based architecture with centralized platform

**Domain Structure:**
```
fedsuite.ai        → FedSuite (FedReconcile, FedTransform)
medsuite.ai        → MedSuite (ClaimsVerify, HipaaAudit)
govsuite.ai        → GovSuite (TBD modules)
corpsuite.ai       → CorpSuite (PropVerify, Greenlight, InvestmAit)

platform.sinergysolutions.ai  → CORTX Platform (7 services)
designer.sinergysolutions.ai  → BPM Designer
```

**Recommendation:** See Section 6 for detailed suite architecture

---

## 5. SUITE ARCHITECTURE RECOMMENDATION

### 5.1 Multi-Domain Strategy

**Architecture Pattern:** Domain-per-suite with shared platform services

```
┌─────────────────────────────────────────────────────────────────┐
│                     DOMAIN ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│  fedsuite.ai (Federal)                                          │
│  ├── Next.js App → FedReconcile, FedTransform modules           │
│  ├── API calls → platform.sinergysolutions.ai/v1/*              │
│  └── Database: fedsuite schema in shared PostgreSQL             │
├─────────────────────────────────────────────────────────────────┤
│  corpsuite.ai (Corporate)                                       │
│  ├── Next.js App → PropVerify, Greenlight, InvestmAit          │
│  ├── API calls → platform.sinergysolutions.ai/v1/*              │
│  └── Database: corpsuite schema in shared PostgreSQL            │
├─────────────────────────────────────────────────────────────────┤
│  medsuite.ai (Healthcare)                                       │
│  ├── Next.js App → ClaimsVerify, HipaaAudit                     │
│  ├── API calls → platform.sinergysolutions.ai/v1/*              │
│  └── Database: medsuite schema in shared PostgreSQL             │
├─────────────────────────────────────────────────────────────────┤
│  govsuite.ai (State/Local Gov)                                  │
│  ├── Next.js App → TBD modules                                  │
│  ├── API calls → platform.sinergysolutions.ai/v1/*              │
│  └── Database: govsuite schema in shared PostgreSQL             │
├─────────────────────────────────────────────────────────────────┤
│  platform.sinergysolutions.ai (CORTX Platform)                  │
│  ├── Gateway (8080), Identity (8082), AI Broker (8085)          │
│  ├── Validation (8083), Workflow (8130), Compliance (8135)      │
│  ├── Schemas (8084), Ledger (8136), OCR (8137), RAG (8138)     │
│  └── Database: platform schema + tenant management              │
├─────────────────────────────────────────────────────────────────┤
│  designer.sinergysolutions.ai (BPM Designer)                    │
│  ├── React Flow canvas, AI assistant, Pack marketplace          │
│  └── Calls platform services for pack validation/testing        │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Suite Frontend Architecture

**Technology Stack:**
- **Framework:** Next.js 14 (App Router)
- **UI Library:** React + Tailwind CSS
- **Component Library:** `@sinergysolutions/ui-components` (shared)
- **API Client:** `@sinergysolutionsllc/cortx-sdk` (TypeScript SDK)
- **State Management:** React Query for server state, Zustand for client state
- **Auth:** JWT tokens from platform Identity Service

**Directory Structure (per suite):**
```
fedsuite/
├── frontend/
│   ├── src/
│   │   ├── app/                      # Next.js 14 App Router
│   │   │   ├── layout.tsx            # Root layout (Sinergy branding)
│   │   │   ├── page.tsx              # Suite landing page
│   │   │   ├── fedreconcile/         # FedReconcile module pages
│   │   │   └── fedtransform/         # FedTransform module pages
│   │   ├── components/               # Suite-specific components
│   │   ├── lib/                      # SDK client, utilities
│   │   └── styles/
│   │       ├── globals.css           # Sinergy brand styles
│   │       └── tailwind.config.js    # Sinergy colors/fonts
│   ├── public/
│   │   ├── SS_Logo_Transparent.png
│   │   └── SS-Icon-Transparent.png
│   └── package.json
├── modules/                           # Backend modules
│   ├── fedreconcile/
│   └── fedtransform/
└── README.md
```

### 5.3 Suite Backend Architecture

**Deployment Pattern:** Each suite is a single FastAPI application with module routers

```python
# fedsuite/backend/main.py
from fastapi import FastAPI
from modules.fedreconcile import router as fedreconcile_router
from modules.fedtransform import router as fedtransform_router

app = FastAPI(title="FedSuite API", version="1.0.0")

# Register module routers
app.include_router(fedreconcile_router, prefix="/v1/fedreconcile", tags=["fedreconcile"])
app.include_router(fedtransform_router, prefix="/v1/fedtransform", tags=["fedtransform"])
```

**Module Structure:**
```
fedsuite/modules/fedreconcile/
├── src/
│   ├── __init__.py
│   ├── router.py              # FastAPI router
│   ├── service.py             # Business logic
│   ├── models.py              # Data models
│   └── clients/               # External API clients (GTAS, Treasury)
├── rulepacks/                 # GTAS-specific validation rules
├── workflows/                 # GTAS-specific workflows
├── tests/
└── README.md
```

### 5.4 Database Strategy

**Multi-Tenant Schema-Per-Suite Pattern:**

```sql
-- PostgreSQL schemas
CREATE SCHEMA platform;        -- Platform services, tenant registry
CREATE SCHEMA fedsuite;        -- FedReconcile, FedTransform data
CREATE SCHEMA corpsuite;       -- PropVerify, Greenlight, InvestmAit data
CREATE SCHEMA medsuite;        -- ClaimsVerify, HipaaAudit data
CREATE SCHEMA govsuite;        -- GovSuite data
```

**Data Isolation:**
- Each suite operates in its own schema
- Platform services use `platform` schema for cross-cutting concerns
- RLS (Row-Level Security) within each schema for tenant isolation
- Tenant ID propagated via JWT claims

### 5.5 API Gateway Strategy

**Recommendation:** Single Gateway with domain-based routing

**Option A: Single Gateway at platform.sinergysolutions.ai (RECOMMENDED)**

```
platform.sinergysolutions.ai/v1/suites/fedsuite/*   → fedsuite backend
platform.sinergysolutions.ai/v1/suites/corpsuite/* → corpsuite backend
platform.sinergysolutions.ai/v1/suites/medsuite/*  → medsuite backend
platform.sinergysolutions.ai/v1/suites/govsuite/*  → govsuite backend
```

**Pros:**
- Single ingress point for monitoring, rate limiting, auth
- Centralized CORS, logging, metrics
- Easier certificate management
- Unified API documentation

**Cons:**
- Single point of failure (mitigated with GCP Cloud Run autoscaling)
- More complex routing logic

**Option B: Suite-Level Gateways (ALTERNATIVE)**

```
api.fedsuite.ai/*
api.corpsuite.ai/*
api.medsuite.ai/*
api.govsuite.ai/*
```

**Pros:**
- Suite autonomy
- Blast radius containment
- Independent scaling

**Cons:**
- More infrastructure overhead
- Duplicated middleware logic
- More complex monitoring

**RECOMMENDATION:** **Option A** (Single Gateway) for Phase 1, migrate to Option B if suite independence becomes critical.

### 5.6 Shared UI Component Library

**Location:** `cortx-platform/packages/ui-components/`

**Purpose:** Provide Sinergy-branded React components for all suites

**Components to include:**
```typescript
// Brand
<SinergyLogo variant="full" | "icon" />
<SuiteHeader suite="fed" | "corp" | "med" | "gov" />

// Layout
<DashboardLayout />
<ModuleLayout />
<WizardLayout />

// Forms
<SinergyButton variant="primary" | "secondary" />
<SinergyInput />
<SinergySelect />

// Data Display
<SinergyTable />
<SinergyCard />
<StoplightIndicator value={0-100} />

// Charts (with Sinergy colors)
<SinergyLineChart />
<SinergyBarChart />
<SinergyHeatmap />

// AI
<AIAssistantPanel />
<RAGCitationView />
```

**Styling:** All components use Sinergy brand colors and typography from UI_MODERNIZATION_GUIDE.md

### 5.7 Deployment Architecture

**GCP Cloud Run (Serverless):**

```
platform.sinergysolutions.ai → GCP Cloud Run (cortx-platform-gateway)
designer.sinergysolutions.ai → GCP Cloud Run (cortx-designer)
fedsuite.ai                  → GCP Cloud Run (fedsuite-app)
corpsuite.ai                 → GCP Cloud Run (corpsuite-app)
medsuite.ai                  → GCP Cloud Run (medsuite-app)
govsuite.ai                  → GCP Cloud Run (govsuite-app)
```

**Services:**
```
cortx-platform-gateway       (Gateway Service)
cortx-platform-identity      (Identity Service)
cortx-platform-ai-broker     (AI Broker Service)
cortx-platform-validation    (Validation Service)
cortx-platform-workflow      (Workflow Service)
cortx-platform-compliance    (Compliance Service)
cortx-platform-schemas       (Schema Service)
cortx-platform-ledger*       (Ledger Service - TBD)

fedsuite-app                 (Next.js + FastAPI modules)
corpsuite-app                (Next.js + FastAPI modules)
medsuite-app                 (Next.js + FastAPI modules)
govsuite-app                 (Next.js + FastAPI modules)
```

**Shared Infrastructure:**
- PostgreSQL (Cloud SQL) - shared with schema-per-suite
- Redis (Memorystore) - shared, key prefixing
- GCS (Cloud Storage) - bucket-per-suite
- Secret Manager - centralized

### 5.8 Cross-Suite Integration

**Event Bus Pattern (Redis Streams):**

```python
# Publish event from FedReconcile
await redis.xadd(
    "cortx:events:fedsuite",
    {
        "event_type": "reconciliation_completed",
        "workflow_id": "gtas_monthly_001",
        "tenant_id": "agency-dod-001",
        "status": "success"
    }
)

# Subscribe from Compliance Service
events = await redis.xread({"cortx:events:fedsuite": "0"}, count=10)
```

**Cross-Suite Workflows:**
- FedReconcile → Compliance Service (audit trail)
- PropVerify → Ledger Service (immutable records)
- All suites → AI Broker (explanations, recommendations)

---

## 6. OUTSTANDING QUESTIONS

### 6.1 Ledger Service Decision ✅ (Resolved)
**Outcome:** **Promote to platform** as **Ledger Service (8136)**. Required by multiple suites for tamper-evident compliance evidence; integrates with Compliance Service (8135). 

### 6.2 OCR Engine Decision ✅ (Resolved)
**Outcome:** **Promote to platform** as **OCR Service (8137)** with Tesseract default and optional Google Document AI via AI Broker policy.

### 6.3 RAG Centralization ✅ (Resolved)
**Outcome:** Create dedicated **RAG Service (8138)**. Modules no longer own vector DBs; all retrieval uses hierarchical scoping via the platform service.

---


## 7. MIGRATION PLAN (PHASED + DEMO CHECKPOINTS)

**Phase 0 (Week 0–1): Foundations**
- Stand up **svc-rag (8138)** schema/tables (pgvector), minimal APIs (upload/crawl, ingest, query)
- Promote **svc-ocr (8137)** and **svc-ledger (8136)** with MVP endpoints
- Gateway routes and Identity scopes for new services

**Checkpoint A (End of Week 3): FedReconcile RAG Demo**
- Seed Platform: OMB A-136; Suite: GTAS; Module: FedTransform/FedReconcile docs; Entity: sample agency
- Next.js demo page: query with hierarchical citations; export ledger CSV of actions

**Phase 1 (Week 2–4): Integrations**
- PropVerify: switch OCR to Platform; remove internal ledger writes
- FedTransform: move RAG content to svc-rag (module scope); update SDK calls

**Phase 2 (Week 5–6): Hardening**
- RLS policies, PII redaction in AI Broker before embedding
- RAG Admin UI (scope tabs; upload/crawl/browse/delete)

**Checkpoint B (End of Week 6): Ledger Evidence Demo**
- Show hash-chain verification; downloadable CSV; integrate with Compliance UI

**Phase 3 (Week 7–8): Suite Conversions**
- Greenlight, InvestmAit: audit AI usage; migrate to AI Broker + svc-rag as needed
- E2E tests across gateway → services → DB

**Checkpoint C (End of Week 8–9): OCR→RAG Pipeline Demo**
- Upload scanned PDF → OCR → svc-rag index → answer with citations


## 8. NEXT STEPS

1. ✅ Complete this analysis
2. ✅ Get stakeholder decisions on key questions
3. ⏳ **Create ADRs for key decisions:**
   - ADR-001: Platform centralization strategy (Gateway, Identity, Validation, Workflow, Compliance)
   - ADR-002: Suite-level architecture (Single gateway vs per-suite)
   - ADR-003: Database strategy (schema-per-suite + RLS)
   - ADR-004: Shared UI component library
   - ADR-005: PropVerify service migration to platform (OCR, Ledger, RAG)
   - ADR-006: RAG hierarchy & retrieval policy (Platform/Suite/Module/Entity)
   - ADR-007: AI Broker provider policy (Vertex primary; OpenAI dev-only)
4. ⏳ Create detailed migration plan (phased rollout)
5. ⏳ Identify breaking changes and migration paths
6. ⏳ Create prototype refactoring for one module (**FedReconcile RAG demo**) referencing Platform/Suite/Module scopes + Ledger export

---

## Appendices

### Appendix A: Repository Inventory

#### Source Repositories
1. `/Users/michael/Development/cortx-suites` - FedSuite code
2. `/Users/michael/Development/cortx-platform` - Platform services (partial)
3. `/Users/michael/Development/cortx-designer` - BPM Designer
4. `/Users/michael/Development/cortx-propverify` - PropVerify module
5. `/Users/michael/Development/greenlight` - Greenlight module
6. `/Users/michael/Development/OffermAit` - InvestmAit module
7. `/Users/michael/Development/compliance-scanner` - Compliance scanner tool
8. `/Volumes/Dev Volume/Asset Development/FedTransform` - FedTransform (v1)
9. `/Volumes/Dev Volume/Development/FedTransform` - FedTransform (v2?)
10. `/Volumes/Dev Volume/sinergy_dev/greenlight` - Greenlight (alt)
11. `/Users/michael/Development/deprecated-cortx-development` - Legacy code

#### Target Repositories
1. `~/Development/sinergysolutionsllc/cortx-platform` - Platform services
2. `~/Development/sinergysolutionsllc/cortx-designer` - BPM Designer
3. `~/Development/sinergysolutionsllc/cortx-sdks` - SDKs
4. `~/Development/sinergysolutionsllc/cortx-packs` - RulePacks & WorkflowPacks
5. `~/Development/sinergysolutionsllc/cortx-e2e` - E2E tests
6. `~/Development/sinergysolutionsllc/fedsuite` - Federal suite
7. `~/Development/sinergysolutionsllc/corpsuite` - Corporate suite
8. `~/Development/sinergysolutionsllc/medsuite` - Healthcare suite
9. `~/Development/sinergysolutionsllc/govsuite` - Government suite

---

**END OF ANALYSIS (IN PROGRESS)**
