# REPO_INSTRUCTION

- Keep OpenAPI/JSON Schemas in /specs
- CI: lint, tests, SCA, SBOM
- Trunk-based dev; SemVer tags for releases
- No secrets; enforce CODEOWNERS on critical paths

# CORTX Repository Blueprint & CI/CD (Authoritative Reference)

> Purpose: stop the “is this a monorepo?” confusion and define a clean, audit‑ready **multi‑repo** model for **CORTX (platform) + Suites + Designer + Packs + SDKs + Infra + E2E**. This document is the canonical layout and pipeline contract for all CORTX repos.

---

## 1) Repository map (what to create and what lives where)

**Guiding principle:** **CORTX (orchestration) ≠ RulePacks/WorkflowPacks (business rules)**, and **Suites ≠ Platform**. Each major concern is its own repo. A small “coordination” repo hosts docs/portals only—no app code.

### A. Platform & Core Services (one repo per service)
- **cortx-gateway** (FastAPI)—ingress, request routing, policy router, workflow executor  
- **cortx-identity**—authn/authz (RBAC/ABAC), session mgmt, JWT/OIDC, policy decision points  
- **cortx-validation**—schema + rule engine execution  
- **cortx-workflow**—long-running jobs, sagas, compensations (if not folded into gateway)  
- **cortx-compliance**—immutable audit logs, evidence packaging, reporting  
- **cortx-ai-broker**—LLM brokering (Vertex, GPT, Claude), prompt library, safety/guardrails  
- **cortx-rag**—RAG indexers, ingestion, retrieval contracts  
- **cortx-ocr**—document parsing (PDF/DOCX), layout extraction  
- **cortx-ledger**—usage metering, token/cost, events for billing  

**Why separate:** independent scaling, smaller blast radius, clearer ownership, cleaner FedRAMP scope items.

### B. Designer (design-time toolchain)
- **cortx-designer** (Next.js + FastAPI compiler): Visual builder → compiles → publishes **WorkflowPacks/RulePacks** to platform registries.

### C. Packs (externalized rules/config)
- **cortx-packs**: versioned **RulePacks** + **WorkflowPacks** + **Schemas**; JSON/YAML only, signed, with tests and golden datasets. *(No app code.)*

### D. Suites (domain apps that *consume* platform)
- **cortx-suites** (mono-suite repo with subfolders or 1 repo per suite if you prefer):
  - `fedsuite/` (active)
  - `govsuite/`
  - `medsuite/`
  - `corpsuite/`
  - `frontend/` (Next.js multi-suite UI) and `shared/`

### E. SDKs & Shared Packages
- **cortx-sdks**
  - `sdk-python/` (pip package)
  - `sdk-ts/` (npm package)
  - shared client auth, typed contracts, retry policies
- **cortx-libs** *(optional if you want a separate repo)* — Common Python/TS libs (logging, tracing, error model, OpenAPI client codegen)

### F. Infra, E2E, Docs (coordination—not app code)
- **cortx-infra**: `terraform/`, `helm/`, `kustomize/`, cluster overlays (dev/stage/prod), OPA/Gatekeeper policies, Cloud Armor, Workload Identity.  
- **cortx-e2e**: Playwright API/UI tests, synthetic monitors, contract tests across services; test env configs.  
- **cortx-docs**: MkDocs site, ADRs/RFCs, compliance matrices, runbooks, architecture diagrams. *Public portal repo.* No service code here.

---

## 2) Folder conventions (inside each repo)

All **service** repos follow:

```
.
├── app/                    # source code (FastAPI/Workers)
│   ├── api/                # routers/controllers
│   ├── core/               # config, security, DI, settings
│   ├── domain/             # entities, Pydantic models
│   ├── services/           # business services & adapters
│   ├── clients/            # outgoing service clients
│   └── workers/            # background jobs (Celery/Arq/Prefect)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/           # Pact or schema-based contract tests
├── openapi/                # *.yaml source (hand-written or generated)
├── infra/
│   ├── Dockerfile
│   ├── helm/               # Helm chart for THIS service
│   └── kustomize/          # overlays per-env (optional)
├── scripts/
│   ├── dev.sh
│   ├── lint.sh
│   └── openapi_sync.sh
├── .github/
│   └── workflows/          # calls reusable workflows
├── pyproject.toml / package.json
├── README.md
└── CODEOWNERS
```

**Designer** adds:
```
frontend/ (Next.js)
backend/  (FastAPI compiler service)
packages/ (shared TS libs, e.g., node palettes)
```

**Packs**:
```
rulepacks/        # JSON/YAML (immutable, semver)
workflowpacks/
schemas/          # JSONSchema, Avro
tests/
  ├── data/       # golden datasets + edge cases
  └── validation/ # rule-level tests with expected outcomes
signing/          # optional sigstore/cosign materials
```

**Suites**:
```
fedsuite/
govsuite/
medsuite/
corpsuite/
frontend/         # multi-suite Next.js (AI assistant, dashboards)
shared/
docs/
```

**SDKs**:
```
sdk-python/
sdk-ts/
examples/
```

**Infra**:
```
terraform/
  ├── envs/{dev,stage,prod}/
  └── modules/{gke,sql,buckets,redis,...}
helm/
  ├── base-charts/[gateway,identity,...]
  └── envs/{dev,stage,prod}/values.yaml
policies/
  ├── opa/
  └── cloud-armor/
```

**E2E**:
```
e2e/
environments/
playwright.config.ts
synthetics/       # uptime/API probes
```

**Docs portal**:
```
docs/
  ├── architecture/
  ├── compliance/
  ├── services/
  ├── suites/
  ├── packs/
  └── runbooks/
mkdocs.yml
.github/workflows/site-build.yml
```

---

## 3) CI/CD (reusable, security-first, compliance-friendly)

Create **one dedicated CI repo** with reusable workflows:

- **cortx-ci**
  ```
  .github/workflows/
    reusable-python-service.yml
    reusable-node-frontend.yml
    reusable-openapi-publish.yml
    reusable-docker-build-scan.yml
    reusable-helm-deploy.yml
    reusable-sdk-publish.yml
    reusable-pack-validate.yml
    reusable-e2e-run.yml
  ```
All other repos **call** these via `workflow_call`. One source of truth for gates.

### A. Standard pipeline per service repo
- **Check**: ruff, black --check, mypy, pip-audit; eslint/tsc for Node; Gitleaks; license check  
- **Test**: unit + integration + contract; coverage ≥ 85% (Codecov optional)  
- **Build + Scan**: container build → Trivy/Grype scan (fail on high CVEs)  
- **OpenAPI publish**: validate + attach artifacts + PR to **cortx-docs**  
- **Deploy**: `dev` auto, `stage` gated, `prod` gated + changelog  
- **Post-deploy**: smoke + synthetics; rollback on SLO breach

### B. Packs repo
- Validate JSON Schema, semver, signatures
- Run rule tests vs golden datasets
- Publish to pack registry (Supabase/Postgres) with provenance (cosign/SLSA)
- Generate rule docs; PR to **cortx-docs**

### C. Designer
- FE build/tests/bundle budgets
- BE tests + OpenAPI publish
- E2E on ephemeral env (preview URLs)
- Publish images & Helm; deploy to `dev`

### D. Suites
- API/UI tests, contract tests to platform
- Fixture runs with sample Packs
- Suite docs → **cortx-docs**
- Deploy to suite namespaces per env

### E. SDKs
- Lint/test → version → publish (PyPI/npm) on tag
- Typed clients from latest OpenAPI

### F. Infra
- Terraform fmt/validate/plan
- OPA policy checks
- Apply with env protections + approvals
- Helm chart lint/tests

### G. E2E
- Ephemeral env or `dev`
- Playwright API+UI regression gates

---

## 4) Branching, versioning, governance

- **Trunk-based** with short-lived feature branches → PR → `main`
- **SemVer** per service and per pack (`vX.Y.Z`)
- **CODEOWNERS** on `/openapi/**`, `/infra/**`, `/policy/**`, `/schemas/**`
- **Required checks**: check + test + scan + e2e (where applicable)
- **Conventional Commits** + Release Please (or semantic-release)
- **Environments**: `dev` (auto), `stage` (manual), `prod` (manual + approvers)

---

## 5) Secrets & compliance

- No hardcoded secrets; use OIDC → cloud KMS/Secrets Manager
- Structured audit events to **cortx-compliance**
- SBOMs (CycloneDX) attached to releases; images signed (cosign)
- OPA/Gatekeeper for K8s; Cloud Armor/WAF; network policies
- Per-tenant isolation (DB schema/instance), TLS everywhere

---

## 6) Migration from mixed root repo (mapping)

- Keep **cortx-docs** as public/docs portal only (move `docs/`, `site/`, `mkdocs.yml` there)
- Move each folder under `services/` into its **own repo** (named above)
- Remove local mirrors under `repos/` in favor of org repos
- Keep **cortx-e2e** and **cortx-infra** separate
- Keep **cortx-sdks** and **cortx-packs** separate
- **cortx-designer** publishes packs to platform via API
- Each service keeps `openapi/` and publishes specs to **cortx-docs** via reusable workflow

---

## 7) Example workflow callers (copy/paste)

**Service repo CI caller**
```yaml
# .github/workflows/ci.yml
name: Service CI
on:
  pull_request:
  push:
    tags: ['v*.*.*']
jobs:
  service-ci:
    uses: sinergysolutionsllc/cortx-ci/.github/workflows/reusable-python-service.yml@main
    with:
      service_name: "gateway"
      publish_openapi: true
      deploy_env: "dev"
    secrets: inherit
```

**Packs repo validation**
```yaml
# .github/workflows/packs.yml
name: Packs Validate & Publish
on:
  pull_request:
  push:
    tags: ['v*.*.*']
jobs:
  packs:
    uses: sinergysolutionsllc/cortx-ci/.github/workflows/reusable-pack-validate.yml@main
    with:
      registry_url: ${{ vars.PACK_REGISTRY_URL }}
    secrets: inherit
```

**Docs portal build**
```yaml
# .github/workflows/site-build.yml
name: Build & Publish Docs
on:
  workflow_call:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: mkdocs build
      - uses: actions/upload-pages-artifact@v3
  deploy:
    needs: build
    permissions: { pages: write, id-token: write }
    uses: actions/deploy-pages@v4
```

---

## 8) What belongs where (cheatsheet)

- **Business rules & validations:** `cortx-packs` (JSON/YAML; tests + golden data)  
- **Orchestration/execution/registries:** platform service repos (`cortx-*`)  
- **Visual compile & publish of packs:** `cortx-designer`  
- **Domain UX & APIs:** `cortx-suites` (Fed/Gov/Med/Corp)  
- **Shared client code:** `cortx-sdks` (Python/TS)  
- **K8s/cloud infra:** `cortx-infra`  
- **Cross-system tests & synthetics:** `cortx-e2e`  
- **Public docs & API refs:** `cortx-docs`  
- **Reusable CI logic:** `cortx-ci`
