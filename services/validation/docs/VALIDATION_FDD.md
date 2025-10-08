# CORTX Validation Service - Functional Design Document

**Version**: 1.0.0
**Last Updated**: 2025-10-08
**Status**: Active

## 1. Purpose and Scope

### 1.1 Purpose

Provides comprehensive data validation using JSON Schema for structural validation and RulePacks for business logic validation. Supports both static rule-based validation and AI-powered contextual validation.

### 1.2 Scope

- JSON Schema validation
- RulePack execution (Python rules)
- Dual validation modes (static + RAG)
- Validation result comparison and analytics
- Failure explanation and remediation
- Validation caching

## 2. Key Features

### 2.1 JSON Schema Validation

- Structural validation against JSON Schema
- Custom format validators
- Nested object validation
- Array validation with constraints

### 2.2 RulePack Validation

- Python-based business rules
- Domain-specific rule packages
- Configurable severity levels
- Rule chaining and dependencies

### 2.3 Dual Validation Mode

- **Static Mode**: JSON Schema + RulePack only
- **RAG Mode**: AI-powered validation with contextual understanding
- Comparison and agreement analysis
- Confidence scoring

### 2.4 Failure Management

- Detailed failure messages
- Field-level error reporting
- Suggested remediations
- User decision tracking

## 3. API Contracts

### 3.1 Validate Data

```
POST /v1/validate?domain={domain}&mode={static|rag}
Body:
  {
    "data": {...},
    "options": {
      "strict": true,
      "include_warnings": true
    }
  }
Response: 200 OK
  {
    "valid": false,
    "failures": [
      {
        "rule_id": "REQ-001",
        "field": "amount",
        "severity": "error",
        "message": "Amount exceeds limit",
        "expected": "< 1000000",
        "actual": "1500000"
      }
    ],
    "mode": "static",
    "duration_ms": 45
  }
```

### 3.2 Explain Failure

```
POST /v1/explain?failure_id={id}
Response: 200 OK
  {
    "explanation": "AI-generated explanation",
    "policy_refs": ["CFR 1234.56"],
    "remediation_steps": [...]
  }
```

## 4. Dependencies

### 4.1 Upstream

- **RAG Service**: AI validation, explanations
- **Compliance Service**: Audit logging
- **RulePack Registry**: Rule package retrieval

### 4.2 Downstream

- **Gateway**: Validation job orchestration
- **Workflow**: Validation step execution

## 5. Data Models

### 5.1 Validation Request

```python
@dataclass
class ValidationRequest:
    data: dict
    domain: str
    mode: Literal["static", "rag"]
    options: ValidationOptions
```

### 5.2 Validation Result

```python
@dataclass
class ValidationResult:
    valid: bool
    failures: List[ValidationFailure]
    warnings: List[ValidationWarning]
    mode: str
    duration_ms: int
    metadata: dict
```

### 5.3 Validation Failure

```python
@dataclass
class ValidationFailure:
    rule_id: str
    field: Optional[str]
    severity: Literal["error", "warning", "info"]
    message: str
    expected: Optional[Any]
    actual: Optional[Any]
    explanation: Optional[str]
```

## 6. Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CORTX_RAG_URL` | <http://localhost:8138> | RAG service URL |
| `CORTX_COMPLIANCE_URL` | <http://localhost:8135> | Compliance service URL |
| `DEFAULT_VALIDATION_MODE` | static | Default mode if not specified |
| `ENABLE_CACHING` | true | Cache validation results |
| `CACHE_TTL_SECONDS` | 3600 | Cache expiration time |

## 7. Performance Characteristics

### 7.1 Latency Targets

- JSON Schema validation: < 50ms
- RulePack validation: < 200ms
- RAG validation: < 2000ms

### 7.2 Throughput

- 500 validations/second (static mode)
- 100 validations/second (RAG mode)

## 8. Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-08 | Initial FDD creation |
