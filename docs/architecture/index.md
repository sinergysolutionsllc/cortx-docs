# Architecture
High-level topology and flows.

```mermaid
flowchart LR
  User-->Gateway
  Gateway-->Identity & Validation & Workflow & Compliance & Ledger & OCR & RAG
  RAG-->DB[(PostgreSQL + pgvector)]
  Ledger-->Evidence[(Immutable Chain)]