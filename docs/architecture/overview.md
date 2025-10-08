# CORTX Platform Architecture Overview

**Version**: 1.0
**Status**: Active

This document provides a high-level overview of the CORTX platform architecture. The platform is designed as a set of microservices that provide core capabilities for compliance, orchestration, and AI-powered assistance.

## Guiding Principles

- **Modularity**: Services are independent and can be deployed and scaled separately.
- **Centralized Core**: Core functions like identity, validation, and workflow are centralized for consistency.
- **Extensibility**: The platform is designed to be extended with new suites and modules for different domains.
- **API-First**: All platform capabilities are exposed through a consistent REST API.

## Key Architectural Components

- **Gateway**: A single entry point for all API requests, responsible for routing, authentication, and rate limiting.
- **Core Services**: A set of services providing the fundamental capabilities of the platform, including:
  - `svc-identity`: Manages users, tenants, and authentication.
  - `svc-validation`: Executes RulePacks to validate data.
  - `svc-workflow`: Orchestrates business processes using WorkflowPacks.
  - `svc-compliance`: Logs audit trails and generates compliance reports.
- **AI Services**: A set of services providing AI and machine learning capabilities:
  - `svc-rag` (ThinkTank): Provides retrieval-augmented generation (RAG) capabilities.
  - `svc-ai-broker`: A broker for accessing various large language models (LLMs).
  - `svc-ocr`: Extracts text from documents.
- **Data Stores**: The platform uses PostgreSQL with the `pgvector` extension for structured data and vector storage, and Redis for caching.

For more detailed information on specific services, please refer to the documents in the [services](./services/) directory.
