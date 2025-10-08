# CORTX Validation Service

Platform service for JSON Schema + RulePack validation.

- **Port**: 8083
- **Purpose**: Integrate with CORTX Platform (Validation, Compliance)
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
export JWT_AUDIENCE=validation
export JWT_ISSUER=https://identity.example

# Tracing (OTLP/HTTP)
export OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.observability:4318/v1/traces
```

## Run Locally

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8083 --reload
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
docker build -t propverify/validation-svc:dev -f backend/validation_svc/Dockerfile .
```

## K8s

- See `k8s/validation-svc/*`. Configure secrets via KMS/Secret Manager; do not commit secrets.
