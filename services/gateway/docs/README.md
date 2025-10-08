# CORTX Gateway Service Documentation

Welcome to the CORTX Gateway Service documentation. This directory contains comprehensive documentation for the API gateway that serves as the entry point for the entire CORTX platform.

## Documentation Structure

- **[Functional Design Document (FDD)](./GATEWAY_FDD.md)** - Complete functional specification
- **[Architecture](./architecture/)** - Architecture Decision Records (ADRs) and diagrams
- **[Operations](./operations/)** - Deployment and troubleshooting guides
- **[Testing](./testing/)** - Test plans and strategies

## Quick Links

- [Deployment Guide](./operations/deployment.md)
- [Troubleshooting Guide](./operations/troubleshooting.md)
- [OpenAPI Specification](../openapi.yaml)

## Service Overview

The Gateway service is a FastAPI-based reverse proxy that:

- Terminates incoming requests and enforces authentication policies
- Routes traffic to orchestration endpoints, suite proxies, and service discovery APIs
- Brokers RulePack validation requests via the policy router and registry client
- Provides health and info probes for installers and CI/CD

**Port**: 8080
**Technology**: FastAPI (Python 3.11+)
**Dependencies**: Identity service, Validation service, various suite backends
