# CORTX Workflow Service

Platform service for workflow orchestration and Pack execution.

- **Port**: 8130
- **Purpose**: WorkflowPack execution engine, step sequencing, state management
- **Endpoints**: `/healthz`, `/readyz`, `/livez`, `/metrics`
- **Security**: No secrets in code. Use JWT + SecretManager/KMS
- **Observability**: OTEL-friendly; correlation ID via `X-Correlation-ID`

## Installation

### Prerequisites

- Python 3.11+
- The `cortx_backend` package (installed automatically)

### Install in Development Mode

```bash
# First, install cortx_backend shared library
pip install -e ../../packages/cortx_backend

# Then install this service
pip install -e .
```

## Configuration

### Auth & Tracing (Quick Start)

```bash
# Gateway URL (required)
export CORTX_GATEWAY_URL=http://localhost:8080

# Auth (enable in non-dev)
export REQUIRE_AUTH=true
export CORTX_IDENTITY_URL=https://identity.example
export JWT_AUDIENCE=workflow
export JWT_ISSUER=https://identity.example

# Tracing (OTLP/HTTP)
export OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.observability:4318/v1/traces
```

## Run Locally

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8130 --reload
```

## Test

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Container

```bash
docker build -t propverify/workflow-svc:dev -f backend/workflow_svc/Dockerfile .
```

## K8s

- See `k8s/workflow-svc/*`. Configure secrets via KMS/Secret Manager; do not commit secrets.
