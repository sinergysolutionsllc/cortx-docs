# CORTX Service Contracts

**Date:** 2025-10-08
**Purpose:** Define service-to-service contracts and dependencies
**Status:** Ready for Implementation

---

## Overview

This document defines the API contracts between CORTX services, including producers, consumers, and OpenAPI specifications.

---

## Service Dependency Graph

```
┌─────────────┐
│   Gateway   │◄─── All external requests
└──────┬──────┘
       │
       ├──────► Identity (auth/authz)
       ├──────► Validation (rule execution)
       ├──────► Workflow (job submission)
       ├──────► AI Broker (LLM requests)
       ├──────► RAG (knowledge retrieval)
       ├──────► OCR (document parsing)
       ├──────► Compliance (audit logging)
       └──────► Ledger (usage tracking)

┌────────────┐
│  Identity  │
└─────┬──────┘
      └──────► (no outgoing dependencies)

┌─────────────┐
│ Validation  │
└──────┬──────┘
       ├──────► Compliance (log validation events)
       └──────► Ledger (track rule executions)

┌───────────┐
│ Workflow  │
└─────┬─────┘
      ├──────► Validation (execute rules in workflow)
      ├──────► AI Broker (AI steps in workflow)
      ├──────► Compliance (workflow audit trail)
      └──────► Ledger (workflow metering)

┌────────────┐
│ AI Broker  │
└─────┬──────┘
      ├──────► RAG (retrieve context for prompts)
      ├──────► Compliance (log AI usage)
      └──────► Ledger (AI cost tracking)

┌─────┐
│ RAG │
└──┬──┘
   ├──────► AI Broker (generate embeddings)
   ├──────► Compliance (index audit trail)
   └──────► Ledger (RAG usage tracking)

┌─────┐
│ OCR │
└──┬──┘
   ├──────► Compliance (document processing audit)
   └──────► Ledger (OCR usage tracking)

┌────────────┐
│ Compliance │
└──────┬─────┘
       └──────► Ledger (compliance event metering)

┌────────┐
│ Ledger │
└────────┘
       └──────► (no outgoing dependencies - append-only)
```

---

## Contract Matrix

| Producer Service | Consumer Service | Contract (OpenAPI Ref) | Criticality | Notes |
|-----------------|------------------|------------------------|-------------|-------|
| **Identity** | Gateway | `/openapi/auth.yaml` | CRITICAL | JWT validation, RBAC checks |
| **Identity** | All Services | `/openapi/auth.yaml` | CRITICAL | Service-to-service auth |
| **Validation** | Gateway | `/openapi/validation.yaml` | HIGH | Rule execution |
| **Validation** | Workflow | `/openapi/validation.yaml` | HIGH | Rules in workflow steps |
| **Workflow** | Gateway | `/openapi/workflow.yaml` | HIGH | Job submission, status |
| **Workflow** | Validation | `/openapi/validation.yaml` | MEDIUM | Execute rules |
| **Workflow** | AI Broker | `/openapi/ai-broker.yaml` | MEDIUM | AI workflow steps |
| **Workflow** | Compliance | `/openapi/compliance.yaml` | HIGH | Workflow audit trail |
| **AI Broker** | Gateway | `/openapi/ai-broker.yaml` | HIGH | LLM routing |
| **AI Broker** | RAG | `/openapi/rag.yaml` | HIGH | Context retrieval |
| **AI Broker** | Compliance | `/openapi/compliance.yaml` | HIGH | AI usage logging |
| **RAG** | Gateway | `/openapi/rag.yaml` | MEDIUM | Knowledge queries |
| **RAG** | AI Broker | `/openapi/ai-broker.yaml` | HIGH | Embedding generation |
| **OCR** | Gateway | `/openapi/ocr.yaml` | MEDIUM | Document parsing |
| **OCR** | Compliance | `/openapi/compliance.yaml` | HIGH | Document audit |
| **Compliance** | All Services | `/openapi/compliance.yaml` | CRITICAL | Audit logging |
| **Ledger** | All Services | `/openapi/ledger.yaml` | HIGH | Usage metering |

---

## Service-by-Service Contracts

### Gateway (cortx-gateway)

**Role:** API Gateway and request router

**Provides:**

- `/v1/gateway/health` - Health check
- `/v1/gateway/route` - Route requests to backend services
- `/v1/gateway/policies` - Policy evaluation
- `/v1/gateway/info` - Service metadata

**Consumes:**
| Service | Endpoint | Purpose |
|---------|----------|---------|
| Identity | `/v1/auth/verify` | Verify JWT tokens |
| Identity | `/v1/auth/check-permission` | RBAC/ABAC checks |
| Validation | `/v1/validation/execute` | Execute rules |
| Workflow | `/v1/workflow/submit` | Submit jobs |
| AI Broker | `/v1/ai/completion` | LLM requests |
| RAG | `/v1/rag/retrieve` | Knowledge retrieval |
| OCR | `/v1/ocr/parse` | Document parsing |
| Compliance | `/v1/compliance/log` | Audit events |
| Ledger | `/v1/ledger/track` | Usage tracking |

**OpenAPI:** `cortx-gateway/openapi/openapi.yaml`

---

### Identity (cortx-identity)

**Role:** Authentication, authorization, and session management

**Provides:**

- `/v1/auth/login` - User login (JWT issue)
- `/v1/auth/logout` - User logout
- `/v1/auth/refresh` - Token refresh
- `/v1/auth/verify` - Token verification
- `/v1/auth/check-permission` - Permission check (RBAC/ABAC)
- `/v1/users/*` - User management
- `/v1/roles/*` - Role management
- `/v1/policies/*` - Access policy management

**Consumes:**

- None (foundational service)

**OpenAPI:** `cortx-identity/openapi/openapi.yaml`

**Security Note:** This is the trust anchor. All other services depend on Identity for auth decisions.

---

### Validation (cortx-validation)

**Role:** Rule engine execution and schema validation

**Provides:**

- `/v1/validation/execute` - Execute rule pack
- `/v1/validation/schema/validate` - JSON schema validation
- `/v1/validation/packs/*` - Rule pack management
- `/v1/validation/results/*` - Validation results

**Consumes:**
| Service | Endpoint | Purpose |
|---------|----------|---------|
| Compliance | `/v1/compliance/log` | Log validation events |
| Ledger | `/v1/ledger/track` | Track rule executions |

**OpenAPI:** `cortx-validation/openapi/openapi.yaml`

---

### Workflow (cortx-workflow)

**Role:** Long-running job orchestration, sagas, compensations

**Provides:**

- `/v1/workflow/submit` - Submit workflow job
- `/v1/workflow/status/{id}` - Job status
- `/v1/workflow/cancel/{id}` - Cancel job
- `/v1/workflow/retry/{id}` - Retry failed job
- `/v1/workflow/packs/*` - Workflow pack management

**Consumes:**
| Service | Endpoint | Purpose |
|---------|----------|---------|
| Validation | `/v1/validation/execute` | Execute rules in workflow |
| AI Broker | `/v1/ai/completion` | AI workflow steps |
| Compliance | `/v1/compliance/log` | Workflow audit trail |
| Ledger | `/v1/ledger/track` | Workflow metering |

**OpenAPI:** `cortx-workflow/openapi/openapi.yaml`

---

### AI Broker (cortx-ai-broker)

**Role:** LLM provider routing, prompt management, safety guardrails

**Provides:**

- `/v1/ai/completion` - Text completion
- `/v1/ai/chat` - Chat completion
- `/v1/ai/embedding` - Generate embeddings
- `/v1/ai/models` - List available models
- `/v1/ai/prompts/*` - Prompt library management

**Consumes:**
| Service | Endpoint | Purpose |
|---------|----------|---------|
| RAG | `/v1/rag/retrieve` | Retrieve context for prompts |
| Compliance | `/v1/compliance/log` | Log AI usage |
| Ledger | `/v1/ledger/track` | AI cost tracking |

**OpenAPI:** `cortx-ai-broker/openapi/openapi.yaml`

**External Dependencies:**

- Vertex AI (GCP)
- OpenAI API (optional)
- Claude API (planned)

---

### RAG (cortx-rag)

**Role:** Retrieval-Augmented Generation - knowledge indexing and retrieval

**Provides:**

- `/v1/rag/index` - Index documents
- `/v1/rag/retrieve` - Retrieve relevant chunks
- `/v1/rag/search` - Semantic search
- `/v1/rag/collections/*` - Manage collections

**Consumes:**
| Service | Endpoint | Purpose |
|---------|----------|---------|
| AI Broker | `/v1/ai/embedding` | Generate embeddings |
| Compliance | `/v1/compliance/log` | Index audit trail |
| Ledger | `/v1/ledger/track` | RAG usage tracking |

**OpenAPI:** `cortx-rag/openapi/openapi.yaml`

**Data Dependencies:**

- PostgreSQL with pgvector extension

---

### OCR (cortx-ocr)

**Role:** Document parsing and field extraction

**Provides:**

- `/v1/ocr/parse` - Parse document (PDF, DOCX, images)
- `/v1/ocr/extract` - Extract fields
- `/v1/ocr/jobs/{id}` - Job status (async processing)

**Consumes:**
| Service | Endpoint | Purpose |
|---------|----------|---------|
| Compliance | `/v1/compliance/log` | Document processing audit |
| Ledger | `/v1/ledger/track` | OCR usage tracking |

**OpenAPI:** `cortx-ocr/openapi/openapi.yaml`

**External Dependencies:**

- Tesseract OCR
- Google Document AI (optional)

---

### Compliance (cortx-compliance)

**Role:** Immutable audit logs, evidence packaging, reporting

**Provides:**

- `/v1/compliance/log` - Log audit event
- `/v1/compliance/query` - Query audit logs
- `/v1/compliance/evidence/{id}` - Get evidence package
- `/v1/compliance/reports/*` - Compliance reports

**Consumes:**
| Service | Endpoint | Purpose |
|---------|----------|---------|
| Ledger | `/v1/ledger/track` | Compliance event metering |

**OpenAPI:** `cortx-compliance/openapi/openapi.yaml`

**Data Characteristics:**

- Append-only (no updates/deletes)
- Immutable audit trail
- Long-term retention

---

### Ledger (cortx-ledger)

**Role:** Usage metering, cost tracking, billing events

**Provides:**

- `/v1/ledger/track` - Track usage event
- `/v1/ledger/query` - Query usage
- `/v1/ledger/summary` - Usage summary
- `/v1/ledger/export` - Export for billing

**Consumes:**

- None (terminal service in dependency graph)

**OpenAPI:** `cortx-ledger/openapi/openapi.yaml`

**Data Characteristics:**

- SHA-256 hash-chained
- Tamper-proof
- Append-only

---

## Authentication & Authorization Flow

### Inter-Service Authentication

All service-to-service calls use **service accounts** with JWT tokens:

```
1. Gateway receives external request with user JWT
2. Gateway verifies JWT with Identity service
3. Gateway calls backend service with:
   - User context (original JWT)
   - Service account token (for service auth)
4. Backend service validates service account token
5. Backend service uses user context for RBAC
```

### Token Types

| Token Type | Issuer | Audience | TTL | Purpose |
|-----------|--------|----------|-----|---------|
| User Access Token | Identity | Gateway | 15 min | User authentication |
| User Refresh Token | Identity | Gateway | 7 days | Token renewal |
| Service Token | Identity | Specific Service | 1 hour | Service-to-service auth |

---

## API Versioning Strategy

### Version Format

All APIs use `/v{major}/` prefix:

- `/v1/` - Current stable
- `/v2/` - Next major version (when needed)

### Breaking Changes

Require major version bump:

- Removing endpoints
- Changing request/response schemas (non-backward compatible)
- Changing authentication requirements
- Changing error codes/formats

### Non-Breaking Changes

Can be added to current version:

- Adding new endpoints
- Adding optional fields to requests
- Adding fields to responses
- Adding new error codes (not changing existing)

---

## Contract Testing

### Consumer-Driven Contracts

**Approach:** Pact-based contract testing

**Process:**

1. Consumer defines expected contract (Pact file)
2. Consumer tests run against mock provider
3. Provider verifies it meets consumer contract
4. Contract published to Pact Broker

**Files:**

- `tests/contract/consumer_*.py` (in consumer repos)
- `tests/contract/provider_*.py` (in provider repos)

### OpenAPI Validation

**Approach:** Schema-based validation

**Process:**

1. Provider publishes OpenAPI spec
2. Consumer generates client from OpenAPI
3. CI validates requests/responses match spec
4. Breaking changes detected automatically

**Tools:**

- openapi-spec-validator
- schemathesis (property-based testing)

---

## Service Discovery

### Development

**Approach:** Direct URLs

```yaml
CORTX_GATEWAY_URL: http://localhost:8080
CORTX_IDENTITY_URL: http://localhost:8082
CORTX_VALIDATION_URL: http://localhost:8083
# ... etc
```

### Production (GKE)

**Approach:** Kubernetes DNS

```yaml
CORTX_GATEWAY_URL: http://cortx-gateway.cortx-platform.svc.cluster.local:8080
CORTX_IDENTITY_URL: http://cortx-identity.cortx-platform.svc.cluster.local:8082
# ... etc
```

### Cloud Run

**Approach:** Service URLs from Terraform outputs

```yaml
CORTX_GATEWAY_URL: https://cortx-gateway-<hash>-uc.a.run.app
CORTX_IDENTITY_URL: https://cortx-identity-<hash>-uc.a.run.app
# ... etc
```

---

## Error Handling

### Standard Error Response

All services use consistent error format:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Rule pack validation failed",
    "details": {
      "rule_id": "gtas-gate-001",
      "field": "transaction.amount",
      "reason": "Amount exceeds threshold"
    },
    "trace_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request (client error) |
| 401 | Unauthorized (authentication failed) |
| 403 | Forbidden (authorization failed) |
| 404 | Not Found |
| 422 | Unprocessable Entity (validation failed) |
| 429 | Too Many Requests (rate limit) |
| 500 | Internal Server Error |
| 503 | Service Unavailable (dependency down) |

---

## Circuit Breakers

### Resilience Strategy

Services implement circuit breakers for downstream dependencies:

**Thresholds:**

- Failure rate: >50% over 10 requests
- Slow call rate: >50% over 200ms threshold
- Circuit open duration: 60 seconds

**Fallback:**

- Return cached response (if available)
- Return degraded response (partial data)
- Fail fast with 503

---

## SLOs (Service Level Objectives)

### Availability

| Service | Target Availability | Acceptable Downtime/month |
|---------|-------------------|---------------------------|
| Gateway | 99.9% | 43.8 minutes |
| Identity | 99.9% | 43.8 minutes |
| All Others | 99.5% | 3.6 hours |

### Latency

| Service | P50 | P95 | P99 |
|---------|-----|-----|-----|
| Gateway | <50ms | <200ms | <500ms |
| Identity | <20ms | <100ms | <200ms |
| Validation | <100ms | <500ms | <1s |
| Workflow | <50ms (submit) | <200ms | <500ms |
| AI Broker | <500ms | <2s | <5s |
| RAG | <200ms | <1s | <2s |
| OCR | <2s | <10s | <30s |
| Compliance | <50ms | <200ms | <500ms |
| Ledger | <20ms | <100ms | <200ms |

---

## Monitoring & Observability

### Trace Propagation

All services propagate trace context via headers:

```
X-Trace-Id: 550e8400-e29b-41d4-a716-446655440000
X-Span-Id: 7a085853-8b1c-4a7e-8c4c-3d9f8e7a6b5c
X-Parent-Span-Id: 6b9e8f7a-5c4d-3e2a-1b0c-9d8e7f6a5b4c
```

### Metrics

Standard metrics for all services:

**Request Metrics:**

- `http_requests_total` (counter)
- `http_request_duration_seconds` (histogram)
- `http_requests_in_flight` (gauge)

**Dependency Metrics:**

- `dependency_requests_total` (counter)
- `dependency_request_duration_seconds` (histogram)
- `dependency_failures_total` (counter)

**Business Metrics:**

- Service-specific (e.g., `rules_executed_total`, `ai_tokens_total`)

---

**Status:** ✅ Service Contracts Complete
**Next:** Phase 2 - Repository Provisioning
