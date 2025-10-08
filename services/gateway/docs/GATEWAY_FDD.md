# CORTX Gateway Service - Functional Design Document

**Version**: 1.0.0
**Last Updated**: 2025-10-08
**Status**: Active

## 1. Purpose and Scope

### 1.1 Purpose

The CORTX Gateway service serves as the unified entry point and API gateway for the entire CORTX platform. It provides centralized request routing, authentication enforcement, policy brokering, and observability for all client requests.

### 1.2 Scope

The Gateway service is responsible for:

- HTTP request termination and routing
- JWT-based authentication enforcement
- Suite-specific proxy routing (FedSuite, PropVerify, etc.)
- Orchestration API endpoints for validation workflows
- Analytics endpoints for JSON vs RAG comparison
- Service discovery for local development
- Health and readiness probes

### 1.3 Out of Scope

- Business logic implementation (delegated to downstream services)
- Data persistence (stateless proxy pattern)
- Complex workflow orchestration (handled by Workflow service)
- Direct database access

## 2. Key Features

### 2.1 Request Routing

- **Orchestration Routes** (`/jobs/*`, `/explain`, `/failures/*`)
  - Validation job creation and status
  - AI-powered failure explanation
  - User decision tracking

- **Suite Proxies**
  - `/fedsuite/*` - Federal financial reconciliation
  - `/propverify/*` - Corporate property verification
  - Future: `/medsuite/*`, `/govsuite/*`

- **Analytics Routes** (`/analytics/*`)
  - Comparison summary statistics
  - Detailed comparison analysis
  - Time-series trend data
  - Rule-specific performance metrics

- **Infrastructure Routes**
  - `/health` - Liveness probe
  - `/_info` - Service metadata and feature flags
  - `/v1/services` - Service discovery (dev only)

### 2.2 Authentication & Authorization

- JWT token validation via Identity service
- Bearer token extraction from `Authorization` header
- Tenant isolation via `X-Tenant-ID` header
- Request correlation via `X-Request-ID` and `X-Correlation-ID` headers
- Public endpoints: `/health`, `/fedsuite/health`

### 2.3 Policy Enforcement

- RulePack registry integration
- Domain-based routing to appropriate validators
- Mode selection (static JSON vs dynamic RAG validation)
- Cross-origin resource sharing (CORS) configuration

### 2.4 Observability

- Structured logging with correlation IDs
- Request/response tracking
- Error aggregation and reporting
- Performance metrics collection

## 3. API Contracts

### 3.1 Core Endpoints

#### Create Validation Job

```
POST /jobs/validate?domain={domain}&mode={mode}
Headers:
  - X-Tenant-ID: {tenant_id}
  - X-Request-ID: {request_id}
  - Authorization: Bearer {jwt_token}
Body:
  {
    "input_data": {...},
    "options": {...}
  }
Response: 200 OK
  {
    "job_id": "uuid",
    "status": "pending|processing|completed|failed",
    "created_at": "ISO8601"
  }
```

#### Get Job Status

```
GET /jobs/{job_id}
Headers:
  - X-Tenant-ID: {tenant_id}
Response: 200 OK
  {
    "job_id": "uuid",
    "status": "...",
    "results": {...},
    "failures": [...]
  }
```

#### Explain Failure

```
POST /explain?domain={domain}&failure_id={id}
Headers:
  - X-Tenant-ID: {tenant_id}
  - X-Request-ID: {request_id}
Body: {failure_data}
Response: 200 OK
  {
    "explanation": "...",
    "policy_refs": [...],
    "remediation": "..."
  }
```

### 3.2 Analytics Endpoints

#### Comparison Summary

```
GET /analytics/comparison/summary?domain={domain}&days_back={days}
Response: 200 OK
  {
    "total_comparisons": int,
    "agreement_rate": float,
    "json_only_failures": int,
    "rag_only_failures": int,
    "disagreements": int
  }
```

#### Detailed Comparison

```
GET /analytics/comparison/detailed?domain={domain}&rule_category={cat}&confidence_min={min}
Response: 200 OK
  {
    "comparisons": [
      {
        "comparison_id": "uuid",
        "rule_id": "...",
        "json_result": "pass|fail",
        "rag_result": "pass|fail",
        "agreement": bool,
        "rag_confidence": float
      }
    ]
  }
```

### 3.3 Suite Proxies

All suite proxy routes follow the pattern:

```
{GET|POST|PUT|DELETE} /{suite_name}/{path}
Headers:
  - Authorization: Bearer {jwt_token} (verified)
```

Proxied to the appropriate backend service with authentication context preserved.

## 4. Dependencies

### 4.1 Upstream Dependencies

- **Identity Service** (port 8082)
  - JWT token verification
  - User authentication

- **Validation Service** (port 8083)
  - JSON Schema validation
  - RulePack execution

- **RAG Service** (port 8138)
  - AI-powered validation
  - Contextual explanation

- **Compliance Service** (port 8135)
  - Audit logging
  - Decision tracking

- **RulePack Registry** (configured via `CORTX_REGISTRY_URL`)
  - Domain to RulePack mapping
  - Policy retrieval

### 4.2 Downstream Consumers

- **Frontend Applications**
  - Designer (WorkflowPack authoring)
  - ThinkTank (conversational AI)
  - Suite-specific UIs (FedReconcile, PropVerify, etc.)

- **CLI Tools**
  - cortx-cli for administrative operations

- **CI/CD Pipelines**
  - Health checks
  - Integration testing

## 5. Data Models

### 5.1 Request Context

```python
@dataclass
class RequestContext:
    tenant_id: str
    user_id: Optional[str]
    request_id: str
    correlation_id: Optional[str]
    jwt_token: Optional[str]
```

### 5.2 Validation Job

```python
@dataclass
class ValidationJob:
    job_id: str
    tenant_id: str
    domain: str
    mode: Literal["static", "rag"]
    status: Literal["pending", "processing", "completed", "failed"]
    input_data: dict
    results: Optional[dict]
    failures: list[ValidationFailure]
    created_at: datetime
    updated_at: datetime
```

### 5.3 Validation Failure

```python
@dataclass
class ValidationFailure:
    failure_id: str
    rule_id: str
    severity: Literal["error", "warning", "info"]
    message: str
    field_path: Optional[str]
    expected: Optional[Any]
    actual: Optional[Any]
    explanation: Optional[str]
    remediation: Optional[str]
    user_decision: Optional[Literal["accept", "override", "fix"]]
```

### 5.4 Analytics Comparison

```python
@dataclass
class ValidationComparison:
    comparison_id: str
    job_id: str
    rule_id: str
    json_result: Literal["pass", "fail"]
    rag_result: Literal["pass", "fail"]
    agreement: bool
    rag_confidence: float
    json_processing_time_ms: int
    rag_processing_time_ms: int
    created_at: datetime
```

## 6. Configuration

### 6.1 Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CORTX_REGISTRY_URL` | URL | `http://localhost:8081` | RulePack registry service |
| `CORTX_IDENTITY_URL` | URL | `http://localhost:8082` | Identity service for JWT verification |
| `CORTX_VALIDATION_URL` | URL | `http://localhost:8083` | Validation service |
| `CORTX_RAG_URL` | URL | `http://localhost:8138` | RAG service |
| `CORTX_ENV` | string | `dev` | Environment label (dev/staging/prod) |
| `ALLOWED_ORIGINS` | CSV | `http://localhost:3000,...` | CORS allowed origins |
| `LOG_LEVEL` | string | `INFO` | Logging verbosity |
| `REQUIRE_AUTH` | bool | `true` | Enforce JWT authentication |

### 6.2 Feature Flags

Feature flags are exposed via the `/_info` endpoint:

```json
{
  "service": "gateway",
  "version": "1.0.0",
  "features": {
    "analytics_enabled": true,
    "rag_validation": true,
    "suite_proxies": ["fedsuite", "propverify"]
  }
}
```

## 7. Error Handling

### 7.1 Error Response Format

All errors follow the standard format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "request_id": "uuid",
  "timestamp": "ISO8601"
}
```

### 7.2 HTTP Status Codes

| Code | Meaning | Use Case |
|------|---------|----------|
| 200 | OK | Successful request |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid JWT |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | Upstream service unavailable |
| 503 | Service Unavailable | Service temporarily down |

## 8. Security Considerations

### 8.1 Authentication

- All endpoints (except `/health` and suite health checks) require valid JWT
- Tokens verified against Identity service public key
- Token expiration enforced (default: 15 minutes access, 7 days refresh)

### 8.2 Authorization

- Tenant isolation enforced via `X-Tenant-ID` header
- Admin-only endpoints require `admin` role in JWT claims
- Cross-tenant access prevented at gateway level

### 8.3 Input Validation

- Request body size limits enforced (default: 10MB)
- Content-Type validation
- SQL injection prevention (no direct DB access)
- XSS prevention via input sanitization

### 8.4 Rate Limiting

- Per-tenant rate limiting (configurable)
- Per-endpoint rate limiting
- Burst allowance for batch operations

### 8.5 Secrets Management

- No secrets in code or configuration files
- JWT secrets fetched from Secret Manager
- API keys for upstream services stored securely

## 9. Performance Characteristics

### 9.1 Latency Targets

- Health check: < 50ms
- Validation job creation: < 200ms (excluding downstream processing)
- Job status retrieval: < 100ms
- Proxy requests: < 50ms overhead

### 9.2 Throughput Targets

- 1000 requests/second per instance
- Horizontal scaling via load balancer
- Stateless design enables unlimited scaling

### 9.3 Resource Requirements

- CPU: 0.5 cores baseline, 2 cores under load
- Memory: 256MB baseline, 1GB under load
- Network: 100 Mbps sustained

## 10. Monitoring and Observability

### 10.1 Health Checks

- **Liveness**: `GET /health` - Service is running
- **Readiness**: Includes upstream dependency checks
- **Startup**: Initial configuration validation

### 10.2 Metrics

- Request count by endpoint
- Request latency (p50, p95, p99)
- Error rate by status code
- Upstream dependency latency
- Active connections

### 10.3 Logging

- Structured JSON logs
- Correlation ID propagation
- Request/response logging (sanitized)
- Error stack traces
- Performance timing

### 10.4 Tracing

- OpenTelemetry integration
- Distributed tracing across services
- Span tagging with tenant_id, user_id
- Custom instrumentation for key operations

## 11. Deployment Model

### 11.1 Container

- Base image: `python:3.11-slim`
- Multi-stage build for minimal image size
- Non-root user execution
- Health check included in Dockerfile

### 11.2 Kubernetes

- Deployment with 3+ replicas
- HorizontalPodAutoscaler based on CPU/memory
- Service with LoadBalancer type
- ConfigMap for environment variables
- Secret for sensitive configuration

### 11.3 Cloud Run

- Serverless deployment option
- Auto-scaling from 0 to N instances
- Per-request billing
- Regional availability

## 12. Future Enhancements

### 12.1 Planned Features

- GraphQL gateway alongside REST
- WebSocket support for real-time updates
- API versioning strategy (v1, v2, etc.)
- Request batching for improved throughput
- Circuit breaker pattern for upstream failures

### 12.2 Technical Debt

- Migrate from environment variables to Config Service
- Implement comprehensive API rate limiting
- Add request/response caching layer
- Improve error message standardization
- Add OpenAPI spec validation middleware

## 13. Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-08 | Initial FDD creation |

## 14. References

- [OpenAPI Specification](../openapi.yaml)
- [Deployment Guide](./operations/deployment.md)
- [Troubleshooting Guide](./operations/troubleshooting.md)
- [CORTX Platform Architecture](../../../docs/architecture/overview.md)
