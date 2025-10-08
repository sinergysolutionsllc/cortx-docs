# Platform Services

CORTX centralizes core capabilities as microservices behind the Gateway:

| Service | Port | Purpose |
|---|---:|---|
| Gateway | 8080 | Entry point, routing, policy enforcement |
| Identity | 8082 | JWT/OIDC, RBAC, session management |
| Validation | 8083 | JSON Schema + RulePack validation |
| AI Broker | 8085 | Provider routing (Vertex/OpenAI), PII redaction, embeddings |
| Config Service | 8086 | Hierarchical configuration, feature flags, tenant overrides |
| Packs Registry | 8089 | Pack catalog metadata and certification lifecycle |
| RulePack Registry | 8091 | Validates/signs RulePacks, hydrates validation caches |
| Ingestion | 8092 | Connectors and normalization into Pack-defined schemas |
| Events | 8094 | Pub/Sub backbone for ingestion, workflow, compliance signals |
| Observability | 8096 | Central metrics/logs/tracing and alert management |
| Workflow | 8130 | Workflow orchestration, Pack execution |
| Compliance | 8135 | Compliance logs & reporting |
| Ledger | 8136 | Append-only, SHA-256 chain evidence (tamper-evident) |
| OCR | 8137 | Document → text/fields extraction |
| RAG | 8138 | Hierarchical retrieval (Platform/Suite/Module/Entity) |
| Compliance Scanner | 8140 | Pack-driven static/runtime compliance scanning |
| DataFlow | 8145 | Transformation & reconciliation pipelines (formerly FedTransform) |

```mermaid
flowchart LR
  User-->Gateway
  Gateway-->Identity
  Gateway-->Config
  Gateway-->Packs
  Gateway-->Events
  Gateway-->Workflow
  Workflow-->DataFlow
  DataFlow-->Validation
  DataFlow-->Compliance
  DataFlow-->Ledger
  Events-->Observability
  Observability-->Dashboards[(Grafana/Cloud Monitoring)]
  Gateway-->OCR
  OCR-->Ingestion
  Ingestion-->DataFlow
  Gateway-->RAG
  RAG-->DB[(PostgreSQL + pgvector)]
  Ledger-->Evidence[(Immutable Chain)]
  Compliance-->Scanner
  Scanner-->Ledger
