

# CORTX Repo Alignment — Multi‑Agent Orchestration Prompt (Claude Code)

**Objective:** Bring the current `sinergysolutionsllc` working directory into alignment with the **CORTX multi‑repo architecture and CI/CD blueprint** described in `docs/operations/REPO_INSTRUCTION.md`. Execute a sequenced, auditable plan using the specified agent roles to: split/migrate code, standardize folders, wire reusable CI, and prepare deployable infra. Produce PRs and change logs for every repo touched.

---

## Agent Roster (load these profiles)

Load the following role definitions before starting. Each agent responds only within their remit, hands off artifacts to the next, and opens PRs as needed.

- `/Users/michael/Development/sinergysolutionsllc/.claude/agents/tech-architect.md`
- `/Users/michael/Development/sinergysolutionsllc/.claude/agents/tech-lead-architect.md`
- `/Users/michael/Development/sinergysolutionsllc/.claude/agents/functional-lead.md`
- `/Users/michael/Development/sinergysolutionsllc/.claude/agents/backend-services-dev.md`
- `/Users/michael/Development/sinergysolutionsllc/.claude/agents/ui-frontend-developer.md`
- `/Users/michael/Development/sinergysolutionsllc/.claude/agents/gcp-deployment-ops.md`
- `/Users/michael/Development/sinergysolutionsllc/.claude/agents/quality-assurance-lead.md`

> Coordination mode: **sequential with verification gates**. Each phase ends with a Verification Checklist and explicit artifacts. If a gate fails, open an issue labeled `BLOCKER` and halt.

---

## Scope & Constraints

- **Organization:** `sinergysolutionsllc`
- **Do not** delete history. Use `git filter-repo` or subtree splits to preserve commit history where moved.
- **No secrets in code.** All deploy credentials must use OIDC + environment secrets.
- **Environments:** `dev` (auto), `stage` (manual), `prod` (manual).
- **Primary reference:** `docs/operations/REPO_INSTRUCTION.md` (authoritative).

---

## Global Variables (set once)

```
ORG=sinergysolutionsllc
PRIMARY_DOC=docs/operations/REPO_INSTRUCTION.md
CI_REPO=cortx-ci
DOCS_REPO=cortx-docs
INFRA_REPO=cortx-infra
E2E_REPO=cortx-e2e
SDK_REPO=cortx-sdks
PACKS_REPO=cortx-packs
DESIGNER_REPO=cortx-designer
SUITES_REPO=cortx-suites
SERVICES=(cortx-gateway cortx-identity cortx-validation cortx-workflow cortx-compliance cortx-ai-broker cortx-rag cortx-ocr cortx-ledger)
```

---

## Phase 0 — Architectural Confirmation (Tech Architect → Tech Lead Architect)

**Tech Architect — Tasks**
1. Parse `$PRIMARY_DOC` and extract:
   - target repo list,
   - per‑repo folder conventions,
   - CI workflow callers and gates.
2. Generate a **Target Map** from current tree to destination repos (YAML), including:
   - source path,
   - destination repo,
   - destination path,
   - split strategy (subtree vs filter‑repo),
   - notes.

**Deliverable:** `docs/operations/repo_target_map.yml`

**Tech Lead Architect — Tasks**
1. Review `repo_target_map.yml` for conflicts (name collisions, shared libs).
2. Emit a **Migration Plan** with ordered steps and risk mitigations.

**Deliverable:** `docs/operations/repo_migration_plan.md`

**Verification Gate**
- Both artifacts exist and reference all top‑level paths currently present.
- Risks include rollback strategy per repo.

---

## Phase 1 — Functional Boundaries (Functional Lead)

**Tasks**
1. Confirm that **RulePacks/WorkflowPacks** (business rules) are cleanly separated from **CORTX platform** code.
2. Produce **module ownership** and **CODEOWNERS** matrices for:
   - `/openapi/**`, `/policy/**`, `/infra/**`, `/schemas/**`.
3. Define **service‑to‑service contracts** (table listing producer, consumer, OpenAPI ref).

**Deliverables**
- `docs/operations/ownership_matrix.md`
- `docs/operations/service_contracts.md`
- CODEOWNERS stubs per target repo (inlined in the doc as code blocks)

**Verification Gate**
- No business rules remain in platform service directories.

---

## Phase 2 — Repo Provisioning & History‑Preserving Splits (Tech Lead Architect → Backend Services Dev)

**Tech Lead Architect — Tasks**
1. Create (if missing) the following repos in `$ORG`:
   `$CI_REPO`, `$DOCS_REPO`, `$INFRA_REPO`, `$E2E_REPO`, `$SDK_REPO`, `$PACKS_REPO`, `$DESIGNER_REPO`, `$SUITES_REPO`, and each `${SERVICES[@]}`.

2. For each service in `${SERVICES[@]}`, define the **split command**:
   - Prefer `git subtree split` for single‑path extraction.
   - Fall back to `git filter-repo` for complex moves.

**Backend Services Dev — Tasks**
1. Execute the split commands per service:
   - Ensure final layout matches service blueprint:
     ```
     app/{api,core,domain,services,clients,workers}
     tests/{unit,integration,contract}
     openapi/
     infra/{Dockerfile,helm/,kustomize/}
     scripts/
     .github/workflows/
     ```
2. Push to the new repos with preserved history.
3. Add `README.md` and `CODEOWNERS` from Phase 1 stubs.

**Deliverables**
- PRs opened on each service repo named: `feat(chore): initial split with history`.
- A log file `docs/operations/split_log.md` summarizing SHAs and ranges.

**Verification Gate**
- Each service repo builds locally (`scripts/dev.sh`), tests run, and `openapi/` exists.

---

## Phase 3 — Reusable CI Wiring (Tech Lead Architect → QA Lead)

**Tech Lead Architect — Tasks**
1. In `$CI_REPO`, create reusable workflows:
   - `reusable-python-service.yml`
   - `reusable-node-frontend.yml`
   - `reusable-openapi-publish.yml`
   - `reusable-docker-build-scan.yml`
   - `reusable-helm-deploy.yml`
   - `reusable-sdk-publish.yml`
   - `reusable-pack-validate.yml`
   - `reusable-e2e-run.yml`

2. In each service repo, add CI callers:
   - `.github/workflows/ci.yml` (Python services)
   - configure environment protections (`dev` auto, `stage/prod` manual)

**QA Lead — Tasks**
1. Add quality gates:
   - coverage ≥ 85%, Trivy/Grype fail on High+, Gitleaks enabled.
2. Register Codecov if enabled; add status checks to branch protections.

**Deliverables**
- CI green on all services.
- `docs/operations/ci_matrix.md` listing required checks per repo.

**Verification Gate**
- Required checks enforced via branch protection on `main` for all repos.

---

## Phase 4 — Packs & Designer Integration (Functional Lead → Designer Dev → QA Lead)

**Functional Lead — Tasks**
1. Move all packs into `$PACKS_REPO` under:
   - `rulepacks/`, `workflowpacks/`, `schemas/`, `tests/{data,validation}`, `signing/`
2. Author `PACKS_README.md` with semver and signing policy.

**Designer Developer — Tasks**
1. Ensure `cortx-designer` compiles and publishes packs to the platform registry (API endpoint of `cortx-validation`/registry service).
2. Add CI for preview deployments and pack publish dry‑runs.

**QA Lead — Tasks**
1. Validate `reusable-pack-validate.yml` passes on PR and tag builds.

**Verification Gate**
- Sample pack compiles from Designer and passes validation in `$PACKS_REPO`.

---

## Phase 5 — Suites & SDKs (UI Frontend Dev → Backend Services Dev)

**UI Frontend Dev — Tasks**
1. In `$SUITES_REPO`:
   - Structure: `fedsuite/`, `govsuite/`, `medsuite/`, `corpsuite/`, `frontend/`, `shared/`, `docs/`
   - Next.js app reads OpenAPI from docs site or service URLs.
2. Implement shared UI libs and a multi‑suite layout.

**Backend Services Dev — Tasks**
1. In `$SDK_REPO`:
   - `sdk-python/` + `sdk-ts/` client generation from latest OpenAPI.
   - Publish on tags (PyPI/npm) via `$CI_REPO` workflows.

**Verification Gate**
- Example flows run against `dev` env using SDKs and render in Suite UI.

---

## Phase 6 — Infra & Deploy (GCP Deployment Ops)

**Tasks**
1. In `$INFRA_REPO`:
   - `terraform/` modules for GKE Autopilot, Cloud SQL, Buckets, Redis, Artifact Registry, Workload Identity.
   - `helm/` base charts per service; `envs/{dev,stage,prod}/values.yaml`.
   - OPA/Gatekeeper policies and Cloud Armor rules.

2. Set up GH OIDC → GCP Workload Identity Federation; no static keys.
3. Create environment‑protected deploy pipelines using `reusable-helm-deploy.yml`.

**Deliverables**
- `terraform plan` and initial `apply` for `dev`.
- Deployed `gateway`, `identity`, and at least one additional core service.

**Verification Gate**
- Health checks pass; P95 latency SLO defined; smoke tests green.

---

## Phase 7 — E2E, Synthetics & Docs (QA Lead → Docs Bot)

**QA Lead — Tasks**
1. In `$E2E_REPO` add Playwright API+UI tests against `dev`.
2. Add uptime/API synthetics with thresholds; wire to Slack/email.

**Docs Bot — Tasks**
1. In `$DOCS_REPO`, ingest OpenAPI artifacts (PRs auto‑opened by services).
2. Build and publish MkDocs site; ensure service pages + packs pages render.

**Verification Gate**
- E2E suite green; docs site updated with latest endpoints and pack catalogs.

---

## Phase 8 — Sign‑off & Locks (Tech Architect)

**Tasks**
1. Ensure all repos have:
   - `CODEOWNERS`, branch protection with required checks,
   - Conventional Commit linting,
   - release notes (Release Please / semantic‑release).
2. Produce a **Final Alignment Report** summarizing:
   - repos created,
   - CI gates,
   - deploy state per environment,
   - open risks & follow‑ups.

**Deliverable**
- `docs/operations/final_alignment_report.md`

---

## Command & PR Conventions

- PR title format: `feat(scope): short summary` or `chore(scope): split history import`
- Labels: `BLOCKER`, `CI`, `SECURITY`, `MIGRATION`, `DOCS`
- Every phase produces artifacts under `docs/operations/` and links them in PR descriptions.

---

## Stop Conditions

- Any security scanner (Gitleaks, Trivy/Grype) High+ finding without an explicit `risk-accepted.md` → **halt**.
- Any missing OpenAPI or failing coverage gate → **halt**.

---

## Kickoff

Begin at **Phase 0**. Ask clarifying questions only if a source path cannot be mapped. Otherwise proceed with best judgement according to `REPO_INSTRUCTION.md`. Output artifacts and open PRs as you complete each phase.
