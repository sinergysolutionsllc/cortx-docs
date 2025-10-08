# CORTX Docs • Templates • Governance — Full Repository Audit, De-Dup & Patch Plan
**Role:** You are the *Docs, Templates & Governance Automation Architect* for CORTX by Sinergy.  
**Objective:** Audit the repository against the CORTX documentation & governance standard and produce:
1) a concise scorecard, 2) a concrete gap list, 3) a patch set (unified diffs/new files), **4) a deprecation & delete list for unnecessary/duplicative docs**, and **5) a merge/canonicalization plan**.  
**Context:** Compliance-first (FedRAMP, NIST 800-53, SOC 2 Type II, HIPAA, GDPR). Platform services/ports: Gateway 8080, Identity 8082, Validation 8083, AI Broker 8085, Workflow 8130, Compliance 8135, **Ledger 8136**, **OCR 8137**, **RAG 8138**.

---

## What to Analyze (from repo root)
Perform a deterministic scan and summarize:

1) **Templates (required at `/templates/`)**
   - `README.repo.template.md`
   - `README.service.template.md`
   - `README.module.template.md`
   - `FDD.template.md`  (modeled on CORTX_PLATFORM_FDD.md)
   - `ADR.template.md`  (match ADR 0001–0003: Context → Options → Decision → Consequences → References)
   - `AgentRoles.template.md` (align with Agents.md / Claude.md / Gemini.md)
   - `CHANGELOG.template.md` (Keep a Changelog + SemVer)

2) **Docs Site (MkDocs Material)**
   - `mkdocs.yml` at repo root
   - `/docs/` IA folders: `overview/`, `architecture/`, `services/`, `suites/`, `packs/`, `sdks/`, `security/`, `operations/`, `contribute/`, `adr/`, `rfcs/`, `diagrams/`
   - Mermaid blocks compile; internal links resolve; ADR index exists: `/docs/adr/ADR-000-index.md`

3) **Repo Standards**
   - Root governance: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CODEOWNERS`, `SUPPORT.md`
   - `.github/`:
     - `PULL_REQUEST_TEMPLATE.md`
     - `ISSUE_TEMPLATE/bug.md`, `feature.md`, `rfc.md`, `doc_request.md`
     - `workflows/`:  
       - `docs-ci.yml` (lint MD + links, build docs, validate Mermaid)  
       - `contracts-ci.yml` (validate OpenAPI + JSON Schema)  
       - `release.yml` (semantic releases for SDKs/Packs)  

4) **Contracts-First Artifacts**
   - `services/**/openapi.yaml` (or `.yml`) present/valid
   - `/schemas/**` JSON Schemas present/valid
   - SDK generation hooks/pipelines (documented or CI-backed)

5) **ADRs & RFCs**
   - `/docs/adr/` populated + indexed
   - `/rfcs/NNNN-title/` present if RFCs exist; linked from docs

6) **Readme Consistency**
   - Org, repo, service, and module READMEs follow templates
   - Service ports correct; env strategy (dev→staging→prod) and provider policy (Vertex primary, OpenAI dev-only) referenced

7) **Redundancy / Bloat / Stale Docs (NEW)**
   - Identify **duplicates or near-duplicates** (≥85% textual similarity, same or highly similar titles/headings).
   - Identify **stale** (no edits > 12 months) that are **not referenced** by any README, mkdocs nav, or docs pages.
   - Identify **orphaned** files (not linked anywhere and not in mkdocs nav).
   - Identify **conflicting versions** (e.g., multiple FDDs or ADRs for the same service/decision without index references).
   - Identify **binary/document bloat**: PDFs/images in non-canonical paths or >5MB that aren’t used by docs.
   - Identify **generated artifacts** committed to source (should be ignored).

---

## How to Perform the Scan
Use deterministic, repo-local steps (no network):

- Walk the tree (ignore `node_modules`, `.venv`, `.tox`, `dist`, `build`, `.next`, `__pycache__`, `.git`).
- Record existence and **minimal content rules**:
  - Templates: required headings/sections present.
  - `mkdocs.yml`: includes Material theme and nav entries for IA sections above.
  - Workflows: run on `pull_request`(/`push`), correct paths, sensible defaults.
- **OpenAPI & JSON Schema sanity**: YAML/JSON parseable; `openapi:` key present for OAS3; `$schema` present for JSON Schema.
- **Mermaid**: grep ```mermaid blocks; check for typical keywords (graph/flow/sequence/class/state) and codefence closure.
- **Redundancy detection**:
  - Flag files with the same basename in different locations (e.g., multiple `README.md` or `FDD.md` variants).
  - Compute simple similarity (title + top-level headings + paragraph hashes) to flag near-duplicates.
  - Check whether each doc is referenced by: any README, mkdocs nav, or other docs (grep links).
  - Consider timestamps (older than 12 months) + zero references ⇒ stale candidate.

---

## Output Format (strict)
Return **five sections**, in this order:

### 1) SCORECARD
Table: Area | Status (✅/⚠️/❌) | Notes  
Areas: Templates, Docs Site, Repo Standards, Contracts-First, ADRs/RFCs, Readmes, Env/Security, **Redundancy/Bloat**

### 2) GAPS & DRIFT
Bullet list with exact **paths** and **one-line fixes**.  
Examples:
- `❌ /templates/README.service.template.md` — missing → create from established service style
- `⚠️ /docs/adr/ADR-000-index.md` — missing index → generate linking 0001–000N

### 3) PATCH SET (UNIFIED DIFFS OR NEW FILES)
- Provide ready-to-apply patches.  
- **New files**: include full content (start with `--- /dev/null` → `+++ <path>`).  
- **Modifications**: unified diff.  
- Keep patches minimal and self-contained.

### 4) DEPRECATION & DELETE LIST (SAFE CLEANUP)
For each candidate, list:
- **Path**
- **Category** (duplicate/near-duplicate, stale, orphaned, conflicting, bloat/generated)
- **Rationale** (e.g., “duplicate of X; not referenced; older by 14 months”)
- **Action**: delete, keep, or merge into canonical
- **Canonical target** (if merge)  
> Important: Do **not** propose deleting source code. Limit to docs/assets. Prefer **merge** over delete when a doc has partial unique value.

### 5) MERGE & CANONICALIZATION PLAN
- For duplicates: specify which file becomes **canonical** and provide a **merged version** (unified diff) that retains any unique content from the duplicate(s).
- For ADR conflicts: unify into **one ADR** or add an “Amended by ADR-XXXX” note; update **ADR-000-index.md**.
- For large assets: move to `/docs/assets/` (or `/docs/diagrams/`, `/docs/reference/`) and update links in affected pages.

---

## Generation Rules
- Mirror **established styles** in:
  - `CORTX_PLATFORM_FDD.md` (for FDD.template.md)
  - `docs/ADRs/0001-*.md`, `0002-*.md`, `0003-*.md` (ADR template)
  - `Agents.md`, `Claude.md`, `Gemini.md` (AgentRoles template)
  - `CHANGELOG.md` (CHANGELOG template)
- Voice: compliance-first, production-ready; no TODO/placeholder text.
- Include **Mermaid** snippets where useful (platform topology, hierarchical RAG).
- Default docs engine: **MkDocs Material**.
- Respect CORTX service ports; include environment strategy table in repo README template.
- **Never delete code**; only propose cleanup for docs/assets that are redundant/unreferenced.

---

## Acceptance Criteria
- Scorecard clearly signals readiness.
- Gaps list is actionable/exhaustive.
- Patch set compiles (Markdown/YAML), sensible CI defaults.
- Deletion proposals include rationale + canonical target where applicable.
- Merge plan yields a single, clean, organized docs set.

---

## Optional Commands (if shell is allowed)
Do not fail if shell is blocked; treat as guidance only:
```bash
# Tree (top two levels)
find . -maxdepth 2 -type d -not -path '*/node_modules/*' -not -path '*/.git/*' | sort

# Templates & mkdocs
ls -la templates || true
test -f mkdocs.yml && head -n 40 mkdocs.yml || true

# OpenAPI quick check
grep -R --include='*.y*ml' -n '^openapi:' services 2>/dev/null || true

# Mermaid blocks
grep -R --include='*.md' -n '```mermaid' docs 2>/dev/null || true

# Inbound links to a file (example)
grep -R --include='*.md' -n 'docs/old_fdd.md' . 2>/dev/null || true
