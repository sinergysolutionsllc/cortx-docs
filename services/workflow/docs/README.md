# CORTX Workflow Service Documentation

Orchestrates multi-step business processes using WorkflowPacks with support for complex control flow, error handling, and state management.

## Documentation Structure

- **[Functional Design Document (FDD)](./WORKFLOW_FDD.md)** - Complete functional specification
- **[Architecture](./architecture/)** - Architecture Decision Records (ADRs) and diagrams
- **[Operations](./operations/)** - Deployment and troubleshooting guides
- **[Testing](./testing/)** - Test plans and strategies

## Service Overview

- WorkflowPack execution engine
- Step orchestration with dependencies
- Conditional branching and loops
- Error handling and retry logic
- State persistence and recovery
- Workflow monitoring and metrics

**Port**: 8130
**Technology**: FastAPI (Python 3.11+)
**Dependencies**: Validation, Compliance, Ledger services
