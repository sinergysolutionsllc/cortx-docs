# CORTX Repository Refactor Tracker

**Objective:** Consolidate the Sinergy Solutions CORTX ecosystem into a standardized, FDD-aligned structure while porting code from satellite repositories listed in `REPO_STANDARDIZATION_ADAPTATION.md`.

**Target Repositories:** `cortx-platform`, `cortx-designer`, `cortx-sdks`, `cortx-packs`, `cortx-e2e`, `fedsuite`, `corpsuite`, `medsuite`, `govsuite`.

| Phase | Focus | Owner Agent | Preferred LLM Tier |
|-------|-------|-------------|---------------------|
| 0 | Baseline Alignment | Tech Lead Architect | Codex GPT-5 (High) |
| 0 | Baseline Alignment | Functional Lead | Claude Code Opus |
| 1 | Source Repo Audit | Tech Architect | Codex GPT-5 (High) |
| 1 | Source Repo Audit | Quality Assurance Lead | Gemini Pro 2.5 |
| 2 | Extraction & Refactor | Backend Services Developer | Codex GPT-5 (High) |
| 2 | Extraction & Refactor | UI/Frontend Developer | Claude Code Opus |
| 3 | Pack & Suite Integration | Functional Lead | Gemini Pro 2.5 |
| 3 | Pack & Suite Integration | Backend Services Developer | Codex GPT-5 (Medium) |
| 4 | SDK & Test Harmonization | Backend Services Developer | Codex GPT-5 (Medium) |
| 4 | SDK & Test Harmonization | Quality Assurance Lead | Codex GPT-5 (High) |
| 5 | Infrastructure & CI | GCP Deployment/Ops Engineer | Codex GPT-5 (High) |
| 5 | Infrastructure & CI | Quality Assurance Lead | Gemini Pro 2.5 |
| 6 | Documentation & Governance Closure | Tech Lead Architect | Codex GPT-5 (Medium) |
| 6 | Documentation & Governance Closure | Functional Lead | Claude Code Opus |
| 6 | Documentation & Governance Closure | Quality Assurance Lead | Gemini Pro 2.5 |

---

## Phase Details & Deliverables

### Phase 0 – Baseline Alignment

- **Tech Lead Architect (Codex GPT-5 High):** Cross-check every `docs/fdd` chapter against actual service catalog; log drift items that will become refactor issues.
- **Functional Lead (Claude Code Opus):** Validate suite/module narratives against business priorities; ensure roadmap milestones match current targets.

**Exit Criteria:** Architectural gaps documented; module purpose statements current and approved.

### Phase 1 – Source Repo Audit

- **Tech Architect (Codex GPT-5 High):** Inventory each repo’s services, specs, and config; map to canonical platform/service layout.
- **Quality Assurance Lead (Gemini Pro 2.5):** Capture current test matrices, CI workflows, coverage stats, and tooling gaps for each repo.

**Exit Criteria:** Repo audit report produced; QA baseline captured in `docs/tracking`.

### Phase 2 – Extraction & Refactor

- **Backend Services Developer (Codex GPT-5 High):** Port core platform services into the standardized structure, removing duplicates and enforcing shared libraries.
- **UI/Frontend Developer (Claude Code Opus):** Refactor Designer UI to consume centralized APIs and align with updated service contracts.

**Exit Criteria:** Platform services consolidated; Designer uses shared contracts and passes smoke tests.

### Phase 3 – Pack & Suite Integration

- **Functional Lead (Gemini Pro 2.5):** Align suites with Pack governance, ensuring RulePacks/WorkflowPacks match compliance references.
- **Backend Services Developer (Codex GPT-5 Medium):** Update suite backends to call centralized services through SDKs and shared clients.

**Exit Criteria:** Suites rely on common services; Pack metadata/governance consistent.

### Phase 4 – SDK & Test Harmonization

- **Backend Services Developer (Codex GPT-5 Medium):** Regenerate SDK clients from latest OpenAPI specs and distribute language helpers.
- **Quality Assurance Lead (Codex GPT-5 High):** Expand `cortx-e2e` to cover integration paths defined in the FDD testing strategy.

**Exit Criteria:** SDKs synced with contracts; e2e suite covers critical cross-service flows.

### Phase 5 – Infrastructure & CI

- **GCP Deployment/Ops Engineer (Codex GPT-5 High):** Normalize Terraform, Docker, Makefiles, and deployment pipelines for single-command deployments.
- **Quality Assurance Lead (Gemini Pro 2.5):** Integrate markdownlint, OpenAPI sync guard, docs build, and testing gates into CI.

**Exit Criteria:** Unified infra pipeline; CI enforces docs/contracts/tests on every change.

### Phase 6 – Documentation & Governance Closure

- **Tech Lead Architect (Codex GPT-5 Medium):** Update FDD chapters with final architecture state.
- **Functional Lead (Claude Code Opus):** Refresh suite/module READMEs and Pack guides to mirror final system.
- **Quality Assurance Lead (Gemini Pro 2.5):** Publish QA metrics, regression logs, and support runbooks.

**Exit Criteria:** Documentation mirrors refactored system; governance artifacts updated.

---

## Source-to-Target Crossreference

| Category | Target Location (Monorepo) | Current Repository | Source Path(s) | Notes / Action |
|----------|----------------------------|--------------------|----------------|----------------|
| Platform Core | `services/gateway` | `cortx-platform` | `cortx-platform/services/gateway` | Mature FastAPI gateway; normalize config & dependencies. |
| Platform Core | `services/identity` | `cortx-platform` | `cortx-platform/services/identity` | OAuth/OIDC scaffold; complete RBAC/user storage on import. |
| Platform Core | `services/validation` | `cortx-platform` | `cortx-platform/services/validation` | RulePack executor; align with pack schemas before merge. |
| Platform Core | `services/workflow` | `cortx-platform` | `cortx-platform/services/workflow` | Workflow engine; fold PropVerify workflow customizations via adapters. |
| Platform Core | `services/compliance` | `cortx-platform` | `cortx-platform/services/compliance` | Compliance logging/reporting; wire to ledger + scanner. |
| Platform Core | `services/config-service` | `cortx-platform` | `cortx-platform/services/config_service` | Central configuration registry; ensure env parity. |
| Platform Core | `services/packs-registry` | `cortx-platform` | `cortx-platform/services/packs_registry` | Pack metadata service; integrate with `cortx-packs`. |
| Platform Core | `services/rulepack-registry` | `cortx-platform` | `cortx-platform/services/rulepack_registry` | Decide merge vs deprecate in favour of packs-registry. |
| Platform Core | `services/schemas` | `cortx-platform` | `cortx-platform/services/schemas` | Schema registry microservice; sync with `specs/schemas`. |
| Platform Core | `services/observability` | `cortx-platform` | `cortx-platform/services/observability` | Centralized metrics/logging aggregator. |
| Platform Core | `services/events` | `cortx-platform` | `cortx-platform/services/events` | Pub/Sub helpers for cross-suite workflows. |
| Platform Core | `services/ingestion` | `cortx-platform`, `cortx-hashtrack` | `cortx-platform/services/ingestion`, `cortx-hashtrack/backend/ingestion_svc` | Combine generic ingestion engine with PropVerify adapters. |
| Platform Core | `services/ai-broker` | `cortx-platform`, `cortx-hashtrack` | `cortx-platform/services/ai-broker`, `cortx-hashtrack/backend/ai_svc` | Merge templating/PII scrub features; expose unified API. |
| Platform Core | `services/ledger` | `cortx-hashtrack` | `cortx-hashtrack/backend/ledger_svc` | Append-only ledger; integrate proof hashing + compliance events. |
| Platform Core | `services/ocr` | `cortx-hashtrack` | `cortx-hashtrack/backend/ingestion_svc/ocr` | OCR adapters (Tesseract/DocAI); factor into standalone service. |
| Platform Core | `services/rag` | `greenlight` | `greenlight/services/rag` | Production RAG with multi-scope retrieval; align to FDD hierarchy. |
| Platform Core | `services/observability` infrastructure | `greenlight`, `OffermAit`, `cortx-platform` | `greenlight/infra/terraform/observability`, `OffermAit/monitoring`, `cortx-platform/services/observability` | Merge dashboards + alerting into shared ops stack. |
| Platform Core | `infra/helm` | `cortx-platform`, `cortx-hashtrack` | `cortx-hashtrack/helm/*`, Dockerfiles across services | Harmonize deployment charts and base images. |
| Corpsuite / PropVerify | `suites/corpsuite/propverify/backend` | `cortx-hashtrack` | `cortx-hashtrack/backend/(ingestion_svc|validation_svc|workflow_svc|ledger_svc|ai_svc)` | Preserve PropVerify business logic; rehook to platform APIs. |
| Corpsuite / PropVerify | `suites/corpsuite/propverify/services/gateway` | `cortx-hashtrack` | `cortx-hashtrack/services/gateway` | Lightweight gateway wrapper; replace with platform gateway once migrated. |
| Corpsuite / PropVerify | `suites/corpsuite/propverify/ui` | `cortx-suites` | `cortx-suites/frontend/app/corpsuite/propverify` | Consolidate UI routes within shared frontend shell. |
| Corpsuite / PropVerify | `packs/rulepacks/corpsuite/propverify` | `cortx-hashtrack`, `cortx-packs` | `cortx-hashtrack/sample_rulepack.yml`, `cortx-packs/rulepacks/corpsuite/*` | Convert sample packs + align metadata tags. |
| Corpsuite / Greenlight | `suites/corpsuite/greenlight/services` | `greenlight` | `greenlight/services/*` (ingest-sam, ingest-eva, scoring, notify, template, enrichment-uei) | Group microservices under module; prune duplicates. |
| Corpsuite / Greenlight | `suites/corpsuite/greenlight/apps` | `greenlight` | `greenlight/apps/dashboard`, `greenlight/ui` | Merge React UI with multi-suite frontend. |
| Corpsuite / Greenlight | `packs/rulepacks/greenlight` | `greenlight` | `greenlight/packages/*` | Move shared rule/prompt libs into packs registry. |
| Corpsuite / InvestmAit | `suites/corpsuite/investmait/backend` | `OffermAit` | `OffermAit/backend/src` | FastAPI modeling/orchestration engine for real-estate analysis. |
| Corpsuite / InvestmAit | `suites/corpsuite/investmait/ui` | `OffermAit` | `OffermAit/frontend` | Next.js analytics UI; integrate auth + shared layout. |
| Corpsuite / InvestmAit | `packs/workflowpacks/investmait` | `OffermAit` | `OffermAit/configs`, `OffermAit/scripts`, `OffermAit/templates` | Transform scenario configs into WorkflowPacks. |
| FedSuite | `suites/fedsuite/backend` | `cortx-suites` | `cortx-suites/fedsuite` | Fed reconciliation services; ensure module boundaries match FDD. |
| FedSuite | `suites/fedsuite/frontend` | `cortx-suites` | `cortx-suites/frontend` | Next.js multi-suite shell hosting Fed modules. |
| FedSuite | `packs/rulepacks/fed/dataflow` | `cortx-dataflow` | `cortx-dataflow/templates`, `cortx-dataflow/AI_Coach_Prompts`, `cortx-dataflow/BR100_Template` | Generate Rule/Workflow packs from DataFlow assets. |
| FedSuite | `suites/fedsuite/fedconfig` | `cortx-thinktank` | `cortx-thinktank/templates`, `cortx-thinktank/FSM_CSV_Skeletons`, `cortx-thinktank/ESS_Job_Catalog` | Build FedConfig module and documentation. |
| FedSuite | `services/compliance-scanner` | `compliance-scanner` | `compliance-scanner/service`, `compliance-scanner/scanner` | Promote scanner to platform service + pack governance integration. |
| FedSuite | `docs/fedsuite` | `cortx-suites`, `cortx-dataflow`, `cortx-thinktank` | `cortx-suites/docs`, `cortx-dataflow/docs`, `cortx-thinktank/docs` | Merge FDD/operational docs into centralized tree. |
| MedSuite | `suites/medsuite` | `sinergysolutionsllc/medsuite` | Existing module skeletons | Enhance with future external repos (TBD). |
| GovSuite | `suites/govsuite` | `sinergysolutionsllc/govsuite` | Existing placeholders | Populate once source modules identified. |
| Designer | `designer/frontend` | `cortx-designer` | `cortx-designer/frontend` | Visual authoring UI. |
| Designer | `designer/backend` | `cortx-designer` | `cortx-designer/backend` | Designer API & pack publishing. |
| Designer | `designer/compiler` | `cortx-designer` | `cortx-designer/compiler` | Pack compilation pipelines. |
| Designer | `designer/shared` | `cortx-designer` | `cortx-designer/shared`, `cortx-designer/templates` | Shared components/templates for authoring. |
| SDKs | `sdks/python` | `cortx-sdks` | `cortx-sdks/sdk-python` | Python client + generator config. |
| SDKs | `sdks/typescript` | `cortx-sdks` | `cortx-sdks/sdk-ts` | TypeScript client. |
| Packs | `packs/rulepacks` | `cortx-packs` | `cortx-packs/rulepacks` | RulePack source-of-truth; ensure alignment with platform validation. |
| Packs | `packs/workflowpacks` | `cortx-packs` | `cortx-packs/workflowpacks` | WorkflowPack catalogue. |
| Quality & Testing | `tests/e2e` | `cortx-e2e` | `cortx-e2e/tests`, `cortx-e2e/environments`, `cortx-e2e/scripts` | Move contract + scenario suites; keep env definitions. |
| Quality & Testing | `tests/unit/<module>` | Various | `OffermAit/backend/tests`, `greenlight/tests`, `cortx-hashtrack/tests`, etc. | Migrate module-specific tests alongside code. |
| Docs & Marketing | `site/` | `sinergy-solutions` | Entire repo | Rebuild docs site using existing marketing assets. |
| Docs & Governance | `docs/ai_governance` | `greenlight/docs/ai_governance`, `cortx-designer/docs` | Merge AI governance, prompts, and agent guides. |
| Ops & Infra | `infra/terraform/cloudflare` | Monorepo | `infra/terraform/cloudflare/*` | Manage Cloudflare zones & DNS for platform and suite domains via Terraform. |
| Ops & Infra | `infra/terraform` | `greenlight/infra/terraform`, `OffermAit/k8s`, `cortx-hashtrack/k8s` | Consolidate IaC across repos. |
| Ops & Automation | `scripts/*` | Various | `cortx-hashtrack/tools`, `OffermAit/scripts`, `compliance-scanner/scripts`, `cortx-platform/services/update_services_ports.py` | Curate reusable automation; retire duplicates. |

---

## Hand-off Prompt Workflow

Every agent should:

1. Work through their assigned tasks until the Phase exit criteria are met or blocking dependencies are identified.
2. Produce a **Status & Findings Summary** (what changed, outstanding issues, artifacts).
3. Compose and store a `handoff_prompt.md` in the relevant repo folder containing:
   - **Context Recap:** Scope handled, files touched, outcomes achieved.
   - **Outstanding Items:** TODOs, blockers, or decisions needed before next phase.
   - **Next Agent Instructions:** Explicit tasks for the incoming agent.
   - **LLM Recommendation:** Which tier/model to use (use table above as default).
4. Create a **Next-Agent Prompt** appended to the same file under `---` with:
   - Greeting addressed to the next agent persona.
   - Bullet list of immediate tasks.
   - Links/paths to key files or docs.
   - Test commands or validation steps to run.

**Template:**

```
# Handoff – Phase X (Agent Role)

## Context Recap
- …

## Outstanding Items
- …

## Next Agent Instructions
- …

## Recommended LLM
- …

---

# Next-Agent Prompt – Phase X → Phase Y

Hello <Incoming Agent>,

- Task 1
- Task 2
- Task 3

Run:
- `make ci`
- …

LLM suggestion: <model>.
```

Agents must delete or archive the handoff file after completion to prevent stale instructions.

---

## Tracker Usage

- Update this tracker after each phase with completion dates and links to handoff prompts or summaries.
- Maintain alignment with `docs/fdd` so documentation always matches code state.
- Ensure all migrated repos comply with the standards in `REPO_STANDARDIZATION_ADAPTATION.md`.

| Phase | Status | Owner | Notes/Links |
|-------|--------|-------|-------------|
| 0 | Completed | Tech Lead Architect / Functional Lead | DataFlow rename + service catalog updates (`docs/fdd/03.Technical_Architecture.md`, `docs/suites/index.md`) |
| 1 | In Progress | Tech Architect | Gateway & Identity migrated (2025-10-06); pending audit of remaining repos |
| 2 | Not Started | | |
| 3 | Not Started | | |
| 4 | Not Started | | |
| 5 | Not Started | | |
| 6 | Not Started | | |
