# CORTX RAG Service Documentation

Hierarchical Retrieval-Augmented Generation system with 4-level knowledge organization (Platform/Suite/Module/Entity).

## Documentation Structure

- **[Functional Design Document (FDD)](./RAG_FDD.md)** - Complete functional specification
- **[Architecture](./architecture/)** - Architecture Decision Records (ADRs) and diagrams
- **[Operations](./operations/)** - Deployment and troubleshooting guides
- **[Testing](./testing/)** - Test plans and strategies

## Service Overview

- 4-level hierarchical knowledge base
- Vector similarity search (pgvector)
- Document chunking and embedding
- Contextual retrieval with metadata
- AI-powered answer generation
- Knowledge base management

**Port**: 8138
**Technology**: FastAPI (Python 3.11+)
**Dependencies**: PostgreSQL with pgvector, AI Broker
