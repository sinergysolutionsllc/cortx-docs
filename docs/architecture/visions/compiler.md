
# CORTX Compiler Vision  

### Auto‑UI Generation for WorkflowPack + RulePack Execution

**Aligned With (authoritative UI sources):**  

- `/Users/michael/Development/sinergysolutionsllc/docs/reports/ui/PHASE_2_COMPONENT_LIBRARY_COMPLETION.md`  
- `/Users/michael/Development/sinergysolutionsllc/docs/reports/ui/UI_BRANDING_IMPLEMENTATION_GUIDE.md`  
- `/Users/michael/Development/sinergysolutionsllc/docs/reports/ui/UI_COMPONENTS_AUDIT.md`  
- `/Users/michael/Development/sinergysolutionsllc/docs/reports/ui/UI_INTEGRATION_COMPLETION_REPORT.md`  
- `/Users/michael/Development/sinergysolutionsllc/docs/reports/ui/UI_INTEGRATION_FINAL_SUMMARY.md`  
- `/Users/michael/Development/sinergysolutionsllc/docs/reports/ui/UI_MODERNIZATION_GUIDE.md`  

**Revision Date:** 2025‑10‑07  
**Owners:** CORTX Architecture Team (Platform + Suites)

---

## 1) Purpose

The CORTX Compiler transforms visual BPM designs into executable **WorkflowPacks** and **RulePacks**.  
**Phase 2** expands the compiler so that every successful compile **also produces a runnable, branded UI** (a micro‑frontend) without manual front‑end coding.

---

## 2) Vision Statement

> **“Every WorkflowPack that compiles successfully becomes an immediately runnable experience.”**

The compiler bridges **Design → Execution → Experience**:

1. Parse the BPM node graph and emit normalized WorkflowPack/RulePack JSON.
2. Emit a **UI Schema** describing inputs, actions, results, and HIL gates.
3. Generate a **React/Next.js** component tree conforming to the **Phase 2 Component Library** and the **Branding Implementation Guide**.
4. Register the generated UI with the Platform and expose it inside the appropriate **Suite wrappers** (FedSuite, GovSuite, MedSuite, ClaimSuite).

---

## 3) Output Artifacts

```
/compiled/
 ├─ workflowpacks/
 │   ├─ gtas_upload_flow_v01.json
 │   └─ cars_daily_recon_v02.json
 ├─ rulepacks/
 │   └─ gtas_core_v01.json
 └─ ui/
     ├─ components/
     │   └─ AutoRunner_gtas_upload_flow_v01.tsx
     ├─ metadata/
     │   └─ gtas_upload_flow_v01_ui_schema.json
     └─ assets/
         └─ icons/, loaders/, illustrations/
```

- **WorkflowPack/RulePack JSON:** immutable, versioned.  
- **UI Schema (JSON):** `layout`, `sections`, `inputs`, `actions`, `bindings`, `approval_roles`.  
- **Generated Component:** imports only from approved Phase 2 library; branded via design tokens.

---

## 4) Generation Pipeline

### 4.1 Compile

- Validate graph; normalize node/edge model.
- Persist packs to registries with semantic versions.
- Extract node metadata for UI (`ui_hints`, `field_types`, `role_gates`, `data_bindings`).

### 4.2 Emit UI Schema

Example:

```json
{
  "layout": "runner",
  "sections": ["ingestion", "validation", "hil", "results"],
  "inputs": [
    {"id": "file", "type": "file-upload", "accept": ["csv","xlsx","pdf"], "label": "Upload File"}
  ],
  "actions": [
    {"id": "run", "label": "Run Workflow", "icon": "Play", "variant": "primary"}
  ],
  "results": [
    {"type": "validation-summary"},
    {"type": "reconciliation-table"},
    {"type": "download-artifacts"}
  ],
  "approvals": {
    "roles": ["analyst","compliance","admin"],
    "threshold": 3,
    "weights": {"analyst":1,"compliance":2,"admin":3}
  }
}
```

### 4.3 Generate React (Next.js App Router)

**Mapping (UI Schema → Components)**

- `file-upload` → `<FileUploader />`
- `validation-summary` → `<ValidationGrid />`
- `hil-approval` → `<ApprovalModal />`
- `reconciliation-table` → `<ReconciliationTable />`
- `download-artifacts` → `<ArtifactPanel />`
- `ai-suggestions` → `<AISuggestionPane />`

**Skeleton**

```tsx
import { FileUploader, ValidationGrid, ApprovalModal, ReconciliationTable, ArtifactPanel, AISuggestionPane } from "@/components/ui";
import { RunnerShell } from "@/components/layout/RunnerShell";

export default function AutoRunner_gtas_upload_flow_v01() {
  // data fetching via /api/runs, websocket status, RBAC gates
  return (
    <RunnerShell packId="gtas_upload_flow_v01">
      <FileUploader accept={[".csv",".xlsx",".pdf"]} />
      <AISuggestionPane />
      <ValidationGrid />
      <ApprovalModal />
      <ReconciliationTable />
      <ArtifactPanel />
    </RunnerShell>
  );
}
```

### 4.4 Branding & Theming (authoritative)

- Tokens & typography sourced from **UI_BRANDING_IMPLEMENTATION_GUIDE.md** (colors: Sinergy Teal, Federal Navy, Clarity Blue, Slate Gray; typography: Inter/Graphik).
- Wrapped by `<ThemeProvider systemMode="auto" />`.
- No inline colors; **all** styles via tokens/classes audited in **UI_COMPONENTS_AUDIT.md**.

### 4.5 Registration

- Store component and schema paths in Supabase registry:

```sql
insert into cortx.ui_templates (pack_id, version, path, suite_target, brand_profile)
values ('gtas_upload_flow_v01','0.1','/compiled/ui/components/AutoRunner_gtas_upload_flow_v01.tsx','FedSuite','sinergy-default');
```

- Expose discovery API: `GET /api/ui/templates?pack_id=...`

---

## 5) Runtime Integration

### 5.1 Platform Runner (suite‑agnostic)

- Route: `/runs/[pack_id]`
- Dynamic import of generated component using the `ui_templates` registry record.
- Surfaces run history, audit log, and artifact downloads.

### 5.2 Suite Wrappers (domain UX)

- FedSuite: `GTAS / Reconciliation` surfaces the same runner with Fed‑specific filters.
- GovSuite, MedSuite, ClaimSuite: identical pattern; wrappers add breadcrumbs, saved views, and reporting menus.
- Menu entries appear automatically when `suite_target` is set for a pack version.

---

## 6) Governance & QA Alignment (hard gates)

| Source Document | Enforced Rule |
|---|---|
| **PHASE_2_COMPONENT_LIBRARY_COMPLETION.md** | Imports restricted to approved components; generator fails build on unknown components. |
| **UI_BRANDING_IMPLEMENTATION_GUIDE.md** | Theming via tokens only; CI checks for disallowed inline styles/colors. |
| **UI_COMPONENTS_AUDIT.md** | Build outputs a component‑usage manifest; must match audit expectations. |
| **UI_INTEGRATION_COMPLETION_REPORT.md** | Smoke tests for route registration, auth guards, error boundaries. |
| **UI_INTEGRATION_FINAL_SUMMARY.md** | Per‑suite summary of generated screens, links, and telemetry wiring. |
| **UI_MODERNIZATION_GUIDE.md** | Enforce Next.js App Router, Tailwind v4, and motion patterns where applicable. |

---

## 7) Security, Compliance, and Accessibility

- **RBAC/ABAC:** Approval nodes generate tasks scoped by role & tenant; all actions logged.  
- **FedRAMP/NIST 800‑53:** UI never exposes secrets; all PII paths gated; audit trails immutable.  
- **WCAG 2.1 AA / Section 508:** Generator runs accessibility lints and color‑contrast checks; build fails on violations.

---

## 8) Telemetry & Cost Controls

- Emit Prometheus metrics: pack render latency, run submit latency, HIL dwell time.  
- Frontend logs structured events (OpenTelemetry) with correlation IDs (`execution_id`).  
- Token/cost guardrails when AI widgets are present (per **AI Broker** policy).

---

## 9) Roadmap Enhancements

- **AI‑assisted Layout:** RAG suggests component variants based on past packs.  
- **Auto‑MDX Docs:** Generate MDX usage pages beside each UI.  
- **Multi‑Theme Builds:** Government vs. commercial skins from the same schema.  
- **Offline Bundles:** Pre‑rendered runners for disconnected environments.

---

## 10) Success Metrics

| Metric | Target |
|---|---|
| Manual UI coding reduction | ≥ 80% |
| Time: design → runnable UI | < 5 minutes |
| Component library coverage | 100% |
| Branding conformance | 100% token compliance |
| Accessibility | WCAG 2.1 AA passed |

---

## 11) Summary

The compiler becomes a **dual‑output engine**:  

- **Back‑end:** Workflow/Rule JSON for the orchestrator.  
- **Front‑end:** Runnable, branded micro‑frontends that appear instantly in the Platform Runner and Suite dashboards—governed by Phase 2 UI standards and compliance rules.

*End of document.*
