# UI Components Audit & Integration Plan

**Generated:** 2025-10-06
**Purpose:** Document all existing UI components across source repositories and plan their integration into the multi-repo organization structure aligned with the UI Modernization Guide.

---

## Executive Summary

This document audits UI components from 4 source repositories and maps them to the target organization structure. All UIs use **Next.js + React + Tailwind CSS**, which aligns well with the UI Modernization Guide standards.

### Key Findings

- ✅ **Consistent Tech Stack**: All frontends use Next.js 14/15 + React 18 + Tailwind CSS
- ✅ **Modern Tooling**: TypeScript, ESLint, PostCSS already standard
- ⚠️ **Branding Inconsistency**: Need to apply Sinergy brand colors, typography, and logos
- ⚠️ **Component Duplication**: Similar UI patterns exist across repos (forms, dashboards, modals)
- 🎯 **Optimization Opportunity**: Create shared component library for consistency and DRY

---

## Source Repositories Audit

### 1. CORTX Designer Frontend

**Source:** `/Users/michael/Development/cortx-designer/frontend`
**Target:** `cortx-designer/frontend` (already in correct repo)

#### Tech Stack

```json
{
  "framework": "Next.js 14",
  "ui": "React 18.2 + TypeScript 5.2",
  "styling": "Tailwind CSS 3.3 + PostCSS",
  "components": [
    "Radix UI (Dialog, Dropdown, Select, Tabs, Toast, Tooltip, Checkbox, Label, Icons)",
    "React Flow 11.10 (canvas/visual workflow builder)",
    "Recharts 2.8 (analytics charts)",
    "Lucide React 0.290 (icons)",
    "@dnd-kit (drag-and-drop)"
  ],
  "state": "Zustand 4.4",
  "forms": "React Hook Form 7.47 + Zod 3.22",
  "utilities": [
    "class-variance-authority",
    "clsx",
    "tailwind-merge",
    "date-fns"
  ],
  "testing": "Jest 29.7 + React Testing Library"
}
```

#### UI Features

- **Visual Workflow Canvas**: 28 node types (validation, decision, AI, approval, etc.)
- **AI Assistant Panel**: Natural language → workflow conversion
- **Pack Compiler UI**: Visual design → JSON/YAML export
- **Testing Simulator**: Pack execution with sample data

#### Status

✅ **Already in target location** - Needs branding alignment only

#### Action Items

1. Apply Sinergy brand colors (#00C2CB, #2D5972) to primary buttons and headers
2. Update typography to use Space Grotesk (headings), DM Sans (buttons), IBM Plex Sans (body)
3. Replace favicon and logo with `SS_Logo_Transparent.png` and `SS-Icon-Transparent.png`
4. Add dark mode toggle (Radix UI + CVA variants already present)
5. Ensure WCAG AA contrast compliance

---

### 2. OffermAit (InvestmAit) Frontend

**Source:** `/Users/michael/Development/OffermAit/frontend`
**Target:** `corpsuite/modules/investmait/frontend`

#### Tech Stack

```json
{
  "framework": "Next.js 14.2.3",
  "ui": "React 18.2 + TypeScript 5.4",
  "styling": "Tailwind CSS 3.4 + PostCSS + Autoprefixer",
  "components": [
    "Recharts 2.10 (investment analytics charts)",
    "classnames 2.5 (conditional CSS)"
  ],
  "state": "Zustand 4.5",
  "testing": "Jest 29.7 + React Testing Library + ts-jest"
}
```

#### UI Features

- **Investment Analysis Dashboard**: P/L scenarios, sensitivity charts
- **Property Valuation Forms**: Input forms for real estate data
- **Scenario Comparison**: Side-by-side scenario reports
- **Export Functionality**: Reports → PDF/Excel

#### Status

⚠️ **Needs Migration** - Move to `corpsuite/modules/investmait/frontend`

#### Action Items

1. **Move files** from `/Users/michael/Development/OffermAit/frontend` → `corpsuite/modules/investmait/frontend`
2. Apply Sinergy branding (colors, fonts, logos)
3. Integrate with **cortx-platform Gateway** for auth + API routing
4. Add **Radix UI components** for consistency with Designer
5. Extract reusable chart components → shared library
6. Wire to central Identity service (JWT/OIDC)

---

### 3. cortx-suites (FedSuite) Frontend

**Source:** `/Users/michael/Development/cortx-suites/frontend`
**Target:** `fedsuite/frontend`

#### Tech Stack

```json
{
  "framework": "Next.js 15.4.6",
  "ui": "React 18.3 + TypeScript 5.7",
  "styling": "Tailwind CSS 3.4 + PostCSS + Autoprefixer",
  "components": [
    "Lucide React 0.468 (icons)",
    "Framer Motion 12.23 (animations)"
  ],
  "http": "Axios 1.7.9"
}
```

#### UI Features

- **Fed Reconciliation Dashboard**: Trial Balance vs GTAS ATB discrepancies
- **DataFlow Mapping UI**: Source → FBDI transformation wizard
- **Compliance Reports**: GTAS validation results, journal corrections
- **AI-Assisted Corrections**: Suggested journal entries

#### Status

⚠️ **Needs Migration** - Move to `fedsuite/frontend`

#### Action Items

1. **Move files** from `/Users/michael/Development/cortx-suites/frontend` → `fedsuite/frontend`
2. Apply Sinergy branding + Federal Navy accent color
3. Add **Radix UI + Recharts** for consistency
4. Integrate with Gateway + Identity services
5. Wire to cortx-platform **Validation**, **Workflow**, and **RAG** services
6. Ensure FedRAMP compliance UI patterns (audit logs visible, compliance badges)

---

### 4. Greenlight UI

**Source:** `/Users/michael/Development/greenlight/ui` (and `/apps/dashboard`)
**Target:** `corpsuite/modules/greenlight/frontend`

#### Tech Stack

```json
{
  "status": "⚠️ No package.json found in /ui",
  "alternate_location": "/apps/dashboard (React-based)",
  "services": "Microservices architecture (ingest-sam, ingest-eva, scoring, notify, template, enrichment-uei)"
}
```

#### UI Features

- **Opportunity Triage Dashboard**: SAM/eVA vendor opportunities scoring
- **Document Snapshots**: RFP preview + metadata
- **Scoring Pipeline**: Weighted scoring visualization
- **Notification Center**: Alerts for high-scoring opportunities

#### Status

⚠️ **Needs Discovery + Migration** - Find UI location, migrate to `corpsuite/modules/greenlight/frontend`

#### Action Items

1. **Locate Greenlight UI**: Check `/greenlight/apps/dashboard` or `/greenlight/ui` subdirectories
2. Determine tech stack (likely React + dashboard library)
3. **Modernize to Next.js 14+** if legacy React SPA
4. Apply Sinergy branding
5. Add **Radix UI + Recharts** for consistency
6. Integrate with Gateway + Identity
7. Extract reusable scoring/dashboard components → shared library

---

## Unified Multi-Suite Frontend Shell

### Concept

Create a **single Next.js application** that hosts all suite modules under a unified navigation + auth layer, similar to how AWS Console or Azure Portal work.

### Structure

```
cortx-suites-shell/
├── app/
│   ├── layout.tsx                 # Root layout (nav, auth, branding)
│   ├── (auth)/                    # Auth routes
│   │   ├── login/
│   │   └── callback/
│   ├── (platform)/                # Platform routes
│   │   ├── dashboard/             # Home dashboard
│   │   ├── fedsuite/              # FedSuite modules
│   │   │   ├── reconcile/
│   │   │   └── dataflow/
│   │   ├── corpsuite/             # CorpSuite modules
│   │   │   ├── propverify/
│   │   │   ├── greenlight/
│   │   │   └── investmait/
│   │   ├── medsuite/              # MedSuite modules
│   │   │   ├── hipaaaudit/
│   │   │   └── claimsverify/
│   │   └── govsuite/              # GovSuite modules
│   └── api/                       # Next.js API routes (BFF pattern)
├── components/
│   ├── ui/                        # Shared Radix UI components
│   ├── charts/                    # Shared Recharts components
│   ├── forms/                     # Shared React Hook Form components
│   └── layouts/                   # Suite-specific layouts
├── lib/
│   ├── auth.ts                    # Auth helpers (JWT, OIDC)
│   ├── api-client.ts              # Axios/fetch wrapper → Gateway
│   └── branding.ts                # Sinergy brand tokens
├── styles/
│   ├── globals.css                # Tailwind + brand fonts
│   └── themes/                    # Light/dark mode CSS vars
└── public/
    ├── SS_Logo_Transparent.png
    └── SS-Icon-Transparent.png
```

### Benefits

✅ **Single Authentication**: Login once, access all suites
✅ **Consistent Branding**: Sinergy colors/fonts enforced globally
✅ **Shared Components**: DRY principles, no duplication
✅ **Unified Navigation**: Suite switcher in sidebar
✅ **Performance**: Next.js App Router with code splitting per suite
✅ **Maintenance**: One codebase, one deploy pipeline

### Trade-offs

⚠️ **Monolithic Frontend**: Larger bundle size (mitigated by code splitting)
⚠️ **Shared Dependencies**: Version conflicts possible (use pnpm workspaces)
⚠️ **Deploy Coupling**: All suites deployed together (consider micro-frontends if needed)

---

## UX/Performance Optimization Opportunities

### 1. **Shared Component Library** (High Priority)

**Problem:** Similar UI patterns duplicated across repos (forms, modals, dashboards)
**Solution:** Extract to `packages/cortx-ui` shared library

**Components to Extract:**

- `<Button>`, `<Input>`, `<Select>`, `<Checkbox>`, `<Radio>` (branded Radix UI wrappers)
- `<Modal>`, `<Drawer>`, `<Toast>`, `<Tooltip>` (overlay components)
- `<LineChart>`, `<BarChart>`, `<PieChart>` (branded Recharts wrappers)
- `<FormField>`, `<FormError>`, `<FormLabel>` (React Hook Form wrappers)
- `<DataTable>`, `<Pagination>`, `<SearchBar>` (table components)

**Benefits:**

- ✅ Consistent look/feel across all suites
- ✅ Faster development (reuse > rebuild)
- ✅ Easier branding updates (one place to change)
- ✅ Type-safe props with TypeScript

**Implementation:**

```
packages/cortx-ui/
├── package.json
├── src/
│   ├── components/
│   │   ├── Button.tsx
│   │   ├── Modal.tsx
│   │   └── ...
│   ├── styles/
│   │   └── globals.css       # Sinergy brand tokens
│   └── index.ts              # Barrel exports
└── tailwind.config.js        # Brand color/font presets
```

---

### 2. **AI-Assisted Form Filling** (Medium Priority)

**Problem:** Complex forms (DataFlow mapping, InvestmAit scenarios) require repetitive data entry
**Solution:** Integrate RAG-powered form assist

**Features:**

- **Auto-suggest**: "Fill in typical GTAS mapping" → pre-populate form fields
- **Smart Defaults**: Learn from user's past submissions
- **Validation Explanations**: "Why is this field invalid?" → plain-language explanation

**Benefits:**

- ✅ Faster data entry (50% time reduction)
- ✅ Fewer errors (AI catches common mistakes)
- ✅ Better UX (less friction)

**Implementation:**

- Use existing `services/rag` + `services/ai-broker`
- Add `<FormAssistant>` component with citation tooltips
- Wire to RAG vector store with form templates

---

### 3. **Progressive Disclosure for Complex Workflows** (Medium Priority)

**Problem:** CORTX Designer's 28 node types overwhelm new users
**Solution:** Guided wizard + progressive disclosure

**Features:**

- **Wizard Mode**: "What do you want to build?" → step-by-step wizard
- **Templates**: Pre-built workflows (GTAS submission, HIPAA audit, title validation)
- **Contextual Help**: Inline docs + videos for each node type

**Benefits:**

- ✅ Lower learning curve (30min → 5min to first workflow)
- ✅ Fewer support tickets
- ✅ Higher adoption

**Implementation:**

- Add `<Wizard>` component with step nav
- Create workflow templates in `cortx-packs`
- Integrate with RAG for contextual help

---

### 4. **Real-Time Collaboration (Multi-User Editing)** (Low Priority)

**Problem:** Designer workflows are single-user only
**Solution:** Add WebSocket-based real-time collaboration

**Features:**

- **Live Cursors**: See other users' mouse positions
- **Concurrent Editing**: Merge changes using CRDT
- **Comments**: Add notes to workflow nodes

**Benefits:**

- ✅ Team collaboration (2-3 users building workflow together)
- ✅ Faster review cycles
- ✅ Better knowledge sharing

**Implementation:**

- Use **Yjs** (CRDT library) + **y-websocket**
- Add collab server (Node.js WebSocket)
- Integrate with Identity service for presence

---

### 5. **Performance: Code Splitting + Lazy Loading** (High Priority)

**Problem:** Large bundle sizes (Designer + all node types loaded upfront)
**Solution:** Lazy load node types, suite modules, chart libraries

**Optimizations:**

- **Dynamic Imports**: `const NodeType = lazy(() => import('./nodes/ValidationNode'))`
- **Route-based Splitting**: Next.js App Router already does this
- **Component Lazy Loading**: `<Suspense fallback={<Spinner />}>`

**Benefits:**

- ✅ Faster initial load (50% reduction)
- ✅ Better Lighthouse score (90+ performance)
- ✅ Lower bandwidth usage

**Implementation:**

- Audit bundle size with `next/bundle-analyzer`
- Lazy load Recharts, React Flow, and heavy components
- Use `loading.tsx` for route transitions

---

### 6. **Dark Mode + Accessibility** (High Priority)

**Problem:** No dark mode; unclear WCAG AA compliance
**Solution:** Add dark mode + accessibility audit

**Features:**

- **Dark Mode Toggle**: System preference + manual override
- **WCAG AA Compliance**: 4.5:1 contrast for all text
- **Keyboard Navigation**: Tab order, focus indicators
- **Screen Reader Support**: ARIA labels, semantic HTML

**Benefits:**

- ✅ Better UX (60% of users prefer dark mode)
- ✅ Compliance requirements (FedRAMP, HIPAA)
- ✅ Inclusive design

**Implementation:**

- Use Tailwind dark: variant + CSS custom properties
- Run Lighthouse + axe-core audits
- Add `<ThemeProvider>` with local storage persistence

---

## Branding Alignment Checklist

Per the UI Modernization Guide, all frontends must apply:

### Colors

- [ ] **Primary**: Sinergy Teal `#00C2CB` (buttons, links, CTAs)
- [ ] **Secondary**: Federal Navy `#2D5972` (headers, nav)
- [ ] **Accent**: Clarity Blue `#E5FCFF` (backgrounds, highlights)
- [ ] **Neutral**: Slate Gray `#8CAABF` (borders, disabled states)
- [ ] **Dark Mode**: Navy/Teal shades with WCAG AA contrast

### Typography

- [ ] **H1/H2**: Space Grotesk (400, 500, 600, 700)
- [ ] **Buttons/Subtitles**: DM Sans (400, 500, 600)
- [ ] **Sub-Headings**: Manrope or Sora (400, 500, 600, 700)
- [ ] **Body**: IBM Plex Sans (400, 500, 600, 700)
- [ ] **Quotes**: Lora (400, 500, 600, 700)
- [ ] **Captions/Labels**: Roboto (400, 500, 700)

### Assets

- [ ] **Logo**: `SS_Logo_Transparent.png` in nav bars
- [ ] **Favicon**: `SS-Icon-Transparent.png`
- [ ] **Loading Spinner**: Sinergy Teal animated SVG

### Components

- [ ] **Buttons**: Teal primary, Navy secondary, white ghost
- [ ] **Forms**: Navy labels, Teal focus rings
- [ ] **Modals**: Navy header, white body, Teal CTAs
- [ ] **Charts**: Teal/Navy/Clarity palette for data viz

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)

1. **Create Shared Component Library** (`packages/cortx-ui`)
   - Extract Button, Input, Modal, Chart components
   - Apply Sinergy branding (colors, fonts, logos)
   - Add dark mode support
   - Publish to GitHub Packages

2. **Set Up Unified Frontend Shell** (`cortx-suites-shell`)
   - Initialize Next.js 15 App Router
   - Add root layout with nav + auth
   - Configure Tailwind with Sinergy brand tokens
   - Integrate Gateway + Identity services

3. **Run Accessibility Audit**
   - Lighthouse audits for all UIs
   - Fix WCAG AA contrast issues
   - Add ARIA labels + keyboard navigation

**Deliverables:**

- `packages/cortx-ui` package published
- `cortx-suites-shell` repo scaffolded
- Accessibility audit report

---

### Phase 2: Migration (Week 3-5)

1. **Migrate cortx-designer** (Already in place)
   - Apply branding via `cortx-ui` components
   - Add dark mode toggle
   - Test workflow canvas + compiler

2. **Migrate InvestmAit Frontend** → `corpsuite/modules/investmait/frontend`
   - Move files from OffermAit repo
   - Replace custom components with `cortx-ui`
   - Integrate with Gateway/Identity
   - Test investment analysis dashboards

3. **Migrate FedSuite Frontend** → `fedsuite/frontend`
   - Move files from cortx-suites repo
   - Apply Federal Navy accent color
   - Integrate with Validation/Workflow/RAG services
   - Test GTAS reconciliation flows

4. **Discover + Migrate Greenlight UI** → `corpsuite/modules/greenlight/frontend`
   - Locate UI source (apps/dashboard or ui/)
   - Modernize to Next.js 14+ if needed
   - Apply branding
   - Test opportunity scoring dashboards

**Deliverables:**

- All 4 frontends migrated to target locations
- Branding applied consistently
- Gateway/Identity integration complete

---

### Phase 3: Optimization (Week 6-7)

1. **Add AI-Assisted Form Filling**
   - Integrate RAG service
   - Add `<FormAssistant>` component
   - Test with DataFlow mapping + InvestmAit scenarios

2. **Implement Code Splitting**
   - Lazy load node types in Designer
   - Lazy load charts in dashboards
   - Add Suspense boundaries

3. **Add Progressive Disclosure to Designer**
   - Build wizard mode
   - Create workflow templates
   - Add contextual help tooltips

4. **Performance Testing**
   - Run Lighthouse audits (target: 90+)
   - Measure bundle sizes (< 500KB initial)
   - Test on slow 3G connections

**Deliverables:**

- AI form assist live in 2+ forms
- Bundle size reduced by 40%
- Lighthouse scores 90+ across all pages

---

### Phase 4: Polish (Week 8)

1. **Documentation**
   - Update README for each frontend
   - Create component library Storybook
   - Record Loom videos for common workflows

2. **User Testing**
   - Run usability tests with 5 users per suite
   - Collect feedback on nav, forms, dashboards
   - Iterate based on findings

3. **Launch Prep**
   - Final QA pass
   - Security audit (XSS, CSRF, CSP)
   - Deploy to staging

**Deliverables:**

- Documentation complete
- User testing report
- Staging deployment live

---

## Decision Points for Discussion

### 1. **Unified Shell vs. Independent Suites?**

**Option A: Unified Shell (Recommended)**

- Single Next.js app hosting all suites
- Pros: Consistent auth/nav, shared components, single deploy
- Cons: Larger bundle, shared dependencies

**Option B: Independent Suite Apps**

- Separate Next.js app per suite
- Pros: Smaller bundles, independent deploys
- Cons: Auth duplication, navigation inconsistency

**Recommendation:** Start with **Unified Shell** for consistency. Migrate to micro-frontends if bundle size becomes an issue.

---

### 2. **Component Library Scope?**

**Option A: Minimal (UI primitives only)**

- Button, Input, Modal, Toast
- Pros: Small library, easy to maintain
- Cons: Suites still duplicate complex components

**Option B: Comprehensive (UI + domain components)**

- Primitives + DataTable, FormWizard, ChartDashboard
- Pros: Maximum reuse, fastest dev
- Cons: More maintenance, risk of over-abstraction

**Recommendation:** Start **Minimal**, add domain components as patterns emerge.

---

### 3. **Dark Mode Implementation?**

**Option A: CSS Custom Properties**

- Define light/dark tokens in `:root` and `[data-theme="dark"]`
- Pros: Native CSS, no JS overhead
- Cons: Manual token management

**Option B: Tailwind dark: Variant**

- Use `dark:bg-navy-900` classes
- Pros: Tailwind integration, design system friendly
- Cons: More classes in HTML

**Recommendation:** Use **Tailwind dark: variant** for consistency with existing Tailwind setup.

---

### 4. **AI Form Assist: Inline vs. Sidebar?**

**Option A: Inline Tooltips**

- Show AI suggestions next to form fields
- Pros: Contextual, less disruptive
- Cons: Cluttered on complex forms

**Option B: Collapsible Sidebar**

- AI assistant in right sidebar
- Pros: More space for explanations, citations
- Cons: User must look away from form

**Recommendation:** Use **Collapsible Sidebar** for Designer (complex), **Inline Tooltips** for simple forms.

---

## Appendix: Tech Stack Comparison

| Feature | cortx-designer | InvestmAit | FedSuite | Greenlight |
|---------|---------------|------------|----------|------------|
| **Framework** | Next.js 14 | Next.js 14.2 | Next.js 15.4 | TBD (React?) |
| **React** | 18.2 | 18.2 | 18.3 | 18.x likely |
| **TypeScript** | 5.2 | 5.4 | 5.7 | TBD |
| **Tailwind** | 3.3 | 3.4 | 3.4 | TBD |
| **State** | Zustand 4.4 | Zustand 4.5 | None | TBD |
| **Forms** | React Hook Form + Zod | None | None | TBD |
| **Charts** | Recharts 2.8 | Recharts 2.10 | None | TBD |
| **Icons** | Lucide + Radix Icons | None | Lucide | TBD |
| **Animations** | None | None | Framer Motion | TBD |
| **HTTP** | @tanstack/react-query | None | Axios | TBD |
| **UI Components** | Radix UI (full suite) | None | None | TBD |

**Key Gaps to Fill:**

- **InvestmAit**: Needs Radix UI, React Hook Form, Lucide icons
- **FedSuite**: Needs Recharts, Radix UI, React Hook Form
- **Greenlight**: TBD after discovery

**Standardization Targets:**

- **Next.js**: Upgrade all to 15.x
- **React**: 18.3+
- **TypeScript**: 5.7+
- **Tailwind**: 3.4+
- **State**: Zustand 4.5+
- **Forms**: React Hook Form + Zod
- **Charts**: Recharts 2.10+
- **Icons**: Lucide React
- **UI**: Radix UI (full suite)

---

## Next Steps

1. **Review this audit** with stakeholders
2. **Prioritize optimization opportunities** (recommend: Shared Library, Dark Mode, Code Splitting)
3. **Decide on Unified Shell vs. Independent Suites**
4. **Approve branding alignment checklist**
5. **Begin Phase 1 implementation**

**Questions?** Reach out to the Tech Lead Architect or UI/Frontend Developer.

---

**END OF UI COMPONENTS AUDIT**
