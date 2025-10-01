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