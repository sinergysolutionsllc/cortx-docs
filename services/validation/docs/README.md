# CORTX Validation Service Documentation

Platform service for JSON Schema + RulePack validation with dual-mode support (static and AI-powered).

## Documentation Structure

- **[Functional Design Document (FDD)](./VALIDATION_FDD.md)** - Complete functional specification
- **[Architecture](./architecture/)** - Architecture Decision Records (ADRs) and diagrams
- **[Operations](./operations/)** - Deployment and troubleshooting guides
- **[Testing](./testing/)** - Test plans and strategies

## Service Overview

- JSON Schema validation
- RulePack execution (Python-based rules)
- Dual validation modes (static JSON + dynamic RAG)
- Compliance rule enforcement
- Validation result caching

**Port**: 8083
**Technology**: FastAPI (Python 3.11+)
**Dependencies**: RAG Service (for AI validation), Compliance Service
