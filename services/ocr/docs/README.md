# CORTX OCR Service Documentation

Multi-tier OCR pipeline with automatic escalation from Tesseract to Claude Vision to human review for maximum accuracy.

## Documentation Structure

- **[Functional Design Document (FDD)](./OCR_FDD.md)** - Complete functional specification
- **[Architecture](./architecture/)** - Architecture Decision Records (ADRs) and diagrams
- **[Operations](./operations/)** - Deployment and troubleshooting guides
- **[Testing](./testing/)** - Test plans and strategies

## Quick Links

- [Service README](../README.md) - Detailed usage and examples
- [Implementation Summary](../IMPLEMENTATION_SUMMARY.md)
- [Quick Start Guide](../QUICKSTART.md)

## Service Overview

- 3-tier OCR approach (Tesseract → Claude Vision → Human Review)
- Automatic tier escalation based on confidence
- Hash-based caching to avoid reprocessing
- Multi-page document support
- Structured field extraction
- Background job processing

**Port**: 8137
**Technology**: FastAPI (Python 3.11+)
**Dependencies**: PostgreSQL, Tesseract, Anthropic API
