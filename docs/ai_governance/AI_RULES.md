# AI Development Rules & Guidelines

**Version:** 1.0.0
**Last Updated:** 2025-10-01
**Owner:** Platform Architecture Team
**Classification:** Internal

---

## Purpose

This document establishes rules, guidelines, and best practices for AI-assisted development within the CORTX Platform ecosystem. These rules ensure consistent, high-quality, secure, and compliant code generation across all Sinergy Solutions repositories.

---

## Core Principles

### 1. Compliance-First Development
- **All AI-generated code MUST align with regulatory requirements** (FedRAMP, HIPAA, NIST 800-53, SOC 2)
- Security controls and audit logging are non-negotiable
- Privacy by design: PII redaction before any LLM processing
- Immutable audit trails for all critical operations

### 2. Code Quality Standards
- **Test coverage:** Maintain >80% unit test coverage for all new code
- **Type safety:** Use strict typing (Python type hints, TypeScript strict mode)
- **Documentation:** All public APIs must have OpenAPI/JSDoc comments
- **Error handling:** Comprehensive error handling with contextual messages

### 3. Security-First Approach
- Never include secrets, API keys, or credentials in code
- All sensitive data must use environment variables or GCP Secret Manager
- Input validation on all user-provided data
- Safe operators only (no eval, exec, or code injection vectors)
- SQL injection prevention: Use parameterized queries exclusively

### 4. Platform Coherence
- Follow established patterns from existing services
- Maintain consistency across microservices architecture
- Respect service boundaries and API contracts
- Use shared libraries and common utilities

---

## AI Agent Roles & Responsibilities

### Tech Lead Architect
**Context:** Cross-repository architecture, platform-wide decisions, API contracts

**Responsibilities:**
- Design service interfaces and inter-service communication patterns
- Define data models and database schemas
- Establish API versioning and backward compatibility strategies
- Review and approve architectural decision records (ADRs)

**Rules:**
- Always consider multi-tenant implications
- Document API contracts in OpenAPI 3.0 format
- Ensure services are independently deployable
- Plan for horizontal scalability from day one

### Backend Services Developer
**Context:** FastAPI services, business logic, data access, integrations

**Responsibilities:**
- Implement RESTful APIs following OpenAPI specifications
- Write database queries with proper indexing
- Implement business logic with comprehensive error handling
- Create unit and integration tests for all endpoints

**Rules:**
- Use FastAPI dependency injection for all shared resources
- Implement request/response validation with Pydantic models
- Add correlation IDs to all log entries
- Include health check and readiness probe endpoints
- Never bypass RBAC checks

### UI/Frontend Developer
**Context:** Next.js applications, React components, Tailwind CSS, user experience

**Responsibilities:**
- Build responsive, accessible user interfaces
- Implement client-side state management
- Integrate with backend APIs using typed clients
- Create reusable component libraries

**Rules:**
- Use TypeScript strict mode exclusively
- Implement proper error boundaries
- Follow WCAG 2.1 AA accessibility standards
- Use React Query for server state management
- Implement proper loading and error states

### GCP Deployment/Ops Engineer
**Context:** Cloud infrastructure, Terraform, CI/CD, monitoring, security

**Responsibilities:**
- Maintain Terraform infrastructure as code
- Configure Cloud Run services with proper resource limits
- Set up monitoring, logging, and alerting
- Manage secrets and service accounts

**Rules:**
- All infrastructure changes must be in Terraform
- Use least privilege principle for IAM roles
- Enable Cloud Armor for DDoS protection
- Configure automatic scaling and health checks
- Implement proper backup and disaster recovery

### Quality Assurance Lead
**Context:** Testing strategy, quality metrics, CI/CD pipeline, test automation

**Responsibilities:**
- Define and maintain test coverage standards
- Create test plans for new features
- Review test quality and effectiveness
- Track and report quality metrics

**Rules:**
- Require tests for all pull requests
- Block merges if coverage drops below 80%
- Maintain separate test fixtures and utilities
- Use pytest for Python, Jest for TypeScript
- Implement contract testing for service boundaries

---

## Code Generation Guidelines

### Python (FastAPI Services)

#### Service Structure
```python
# REQUIRED: Type hints for all functions
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Depends

# REQUIRED: Structured logging with correlation IDs
import structlog
logger = structlog.get_logger()

# REQUIRED: Request/Response models with validation
class RequestModel(BaseModel):
    field: str = Field(..., description="Field description")
    tenant_id: str = Field(..., pattern="^[a-z0-9-]+$")

# REQUIRED: Dependency injection for auth
async def verify_token(token: str = Depends(oauth2_scheme)):
    # Validate JWT, extract claims
    pass

# REQUIRED: Comprehensive error handling
@app.post("/api/v1/resource")
async def create_resource(
    request: RequestModel,
    user=Depends(verify_token)
):
    try:
        logger.info(
            "resource.create.start",
            tenant_id=request.tenant_id,
            user_id=user.id
        )
        # Implementation
        return {"status": "success"}
    except Exception as e:
        logger.error(
            "resource.create.failed",
            error=str(e),
            tenant_id=request.tenant_id
        )
        raise HTTPException(status_code=500, detail="Resource creation failed")
```

#### Database Access
```python
# REQUIRED: Use SQLAlchemy or raw SQL with parameters (never string interpolation)
from sqlalchemy import text

async def get_user(tenant_id: str, user_id: str):
    # CORRECT: Parameterized query
    query = text("""
        SELECT * FROM :tenant_schema.users
        WHERE user_id = :user_id
    """)
    result = await db.execute(
        query,
        {"tenant_schema": tenant_id, "user_id": user_id}
    )

    # WRONG: String interpolation (SQL injection risk)
    # query = f"SELECT * FROM {tenant_id}.users WHERE user_id = '{user_id}'"
```

#### Testing
```python
# REQUIRED: Test structure with fixtures
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_auth():
    # Return mock user context
    pass

def test_create_resource_success(client, mock_auth):
    """Test successful resource creation with valid input."""
    response = client.post(
        "/api/v1/resource",
        json={"field": "value", "tenant_id": "test-tenant"},
        headers={"Authorization": f"Bearer {mock_auth.token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_create_resource_unauthorized(client):
    """Test resource creation fails without authentication."""
    response = client.post("/api/v1/resource", json={})
    assert response.status_code == 401
```

### TypeScript (Next.js, SDKs)

#### Component Structure
```typescript
// REQUIRED: Strict TypeScript
interface ResourceProps {
  resourceId: string;
  tenantId: string;
  onUpdate?: (resource: Resource) => void;
}

// REQUIRED: Error boundaries and loading states
export const ResourceComponent: React.FC<ResourceProps> = ({
  resourceId,
  tenantId,
  onUpdate
}) => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['resource', resourceId],
    queryFn: () => api.getResource(resourceId, tenantId)
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay error={error} />;
  if (!data) return <EmptyState />;

  return (
    <div className="resource-container">
      {/* Implementation */}
    </div>
  );
};
```

#### API Client
```typescript
// REQUIRED: Type-safe API clients
interface CortxApiClient {
  getResource(id: string, tenantId: string): Promise<Resource>;
  createResource(data: CreateResourceRequest): Promise<Resource>;
}

// REQUIRED: Error handling with specific error types
class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public code: string
  ) {
    super(message);
  }
}

export const cortxClient: CortxApiClient = {
  async getResource(id: string, tenantId: string) {
    try {
      const response = await fetch(`/api/v1/resources/${id}`, {
        headers: {
          'X-Tenant-ID': tenantId,
          'Authorization': `Bearer ${getToken()}`
        }
      });

      if (!response.ok) {
        throw new ApiError(
          'Failed to fetch resource',
          response.status,
          'RESOURCE_FETCH_FAILED'
        );
      }

      return await response.json();
    } catch (error) {
      logger.error('API call failed', { id, tenantId, error });
      throw error;
    }
  }
};
```

### RulePack/WorkflowPack Definitions

#### RulePack (JSON)
```json
{
  "metadata": {
    "pack_id": "example-validation-v1",
    "version": "1.0.0",
    "compliance": ["NIST-800-53-AC-3"],
    "created_by": "sinergy-platform",
    "created_at": "2025-10-01T00:00:00Z",
    "description": "Example validation rules for demonstration"
  },
  "rules": [
    {
      "rule_id": "EXAMPLE-001",
      "type": "FATAL",
      "field": "user_id",
      "operator": "matches",
      "pattern": "^[a-z0-9_-]{3,64}$",
      "error_message": "User ID must be 3-64 characters (lowercase alphanumeric, hyphens, underscores)"
    },
    {
      "rule_id": "EXAMPLE-002",
      "type": "WARNING",
      "field": "email",
      "operator": "matches",
      "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
      "error_message": "Email format appears invalid"
    }
  ]
}
```

#### WorkflowPack (YAML)
```yaml
workflow_id: example-workflow-v1
version: 1.0.0
description: Example workflow demonstrating step types

metadata:
  compliance: [SOC2-CC6.1]
  created_by: sinergy-platform
  created_at: "2025-10-01T00:00:00Z"

steps:
  - id: validate_input
    type: validation
    config:
      rulepack: example-validation-v1
      on_failure: halt

  - id: check_eligibility
    type: decision
    config:
      condition: "input.status == 'active'"
      on_true: process_record
      on_false: skip_processing

  - id: process_record
    type: calculation
    config:
      formula: "input.amount * 1.05"
      output_field: "adjusted_amount"

  - id: ai_review
    type: ai-inference
    config:
      model: gemini-1.5-flash
      prompt: "Review this record for anomalies: {{input}}"
      max_tokens: 500

  - id: human_approval
    type: approval
    config:
      role: COMPLIANCE_OFFICER
      timeout_hours: 24

  - id: submit_result
    type: data-sink
    config:
      endpoint: "https://api.example.com/submit"
      method: POST
      headers:
        Content-Type: application/json
```

---

## AI Model Usage Guidelines

### Model Selection

**Gemini 1.5 Flash** (Current Default):
- Use for: Quick responses, simple explanations, routine queries
- Cost: Low
- Latency: 200-500ms
- Context window: 1M tokens

**Gemini 1.5 Pro** (High Complexity):
- Use for: Complex reasoning, multi-step workflows, code generation
- Cost: Medium
- Latency: 500-1500ms
- Context window: 1M tokens

**Claude 3.5 Sonnet** (Planned):
- Use for: Highest quality code generation, complex reasoning
- Cost: High
- Latency: 1000-2000ms
- Context window: 200K tokens

### RAG (Retrieval-Augmented Generation)

**Vector Store Management:**
- Embed compliance documents (Treasury rules, HIPAA guidelines, NIST controls)
- Update embeddings when source documents change
- Use 384-dimensional embeddings (sentence-transformers)
- Threshold: 0.5 cosine similarity minimum

**Knowledge Base Documents:**
- OMB Circular A-136 (Treasury Financial Reporting)
- GTAS Validation Rules (204 rules)
- HIPAA Security Rule (Technical Safeguards)
- NIST 800-53 Rev 5 Control Catalog
- FedRAMP Authorization Boundary Guidance
- CORTX Platform API Documentation
- RulePack/WorkflowPack Schema Definitions

**Retrieval Strategy:**
```python
# Example RAG retrieval
async def get_compliance_context(query: str) -> List[Document]:
    # Generate query embedding
    query_embedding = await embedding_model.embed(query)

    # Search vector store
    results = await vector_store.similarity_search(
        query_embedding,
        k=5,  # Top 5 most relevant
        threshold=0.5  # Minimum similarity
    )

    # Boost results with keyword matches
    for result in results:
        if any(keyword in result.content.lower() for keyword in query.lower().split()):
            result.score *= 1.2

    return sorted(results, key=lambda r: r.score, reverse=True)
```

### PII Protection

**Always redact before LLM calls:**
- Social Security Numbers (SSN): XXX-XX-1234
- Credit Card Numbers: **** **** **** 1234
- Email addresses: u***r@domain.com
- Phone numbers: (***) ***-1234
- IP addresses: ***.***.***.123

**Redaction Implementation:**
```python
import re

PII_PATTERNS = {
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
}

def redact_pii(text: str) -> str:
    """Redact PII before sending to LLM."""
    for pii_type, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f'[REDACTED_{pii_type.upper()}]', text)
    return text
```

---

## Security Requirements

### Authentication & Authorization

**JWT Token Validation:**
```python
from jose import jwt, JWTError

async def verify_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["RS256"],
            audience="cortx-platform",
            issuer="identity-service"
        )

        # Verify required claims
        required_claims = ['sub', 'tenant_id', 'roles', 'exp']
        if not all(claim in payload for claim in required_claims):
            raise JWTError("Missing required claims")

        return payload
    except JWTError as e:
        logger.error("JWT validation failed", error=str(e))
        raise HTTPException(status_code=401, detail="Invalid token")
```

**RBAC Enforcement:**
```python
from enum import Enum

class Permission(Enum):
    EXECUTE_WORKFLOW = "execute:workflows"
    CREATE_PACK = "create:packs"
    VIEW_AUDIT_LOGS = "view:audit_logs"

def require_permission(permission: Permission):
    async def dependency(user=Depends(verify_token)):
        if permission.value not in user.get('permissions', []):
            raise HTTPException(
                status_code=403,
                detail=f"Missing required permission: {permission.value}"
            )
        return user
    return dependency

# Usage
@app.post("/api/v1/workflows/execute")
async def execute_workflow(
    user=Depends(require_permission(Permission.EXECUTE_WORKFLOW))
):
    pass
```

### Input Validation

**Always validate user input:**
```python
from pydantic import BaseModel, Field, validator

class UserInput(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, pattern="^[a-z0-9_-]+$")
    email: str = Field(..., regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    tenant_id: str

    @validator('tenant_id')
    def validate_tenant_id(cls, v):
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Invalid tenant_id format')
        return v

    class Config:
        # Reject unknown fields
        extra = 'forbid'
```

### Secrets Management

**Never hardcode secrets:**
```python
# WRONG
API_KEY = "sk_live_abc123xyz"

# CORRECT: Use environment variables
import os
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

# BETTER: Use GCP Secret Manager
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

API_KEY = get_secret("gemini-api-key")
```

---

## Audit Logging Requirements

### Log All Critical Events

**Required fields in every audit log:**
- `timestamp`: ISO 8601 format
- `event_type`: Descriptive event name (e.g., "workflow_executed")
- `tenant_id`: Multi-tenant isolation
- `user_id`: Actor performing action
- `session_id`: Session correlation
- `correlation_id`: Request tracing
- `status`: success/failure
- `details`: Event-specific metadata
- `compliance_tags`: Applicable frameworks

**Example implementation:**
```python
import structlog
from datetime import datetime

logger = structlog.get_logger()

async def log_audit_event(
    event_type: str,
    tenant_id: str,
    user_id: str,
    session_id: str,
    correlation_id: str,
    status: str,
    details: dict,
    compliance_tags: List[str]
):
    logger.info(
        event_type,
        timestamp=datetime.utcnow().isoformat(),
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
        correlation_id=correlation_id,
        status=status,
        details=details,
        compliance_tags=compliance_tags
    )

    # Also write to compliance service for immutable storage
    await compliance_service.store_audit_log({
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "session_id": session_id,
        "correlation_id": correlation_id,
        "status": status,
        "details": details,
        "compliance_tags": compliance_tags
    })
```

---

## Testing Requirements

### Coverage Targets
- **Unit tests:** >80% line coverage
- **Integration tests:** All service-to-service interactions
- **E2E tests:** Critical user journeys
- **Contract tests:** All API endpoints

### Test Structure

**Python (pytest):**
```python
# tests/unit/test_validation_service.py
import pytest
from app.services.validation import validate_rulepack

class TestValidationService:
    """Unit tests for RulePack validation service."""

    @pytest.fixture
    def sample_rulepack(self):
        return {
            "metadata": {"pack_id": "test-v1", "version": "1.0.0"},
            "rules": [
                {
                    "rule_id": "TEST-001",
                    "type": "FATAL",
                    "field": "amount",
                    "operator": ">",
                    "value": 0,
                    "error_message": "Amount must be positive"
                }
            ]
        }

    @pytest.fixture
    def sample_data(self):
        return {"amount": 100, "currency": "USD"}

    def test_validate_rulepack_success(self, sample_rulepack, sample_data):
        """Test successful validation with valid data."""
        result = validate_rulepack(sample_rulepack, sample_data)
        assert result.is_valid
        assert len(result.violations) == 0

    def test_validate_rulepack_fatal_error(self, sample_rulepack):
        """Test validation fails with FATAL error on negative amount."""
        invalid_data = {"amount": -50, "currency": "USD"}
        result = validate_rulepack(sample_rulepack, invalid_data)
        assert not result.is_valid
        assert len(result.violations) == 1
        assert result.violations[0].severity == "FATAL"
```

**TypeScript (Jest):**
```typescript
// tests/unit/api-client.test.ts
import { cortxClient } from '@/lib/api-client';
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  rest.get('/api/v1/resources/:id', (req, res, ctx) => {
    return res(ctx.json({ id: req.params.id, status: 'active' }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('CortxApiClient', () => {
  it('should fetch resource successfully', async () => {
    const resource = await cortxClient.getResource('test-123', 'tenant-1');
    expect(resource.id).toBe('test-123');
    expect(resource.status).toBe('active');
  });

  it('should throw ApiError on 404', async () => {
    server.use(
      rest.get('/api/v1/resources/:id', (req, res, ctx) => {
        return res(ctx.status(404));
      })
    );

    await expect(
      cortxClient.getResource('missing', 'tenant-1')
    ).rejects.toThrow('Failed to fetch resource');
  });
});
```

---

## Documentation Requirements

### Code Documentation

**Python docstrings (Google style):**
```python
def execute_workflow(
    workflow_id: str,
    tenant_id: str,
    input_data: dict,
    user_context: dict
) -> WorkflowResult:
    """Execute a WorkflowPack with the provided input data.

    Args:
        workflow_id: Unique identifier for the workflow (e.g., "gtas-monthly-v1")
        tenant_id: Tenant identifier for multi-tenant isolation
        input_data: Input data to process through the workflow
        user_context: User authentication and authorization context

    Returns:
        WorkflowResult containing execution status, outputs, and audit trail

    Raises:
        WorkflowNotFoundError: If workflow_id does not exist
        ValidationError: If input_data fails schema validation
        PermissionError: If user lacks execute:workflows permission

    Example:
        >>> result = execute_workflow(
        ...     workflow_id="gtas-monthly-v1",
        ...     tenant_id="agency-dod-001",
        ...     input_data={"records": [...]},
        ...     user_context={"user_id": "jane.doe", "roles": ["SUITE_OPERATOR"]}
        ... )
        >>> print(result.status)
        'completed'
    """
    pass
```

**TypeScript JSDoc:**
```typescript
/**
 * Execute a WorkflowPack with the provided input data.
 *
 * @param workflowId - Unique identifier for the workflow
 * @param tenantId - Tenant identifier for multi-tenant isolation
 * @param inputData - Input data to process through the workflow
 * @returns Promise resolving to WorkflowResult
 * @throws {WorkflowNotFoundError} If workflow_id does not exist
 * @throws {ValidationError} If input_data fails schema validation
 *
 * @example
 * ```typescript
 * const result = await executeWorkflow(
 *   'gtas-monthly-v1',
 *   'agency-dod-001',
 *   { records: [...] }
 * );
 * console.log(result.status); // 'completed'
 * ```
 */
export async function executeWorkflow(
  workflowId: string,
  tenantId: string,
  inputData: unknown
): Promise<WorkflowResult> {
  // Implementation
}
```

### API Documentation

**All endpoints must have OpenAPI specs:**
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="CORTX Validation Service",
    description="RulePack execution and data validation",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

class ExecuteRequest(BaseModel):
    """Request model for RulePack execution."""
    rulepack_id: str = Field(..., description="RulePack identifier")
    data: dict = Field(..., description="Data to validate")

    class Config:
        schema_extra = {
            "example": {
                "rulepack_id": "federal-gtas-v1",
                "data": {"TAS": "012-3456", "amount": 1000.00}
            }
        }

@app.post(
    "/api/v1/validate",
    response_model=ValidationResult,
    summary="Execute RulePack validation",
    description="Validate data against a RulePack and return violations",
    tags=["Validation"]
)
async def execute_rulepack(request: ExecuteRequest):
    """Execute RulePack validation endpoint."""
    pass
```

---

## Performance Guidelines

### Database Queries
- Use connection pooling (min=5, max=20 connections)
- Index all foreign keys and frequently queried columns
- Avoid N+1 queries (use eager loading)
- Batch operations for bulk inserts/updates
- Limit result sets (default max=1000 records)

### Caching Strategy
- Cache frequently accessed configuration (TTL: 5 minutes)
- Cache RulePack/WorkflowPack definitions (TTL: 1 hour, invalidate on update)
- Use Redis for distributed caching
- Implement cache warming for critical paths

### API Rate Limiting
- Default: 100 requests/second per tenant
- Burst: 200 requests/second (10 second window)
- Use Redis for distributed rate limiting
- Return `Retry-After` header on 429 responses

---

## Deployment Checklist

Before deploying AI-generated code:

- [ ] All tests pass (`make test`)
- [ ] Coverage meets threshold (>80%)
- [ ] Linting passes with no errors
- [ ] Security scan passes (no critical vulnerabilities)
- [ ] OpenAPI documentation generated
- [ ] Environment variables documented in `.env.example`
- [ ] Secrets stored in GCP Secret Manager
- [ ] Audit logging implemented for critical operations
- [ ] RBAC checks in place for protected endpoints
- [ ] Database migrations tested (up and down)
- [ ] Performance tested (load testing for high-volume endpoints)
- [ ] Monitoring dashboards updated
- [ ] Runbook updated for ops team

---

## Common Patterns & Anti-Patterns

### Patterns ✅

**Multi-Tenant Isolation:**
```python
# Always scope queries to tenant
async def get_resources(tenant_id: str):
    return await db.execute(
        text(f"SELECT * FROM {tenant_id}.resources")
    )
```

**Correlation IDs:**
```python
import uuid

correlation_id = str(uuid.uuid4())
logger.info("request.start", correlation_id=correlation_id)
# Pass correlation_id through all service calls
```

**Circuit Breaker Pattern:**
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_external_api():
    # External API call
    pass
```

### Anti-Patterns ❌

**Global State:**
```python
# WRONG: Mutable global state
current_user = None

# CORRECT: Dependency injection
def get_current_user(token: str = Depends(oauth2_scheme)):
    pass
```

**Blocking I/O:**
```python
# WRONG: Blocking file read
with open('file.txt') as f:
    data = f.read()

# CORRECT: Async I/O
import aiofiles
async with aiofiles.open('file.txt') as f:
    data = await f.read()
```

**Hardcoded Configuration:**
```python
# WRONG
DATABASE_URL = "postgresql://localhost/cortx"

# CORRECT
DATABASE_URL = os.getenv("DATABASE_URL")
```

---

## Continuous Improvement

### Feedback Loop
- Monitor AI-generated code quality metrics
- Track bugs originating from AI-generated code
- Regularly update prompts based on common issues
- Maintain library of high-quality examples

### Knowledge Base Updates
- Update RAG vector store when:
  - New compliance rules published
  - Platform APIs change
  - New patterns established
  - Security vulnerabilities discovered

### Version Control
- Tag all AI-generated code with agent role
- Include reasoning in commit messages
- Link to relevant ADRs and documentation
- Review AI suggestions before committing

---

## Enforcement

**All pull requests must:**
1. Pass automated CI/CD checks
2. Meet code coverage requirements
3. Include tests for new functionality
4. Pass security scanning
5. Be reviewed by human developer
6. Follow these AI development rules

**Violations will result in:**
- PR rejection
- Required remediation
- Agent prompt refinement
- Documentation updates

---

## Contact & Support

**Questions about these rules?**
- Platform Architecture Team: architecture@sinergysolutions.ai
- Security Officer: security@sinergysolutions.ai
- Slack: #ai-development-guidelines

**Propose changes:**
- Create GitHub issue in `sinergysolutionsllc` org
- Tag with `ai-governance`
- Request review from architecture team

---

**Document Control**
- **Version:** 1.0.0
- **Last Updated:** 2025-10-01
- **Review Cycle:** Quarterly
- **Next Review:** 2026-01-01
- **Approvers:** Platform Architecture Team
