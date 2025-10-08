# CORTX Identity Service Documentation

Welcome to the CORTX Identity Service documentation. This service handles authentication, authorization, and identity management for the CORTX platform.

## Documentation Structure

- **[Functional Design Document (FDD)](./IDENTITY_FDD.md)** - Complete functional specification
- **[Architecture](./architecture/)** - Architecture Decision Records (ADRs) and diagrams
- **[Operations](./operations/)** - Deployment and troubleshooting guides
- **[Testing](./testing/)** - Test plans and strategies

## Quick Links

- [Deployment Guide](./operations/deployment.md)
- [Troubleshooting Guide](./operations/troubleshooting.md)
- [OpenAPI Specification](../openapi.yaml)

## Service Overview

The Identity service provides:

- JWT-based authentication and token issuance
- User and tenant management
- Role-based access control (RBAC)
- Session management and token refresh
- OAuth2/OIDC integration (future)

**Port**: 8082
**Technology**: FastAPI (Python 3.11+)
**Dependencies**: PostgreSQL database
