# CORTX by Sinergy

**CORTX** is the AI orchestration and compliance platform powering all Sinergy Solutions product suites. It is **ERP-agnostic, compliance-first, and modular**, serving as the intelligence layer that ingests data, validates against rules, orchestrates workflows, and enables Retrieval-Augmented Generation (RAG) with explainable AI.

---

## 🚀 Mission

To provide a **world-class AI core** that automates reconciliation, compliance, and decision-making across regulated industries — starting with federal financials and expanding to healthcare, corporate compliance, and state/local government.

CORTX separates **platform services** from **suite-specific RulePacks/WorkflowPacks** to remain flexible and future-proof.

---

## 🧩 Core Platform Services

| Service       | Port | Purpose |
|---------------|------|---------|
| **Gateway**   | 8080 | Entry point, routing, policy enforcement |
| **Identity**  | 8082 | JWT/OIDC, RBAC, session management |
| **Validation**| 8083 | JSON schema + RulePack validation |
| **AI Broker** | 8085 | Provider routing (Vertex, OpenAI), PII redaction, embeddings |
| **Workflow**  | 8130 | Workflow orchestration, Pack execution |
| **Compliance**| 8135 | Compliance logs, reports |
| **Ledger**    | 8136 | Append-only, SHA-256 hash-chained evidence (tamper-proof) |
| **OCR**       | 8137 | Document → text/fields extraction (Tesseract/DocAI) |
| **RAG**       | 8138 | 4-level hierarchical retrieval (Platform/Suite/Module/Entity) |

---

## 📚 Hierarchical RAG Architecture

CORTX implements a **4-level RAG hierarchy** to give AI contextual intelligence:

1. **Platform** — universal policy & best practices  
2. **Suite** — domain-specific regulations (Fed, Corp, Med, Gov)  
3. **Module** — technical schemas, validation logic  
4. **Entity** — tenant/org-specific rules & SOPs  

See [HIERARCHICAL_RAG_ARCHITECTURE.md](./HIERARCHICAL_RAG_ARCHITECTURE.md) for full details.

---

## 🏛 Suites & Modules

- **FedSuite** → FedReconcile, DataFlow  
- **CorpSuite** → PropVerify, Greenlight, InvestmAit  
- **MedSuite** → ClaimsVerify, HIPAAAudit  
- **GovSuite** → TBD modules  

All suites now leverage **centralized OCR, Ledger, and RAG services**.

---

## 🔐 Environment Strategy

CORTX follows a strict **dev → staging → prod** promotion model.

| Aspect | Dev | Staging | Prod |
|--------|-----|---------|------|
| Identity | In-repo OIDC + GitHub/Google | Same + restricted IdP | Keycloak/Auth0 or hardened OIDC |
| AI Providers | Vertex + optional OpenAI (flagged) | Vertex primary | Vertex only (ATO-aligned) |
| Database | Cloud SQL (pgvector) | Cloud SQL HA | Cloud SQL HA |
| Redis | MemoryStore basic | MemoryStore standard | MemoryStore standard |
| Storage | gcs-{svc}-dev | gcs-{svc}-stg | gcs-{svc}-prod |
| Secrets | Secret Manager (dev) | Secret Manager (stg) | Secret Manager (prod) |

See [CORTX_PLATFORM_FDD.md](./CORTX_PLATFORM_FDD.md) for deployment details.

---

## 👩‍💻 Developer Quickstart

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & docker-compose
- PostgreSQL with pgvector extension

### Local Development

```bash
# Clone repo
git clone https://github.com/sinergysolutionsllc/cortx.git
cd cortx

# Start services
docker-compose up

# Run backend tests
pytest

# Run frontend
cd apps/designer && npm run dev
