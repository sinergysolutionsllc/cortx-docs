# CORTX AI Broker Service Documentation

Welcome to the CORTX AI Broker Service documentation. This service provides unified access to AI/ML providers including Vertex AI, OpenAI, and Anthropic.

## Documentation Structure

- **[Functional Design Document (FDD)](./AI_BROKER_FDD.md)** - Complete functional specification
- **[Architecture](./architecture/)** - Architecture Decision Records (ADRs) and diagrams
- **[Operations](./operations/)** - Deployment and troubleshooting guides
- **[Testing](./testing/)** - Test plans and strategies

## Quick Links

- [Deployment Guide](./operations/deployment.md)
- [Troubleshooting Guide](./operations/troubleshooting.md)

## Service Overview

The AI Broker service provides:

- Provider routing (Vertex AI, OpenAI, Anthropic Claude)
- PII redaction and data masking
- Embedding generation for RAG
- Text generation and completion
- Function calling support
- Streaming responses

**Port**: 8085
**Technology**: FastAPI (Python 3.11+)
**Dependencies**: Vertex AI, Optional: OpenAI/Anthropic APIs
