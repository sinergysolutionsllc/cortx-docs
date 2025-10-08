# CORTX Ledger Service Documentation

Append-only, SHA-256 hash-chained immutable ledger for tamper-proof audit trails and evidence storage.

## Documentation Structure

- **[Functional Design Document (FDD)](./LEDGER_FDD.md)** - Complete functional specification
- **[Architecture](./architecture/)** - Architecture Decision Records (ADRs) and diagrams
- **[Operations](./operations/)** - Deployment and troubleshooting guides
- **[Testing](./testing/)** - Test plans and strategies

## Service Overview

- Append-only data structure
- SHA-256 hash chaining for integrity
- Tamper detection and verification
- High-throughput writes
- Evidence storage and retrieval
- Chain verification

**Port**: 8136
**Technology**: FastAPI (Python 3.11+)
**Dependencies**: PostgreSQL
