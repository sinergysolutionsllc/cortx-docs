# Prompt: Generate CORTX Service Docs

Role: You are the Docs Automation Agent for CORTX by Sinergy.
Objective: Create the full `/docs/services/` section with Markdown pages for each platform service, modeled on the given structure and tone. Include Mermaid diagrams and align with OpenAPI/Schema templates. At the end, output the optional nav tweak for `mkdocs.yml`.

---

## Instructions

1. Create the following files under `/docs/services/`:
   - `index.md`
   - `gateway.md`
   - `identity.md`
   - `validation.md`
   - `ai-broker.md`
   - `workflow.md`
   - `compliance.md`
   - `ledger.md`
   - `ocr.md`
   - `rag.md`

2. For each file:
   - Start with a top-level heading: `# <Service Name> (Port)`
   - Provide **Purpose**, **Responsibilities**, **Authentication**.
   - List **Sample endpoints** with `GET/POST` routes.
   - Include a **Mermaid diagram** showing that service in context.
   - End with an **OpenAPI** reference (path to stub under `services/<svc>/openapi.yaml`) and, if relevant, JSON Schema example path from `/templates/`.

3. Use the exact examples provided in the draft content. Preserve Markdown and Mermaid formatting.

---

## Expected Output

### `docs/services/index.md`
```md
# Platform Services

CORTX centralizes core capabilities as microservices behind the Gateway:

| Service | Port | Purpose |
|---|---:|---|
| Gateway | 8080 | Entry point, routing, policy enforcement |
| Identity | 8082 | JWT/OIDC, RBAC, session management |
| Validation | 8083 | JSON Schema + RulePack validation |
| AI Broker | 8085 | Provider routing (Vertex/OpenAI), PII redaction, embeddings |
| Workflow | 8130 | Workflow orchestration, Pack execution |
| Compliance | 8135 | Compliance logs & reporting |
| Ledger | 8136 | Append-only, SHA-256 chain evidence (tamper-evident) |
| OCR | 8137 | Document → text/fields extraction |
| RAG | 8138 | Hierarchical retrieval (Platform/Suite/Module/Entity) |

```mermaid
flowchart LR
  User-->Gateway
  Gateway-->Identity
  Gateway-->Validation
  Gateway-->Workflow
  Gateway-->Compliance
  Gateway-->Ledger
  Gateway-->OCR
  Gateway-->RAG
  RAG-->DB[(PostgreSQL + pgvector)]
  Ledger-->Evidence[(Immutable Chain)]


  ### `docs/services/gateway.md`
… (include full Gateway doc as drafted)

### `docs/services/identity.md`
… (include full Identity doc as drafted)

### `docs/services/validation.md`
… (include full Validation doc as drafted)

### `docs/services/ai-broker.md`
… (include full AI Broker doc as drafted)

### `docs/services/workflow.md`
… (include full Workflow doc as drafted)

### `docs/services/compliance.md`
… (include full Compliance doc as drafted)

### `docs/services/ledger.md`
… (include full Ledger doc as drafted)

### `docs/services/ocr.md`
… (include full OCR doc as drafted)

### `docs/services/rag.md`
… (include full RAG doc as drafted)

---

## Optional nav tweak (if you want sub-entries in `mkdocs.yml`)

```yaml
nav:
  - Services:
    - services/index.md
    - Gateway: services/gateway.md
    - Identity: services/identity.md
    - Validation: services/validation.md
    - AI Broker: services/ai-broker.md
    - Workflow: services/workflow.md
    - Compliance: services/compliance.md
    - Ledger: services/ledger.md
    - OCR: services/ocr.md
    - RAG: services/rag.md

    Output Rules
	•	Output each file content with correct headings, sections, and diagrams.
	•	Do not shorten or omit; use the full draft content for each service.
	•	Keep the MkDocs nav tweak at the end.