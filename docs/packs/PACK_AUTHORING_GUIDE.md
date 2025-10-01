# Pack Authoring Guide

**Version:** 1.0.0
**Last Updated:** 2025-10-01
**Owner:** Platform Architecture Team
**Audience:** Pack Authors, Compliance Officers, Developers
**Classification:** Public

---

## Introduction

Welcome to the CORTX Pack Authoring Guide! This document provides comprehensive instructions for creating, testing, and deploying **RulePacks** and **WorkflowPacks** - the core building blocks of compliance automation in the CORTX Platform.

### What are Packs?

**RulePacks** are JSON-based validation rule sets that define compliance policies, business rules, and data quality checks. They execute safely without code injection risks using a declarative rule syntax.

**WorkflowPacks** are YAML-based process orchestration definitions that combine multiple steps (validation, calculations, AI inference, approvals, integrations) into automated workflows.

### Why Use Packs?

- **Version Control:** Packs are stored in Git, providing full audit history
- **Reusability:** Create once, use across multiple tenants and suites
- **Compliance:** Built-in regulatory framework tagging and documentation
- **Marketplace:** Share and monetize packs in the CORTX Marketplace
- **Safety:** Declarative syntax prevents code injection attacks

---

## Prerequisites

### Required Tools

- **Git:** Version control for pack repositories
- **Text Editor:** VS Code (recommended), Sublime, or similar
- **YAML/JSON Validator:** `check-jsonschema` or IDE plugins
- **CORTX CLI:** (Optional) For pack testing and deployment

### Required Knowledge

- Basic understanding of JSON and YAML syntax
- Familiarity with the compliance domain (HIPAA, FedRAMP, etc.)
- Understanding of the CORTX Platform architecture

### Access Requirements

- **GitHub Access:** Write access to `cortx-packs` repository
- **CORTX Platform:** Account with `PACK_AUTHOR` role
- **Development Environment:** Access to dev/staging environments

---

## Part 1: Creating RulePacks

### RulePack Structure

A RulePack consists of two main sections:

1. **Metadata:** Information about the pack (ID, version, compliance tags)
2. **Rules:** Array of validation rules to execute

**Minimal Example:**
```json
{
  "metadata": {
    "pack_id": "example-validation-v1",
    "version": "1.0.0",
    "compliance": ["NIST-800-53-AC-3"],
    "created_by": "jane.doe@agency.gov",
    "created_at": "2025-10-01T00:00:00Z",
    "description": "Example validation rules for user account data"
  },
  "rules": [
    {
      "rule_id": "USER-001",
      "type": "FATAL",
      "field": "username",
      "operator": "matches",
      "pattern": "^[a-z0-9_-]{3,64}$",
      "error_message": "Username must be 3-64 characters (lowercase, numbers, hyphens, underscores only)"
    }
  ]
}
```

### Metadata Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `pack_id` | Yes | string | Unique identifier (kebab-case, e.g., `federal-gtas-v1`) |
| `version` | Yes | string | Semantic version (e.g., `1.0.0`) |
| `compliance` | No | array | Regulatory frameworks (e.g., `["FedRAMP", "HIPAA"]`) |
| `created_by` | Yes | string | Author email or identifier |
| `created_at` | Yes | string | ISO 8601 timestamp |
| `description` | Yes | string | Human-readable description of the pack |
| `tags` | No | array | Searchable tags for marketplace discovery |
| `license` | No | string | License (default: `MIT`) |

### Rule Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `rule_id` | Yes | string | Unique rule identifier (e.g., `GTAS-001`) |
| `type` | Yes | enum | Severity: `FATAL`, `WARNING`, or `INFO` |
| `field` | Yes | string | Data field to validate (dot notation supported) |
| `operator` | Yes | enum | Comparison operator (see operators below) |
| `value` | Conditional | any | Expected value (required for most operators) |
| `pattern` | Conditional | string | Regex pattern (for `matches` operator) |
| `error_message` | Yes | string | User-friendly error message |
| `compliance_ref` | No | string | Regulatory reference (e.g., `NIST-800-53-AC-2`) |
| `remediation` | No | string | How to fix the error |

### Supported Operators

#### Comparison Operators
- `==`: Equal to
- `!=`: Not equal to
- `<`: Less than
- `<=`: Less than or equal to
- `>`: Greater than
- `>=`: Greater than or equal to

**Example:**
```json
{
  "rule_id": "AMOUNT-001",
  "type": "FATAL",
  "field": "transaction_amount",
  "operator": ">",
  "value": 0,
  "error_message": "Transaction amount must be positive"
}
```

#### Membership Operators
- `in`: Value is in list
- `not_in`: Value is not in list

**Example:**
```json
{
  "rule_id": "STATUS-001",
  "type": "FATAL",
  "field": "account_status",
  "operator": "in",
  "value": ["active", "pending", "suspended"],
  "error_message": "Account status must be active, pending, or suspended"
}
```

#### String Operators
- `contains`: String contains substring
- `starts_with`: String starts with prefix
- `ends_with`: String ends with suffix
- `matches`: String matches regex pattern

**Example:**
```json
{
  "rule_id": "EMAIL-001",
  "type": "FATAL",
  "field": "email",
  "operator": "matches",
  "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
  "error_message": "Invalid email format"
}
```

#### Null Check Operators
- `is_null`: Field is null or undefined
- `is_not_null`: Field has a value

**Example:**
```json
{
  "rule_id": "REQUIRED-001",
  "type": "FATAL",
  "field": "taxpayer_id",
  "operator": "is_not_null",
  "error_message": "Taxpayer ID is required"
}
```

### Nested Field Access

Use dot notation to access nested fields:

```json
{
  "rule_id": "NESTED-001",
  "type": "FATAL",
  "field": "address.zip_code",
  "operator": "matches",
  "pattern": "^\\d{5}(-\\d{4})?$",
  "error_message": "ZIP code must be 5 digits or 5+4 format"
}
```

### Array Field Access

Use bracket notation for array elements:

```json
{
  "rule_id": "ARRAY-001",
  "type": "WARNING",
  "field": "items[0].price",
  "operator": ">",
  "value": 0,
  "error_message": "First item must have positive price"
}
```

### Severity Levels

**FATAL:**
- **Blocks processing:** Data cannot proceed
- **Use for:** Critical compliance violations, data corruption risks
- **Example:** Missing required fields, invalid formats

**WARNING:**
- **Allows processing:** Data proceeds with warnings
- **Use for:** Quality issues, potential problems
- **Example:** Missing optional fields, unusual values

**INFO:**
- **Informational only:** No impact on processing
- **Use for:** Audit trails, recommendations
- **Example:** Data quality metrics, optimization suggestions

### Example: GTAS Trial Balance RulePack

```json
{
  "metadata": {
    "pack_id": "federal-gtas-trial-balance-v1",
    "version": "1.0.0",
    "compliance": ["OMB-A-136", "GTAS-2024"],
    "created_by": "treasury-validation-team",
    "created_at": "2025-09-30T00:00:00Z",
    "description": "Treasury GTAS trial balance validation rules for FY 2024",
    "tags": ["federal", "treasury", "gtas", "trial-balance"]
  },
  "rules": [
    {
      "rule_id": "GTAS-001",
      "type": "FATAL",
      "field": "TAS",
      "operator": "matches",
      "pattern": "^[0-9]{3}-[0-9]{4}$",
      "error_message": "TAS must be in format ###-#### (e.g., 012-3456)",
      "compliance_ref": "GTAS Validation Rule #1",
      "remediation": "Verify TAS with Treasury Account Symbol Directory"
    },
    {
      "rule_id": "GTAS-002",
      "type": "FATAL",
      "field": "USSGL_account",
      "operator": "matches",
      "pattern": "^[0-9]{6}$",
      "error_message": "USSGL account must be 6 digits",
      "compliance_ref": "GTAS Validation Rule #2",
      "remediation": "Use valid USSGL account from FY 2024 USSGL Crosswalk"
    },
    {
      "rule_id": "GTAS-003",
      "type": "FATAL",
      "field": "debit_credit_indicator",
      "operator": "in",
      "value": ["D", "C"],
      "error_message": "Debit/Credit indicator must be 'D' or 'C'",
      "compliance_ref": "GTAS Validation Rule #3"
    },
    {
      "rule_id": "GTAS-004",
      "type": "FATAL",
      "field": "amount",
      "operator": "is_not_null",
      "error_message": "Amount is required",
      "compliance_ref": "GTAS Validation Rule #4"
    },
    {
      "rule_id": "GTAS-005",
      "type": "WARNING",
      "field": "amount",
      "operator": ">=",
      "value": 0.01,
      "error_message": "Amount should be at least $0.01 (possible data quality issue)",
      "compliance_ref": "GTAS Best Practice"
    },
    {
      "rule_id": "GTAS-006",
      "type": "FATAL",
      "field": "fiscal_year",
      "operator": "==",
      "value": 2024,
      "error_message": "Fiscal year must be 2024 for this submission",
      "compliance_ref": "GTAS Validation Rule #6"
    }
  ]
}
```

---

## Part 2: Creating WorkflowPacks

### WorkflowPack Structure

A WorkflowPack consists of:

1. **Workflow Metadata:** ID, version, description
2. **Steps:** Ordered array of workflow steps
3. **Configurations:** Step-specific settings

**Minimal Example:**
```yaml
workflow_id: example-workflow-v1
version: 1.0.0
description: Simple workflow demonstrating basic steps

metadata:
  compliance: [SOC2-CC6.1]
  created_by: jane.doe@agency.gov
  created_at: "2025-10-01T00:00:00Z"

steps:
  - id: validate_data
    type: validation
    config:
      rulepack: example-validation-v1
      on_failure: halt

  - id: send_notification
    type: data-sink
    config:
      endpoint: https://api.example.com/notify
      method: POST
```

### Workflow Metadata

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `workflow_id` | Yes | string | Unique workflow identifier |
| `version` | Yes | string | Semantic version |
| `description` | Yes | string | Workflow description |
| `metadata.compliance` | No | array | Compliance frameworks |
| `metadata.created_by` | Yes | string | Author identifier |
| `metadata.created_at` | Yes | string | ISO 8601 timestamp |
| `metadata.tags` | No | array | Searchable tags |

### Step Types

#### 1. Data Source (`data-source`)
**Purpose:** Ingest data from external sources

**Config:**
```yaml
- id: ingest_csv
  type: data-source
  config:
    format: csv  # csv, json, xml, api
    source: s3://bucket/data.csv
    schema: trial-balance-v1
```

#### 2. Validation (`validation`)
**Purpose:** Execute RulePack validation

**Config:**
```yaml
- id: validate_rules
  type: validation
  config:
    rulepack: federal-gtas-v1
    on_failure: halt  # halt, continue, retry
    max_retries: 3
```

#### 3. Calculation (`calculation`)
**Purpose:** Perform data transformations and calculations

**Config:**
```yaml
- id: calculate_total
  type: calculation
  config:
    formula: sum(input.debits) - sum(input.credits)
    output_field: net_balance
```

#### 4. Decision (`decision`)
**Purpose:** Conditional branching

**Config:**
```yaml
- id: check_threshold
  type: decision
  config:
    condition: input.amount > 10000
    on_true: escalate_approval
    on_false: auto_approve
```

#### 5. Approval (`approval`)
**Purpose:** Human-in-the-loop review

**Config:**
```yaml
- id: manager_approval
  type: approval
  config:
    role: COMPLIANCE_OFFICER
    timeout_hours: 24
    auto_approve_on_timeout: false
```

#### 6. AI Inference (`ai-inference`)
**Purpose:** LLM-powered analysis and recommendations

**Config:**
```yaml
- id: anomaly_detection
  type: ai-inference
  config:
    model: gemini-1.5-flash
    prompt: "Analyze this transaction for anomalies: {{input}}"
    max_tokens: 500
    temperature: 0.0
```

#### 7. Data Sink (`data-sink`)
**Purpose:** Output results to external systems

**Config:**
```yaml
- id: submit_gtas
  type: data-sink
  config:
    endpoint: https://gtas.treasury.gov/api/submit
    method: POST
    headers:
      Content-Type: application/json
      Authorization: Bearer {{env.GTAS_API_KEY}}
```

### Example: GTAS Monthly Submission Workflow

```yaml
workflow_id: gtas-monthly-submission-v1
version: 1.0.0
description: Monthly GTAS trial balance submission workflow for federal agencies

metadata:
  compliance: [OMB-A-136, GTAS-2024, FISMA]
  created_by: treasury-workflow-team
  created_at: "2025-09-30T00:00:00Z"
  tags: [federal, treasury, gtas, monthly-reporting]

steps:
  # Step 1: Ingest trial balance data
  - id: ingest_trial_balance
    type: data-source
    config:
      format: csv
      source: s3://agency-financial-data/trial-balance.csv
      schema: gtas-trial-balance-v1

  # Step 2: Validate GTAS rules
  - id: validate_gtas_rules
    type: validation
    config:
      rulepack: federal-gtas-trial-balance-v1
      on_failure: halt
      max_retries: 0

  # Step 3: Calculate net balance
  - id: calculate_net_balance
    type: calculation
    config:
      formula: sum(debits) - sum(credits)
      output_field: net_balance

  # Step 4: Check if balance is zero
  - id: check_balance
    type: decision
    config:
      condition: abs(net_balance) < 0.01
      on_true: ai_review
      on_false: flag_unbalanced

  # Step 5: AI review for unusual patterns
  - id: ai_review
    type: ai-inference
    config:
      model: gemini-1.5-flash
      prompt: |
        Review this GTAS trial balance submission for unusual patterns or anomalies.
        Data: {{input}}

        Flag any:
        - Unusually large amounts
        - Unexpected USSGL account usage
        - Missing TAS components
      max_tokens: 1000
      temperature: 0.0

  # Step 6: Certifying official approval
  - id: certifying_official_approval
    type: approval
    config:
      role: CERTIFYING_OFFICIAL
      timeout_hours: 48
      auto_approve_on_timeout: false
      notification:
        email: certifying.official@agency.gov
        subject: GTAS Submission Approval Required

  # Step 7: Submit to GTAS
  - id: submit_to_gtas
    type: data-sink
    config:
      endpoint: https://gtas.treasury.gov/api/v2/submit
      method: POST
      headers:
        Content-Type: application/json
        Authorization: Bearer {{env.GTAS_API_KEY}}
      payload:
        agency_code: "{{input.agency_code}}"
        fiscal_year: 2024
        fiscal_period: "{{input.fiscal_period}}"
        data: "{{input.validated_data}}"

  # Step 8: Archive submission
  - id: archive_submission
    type: data-sink
    config:
      endpoint: s3://agency-gtas-archive/{{fiscal_year}}/{{fiscal_period}}/
      format: json
      retention_days: 2555  # 7 years
```

### Step Dependencies

Steps execute in order by default. Use `depends_on` for explicit dependencies:

```yaml
steps:
  - id: step1
    type: validation
    config:
      rulepack: pack-v1

  - id: step2a
    type: calculation
    depends_on: [step1]
    config:
      formula: input.amount * 1.05

  - id: step2b
    type: ai-inference
    depends_on: [step1]
    config:
      model: gemini-1.5-flash
      prompt: "Analyze {{input}}"

  # step2a and step2b run in parallel after step1
```

### Error Handling

Define error handling strategies per step:

```yaml
- id: external_api_call
  type: data-sink
  config:
    endpoint: https://api.example.com
    method: POST
  error_handling:
    on_failure: retry
    max_retries: 3
    retry_delay_seconds: 5
    backoff_multiplier: 2  # Exponential backoff
    fallback_step: log_failure
```

### Compensation (Saga Pattern)

For distributed transactions, define compensation logic:

```yaml
workflow_id: distributed-transaction-v1
version: 1.0.0

saga:
  enabled: true
  compensation_order: reverse  # Rollback in reverse order

steps:
  - id: reserve_funds
    type: data-sink
    config:
      endpoint: https://api.bank.com/reserve
    compensate:
      endpoint: https://api.bank.com/release
      method: POST

  - id: create_order
    type: data-sink
    config:
      endpoint: https://api.orders.com/create
    compensate:
      endpoint: https://api.orders.com/cancel
      method: DELETE

on_failure:
  - execute_compensations: true
  - notify: failure_alert
```

---

## Part 3: Testing Packs

### Local Testing

#### RulePack Testing

**Test Data Structure:**
```json
{
  "rulepack_id": "federal-gtas-v1",
  "test_cases": [
    {
      "name": "Valid TAS format",
      "input": {
        "TAS": "012-3456",
        "USSGL_account": "101000",
        "debit_credit_indicator": "D",
        "amount": 1000.00,
        "fiscal_year": 2024
      },
      "expected": {
        "is_valid": true,
        "violations": []
      }
    },
    {
      "name": "Invalid TAS format",
      "input": {
        "TAS": "12-3456",
        "USSGL_account": "101000",
        "debit_credit_indicator": "D",
        "amount": 1000.00,
        "fiscal_year": 2024
      },
      "expected": {
        "is_valid": false,
        "violations": [
          {
            "rule_id": "GTAS-001",
            "field": "TAS",
            "severity": "FATAL"
          }
        ]
      }
    }
  ]
}
```

**Run Tests:**
```bash
# Using CORTX CLI
cortx pack test rulepack ./federal-gtas-v1.json --test-data ./test-cases.json

# Using Python
python -m cortx.validation.test --rulepack federal-gtas-v1.json --data test-cases.json
```

#### WorkflowPack Testing

**Simulation Mode:**
```bash
# Simulate workflow execution without external calls
cortx pack test workflow ./gtas-workflow.yaml --simulate --input ./sample-data.json

# Execute in dev environment
cortx pack test workflow ./gtas-workflow.yaml --env dev --input ./sample-data.json
```

### Automated Testing (CI/CD)

**GitHub Actions Workflow:**
```yaml
name: Test RulePacks

on:
  pull_request:
    paths:
      - 'rulepacks/**/*.json'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Validate JSON Schema
        run: |
          pip install check-jsonschema
          check-jsonschema --schemafile schemas/rulepack-schema.json rulepacks/**/*.json

      - name: Run RulePack Tests
        run: |
          python -m pytest tests/rulepacks/ --cov=rulepacks --cov-report=xml

      - name: Upload Coverage
        uses: codecov/codecov-action@v3
```

### Performance Testing

**Load Test Example:**
```python
import asyncio
from cortx.validation import execute_rulepack

async def load_test():
    """Test RulePack with 1M records."""
    rulepack = load_json("federal-gtas-v1.json")

    # Generate 1M test records
    records = [generate_test_record() for _ in range(1_000_000)]

    start = time.time()
    results = await execute_rulepack(rulepack, records)
    duration = time.time() - start

    print(f"Processed 1M records in {duration:.2f}s")
    assert duration < 30, "Performance target: <30s for 1M records"

asyncio.run(load_test())
```

---

## Part 4: Versioning & Deployment

### Semantic Versioning

Follow semantic versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR:** Breaking changes (requires re-certification)
- **MINOR:** Backward-compatible features (new rules, optional fields)
- **PATCH:** Bug fixes (error message updates, typos)

**Examples:**
- `1.0.0` → `1.0.1`: Fixed typo in error message
- `1.0.1` → `1.1.0`: Added 5 new validation rules
- `1.1.0` → `2.0.0`: Changed rule operator (breaking change)

### Changelog

Maintain a changelog for each pack:

```markdown
# Changelog: federal-gtas-v1

## [1.2.0] - 2025-10-15
### Added
- GTAS-007: Validate fiscal period range (1-12)
- GTAS-008: Check for duplicate TAS entries

### Changed
- GTAS-005: Updated warning threshold to $0.10

## [1.1.0] - 2025-09-30
### Added
- GTAS-006: Fiscal year validation

## [1.0.0] - 2025-09-01
### Added
- Initial release with 5 core validation rules
```

### Deployment Process

**1. Development:**
```bash
# Create feature branch
git checkout -b feature/add-gtas-rule-007

# Edit pack
vim rulepacks/federal/gtas/federal-gtas-v1.json

# Test locally
cortx pack test rulepack ./federal-gtas-v1.json

# Commit changes
git add rulepacks/federal/gtas/federal-gtas-v1.json
git commit -m "feat(gtas): add fiscal period validation (GTAS-007)"
```

**2. Pull Request:**
```bash
# Push to GitHub
git push origin feature/add-gtas-rule-007

# Create PR with description:
# - What changed
# - Why (compliance requirement, bug fix, etc.)
# - Test results
# - Breaking changes (if any)
```

**3. Review & Approval:**
- **Automated Checks:** Schema validation, unit tests
- **Human Review:** Business analyst reviews functional correctness
- **Compliance Review:** Compliance officer certifies regulatory alignment
- **Merge:** Approved PRs merged to `main`

**4. Deployment:**
```bash
# Tag release
git tag -a v1.2.0 -m "Release v1.2.0: Add fiscal period validation"
git push origin v1.2.0

# Deploy to staging
cortx pack deploy federal-gtas-v1 --env staging --version 1.2.0

# Smoke test in staging
cortx pack test workflow gtas-monthly-submission-v1 --env staging

# Deploy to production
cortx pack deploy federal-gtas-v1 --env prod --version 1.2.0
```

---

## Part 5: Best Practices

### RulePack Best Practices

**1. Use Descriptive Rule IDs:**
```json
// Good
"rule_id": "GTAS-TAS-FORMAT-001"

// Bad
"rule_id": "RULE1"
```

**2. Provide Actionable Error Messages:**
```json
// Good
"error_message": "TAS must be in format ###-#### (e.g., 012-3456). Found: {{value}}"

// Bad
"error_message": "Invalid TAS"
```

**3. Tag Compliance References:**
```json
{
  "rule_id": "HIPAA-ACCESS-001",
  "compliance_ref": "HIPAA Security Rule §164.312(a)(1)",
  "remediation": "Implement unique user identification per §164.312(a)(2)(i)"
}
```

**4. Use Appropriate Severity:**
- **FATAL:** Missing required fields, data corruption risks
- **WARNING:** Quality issues, potential problems
- **INFO:** Audit trails, optimization suggestions

**5. Order Rules by Dependency:**
```json
{
  "rules": [
    // First: Check required fields exist
    {"rule_id": "REQ-001", "field": "amount", "operator": "is_not_null"},

    // Then: Validate field values
    {"rule_id": "VAL-001", "field": "amount", "operator": ">", "value": 0}
  ]
}
```

### WorkflowPack Best Practices

**1. Use Meaningful Step IDs:**
```yaml
# Good
- id: validate_hipaa_compliance
- id: certifying_official_approval
- id: submit_to_gtas

# Bad
- id: step1
- id: step2
```

**2. Handle Errors Gracefully:**
```yaml
- id: external_api_call
  type: data-sink
  config:
    endpoint: https://api.example.com
  error_handling:
    on_failure: retry
    max_retries: 3
    fallback_step: log_error_and_notify
```

**3. Use Environment Variables for Secrets:**
```yaml
config:
  headers:
    Authorization: Bearer {{env.API_KEY}}  # Good
    # Authorization: Bearer sk_live_abc123  # NEVER hardcode secrets
```

**4. Document Complex Workflows:**
```yaml
workflow_id: complex-reconciliation-v1
version: 1.0.0
description: |
  Multi-step reconciliation workflow with the following stages:
  1. Ingest trial balance from agency system
  2. Validate against 204 GTAS rules
  3. Perform 3-way reconciliation (GL, sub-ledger, GTAS)
  4. AI-powered anomaly detection
  5. Certifying official approval
  6. Submit to Treasury GTAS system
  7. Archive for 7-year retention
```

**5. Test with Realistic Data:**
- Use production-like data volumes
- Include edge cases (empty fields, special characters, etc.)
- Test error scenarios (network failures, timeouts, etc.)

---

## Part 6: Marketplace Submission

### Preparing for Marketplace

**1. Complete Metadata:**
```json
{
  "metadata": {
    "pack_id": "healthcare-hipaa-audit-v1",
    "version": "1.0.0",
    "compliance": ["HIPAA-Security-Rule", "HIPAA-Privacy-Rule"],
    "created_by": "healthcare-compliance-experts",
    "created_at": "2025-10-01T00:00:00Z",
    "description": "Comprehensive HIPAA compliance audit RulePack with 48 security controls",
    "tags": ["healthcare", "hipaa", "audit", "security", "privacy"],
    "license": "MIT",
    "documentation_url": "https://docs.example.com/packs/hipaa-audit",
    "support_email": "support@example.com",
    "marketplace": {
      "category": "Compliance",
      "pricing": "free",  // or "paid"
      "certification_tier": "certified"  // official, certified, community
    }
  }
}
```

**2. Create Documentation:**
- **README.md:** Overview, use cases, installation
- **USAGE.md:** Step-by-step guide with examples
- **TESTING.md:** How to test the pack
- **CHANGELOG.md:** Version history

**3. Add Examples:**
```
packs/healthcare/hipaa-audit/
├── pack.json
├── README.md
├── USAGE.md
├── CHANGELOG.md
├── examples/
│   ├── sample-input.json
│   ├── sample-output.json
│   └── test-cases.json
└── tests/
    └── test_hipaa_audit.py
```

**4. Submit for Certification:**
```bash
# Submit to marketplace
cortx marketplace submit healthcare-hipaa-audit-v1 \
  --tier certified \
  --category compliance \
  --pricing free

# Certification process:
# 1. Automated testing (schema, tests, security scan)
# 2. Compliance review (regulatory alignment)
# 3. Quality review (code quality, documentation)
# 4. Approval (marketplace team)
```

**5. Monitor Usage:**
- Track downloads and ratings
- Respond to user feedback
- Release updates based on user needs

---

## Resources
> Note: Use **relative links** for all internal docs to satisfy MkDocs strict validation.

### Documentation
- [RulePack Schema Reference](./RULEPACK_SCHEMA.md)
- [WorkflowPack Schema Reference](./WORKFLOWPACK_SCHEMA.md)
- [Pack Governance](./PACK_GOVERNANCE.md)
- [Marketplace Vision](../marketplace/MARKETPLACE_VISION.md)

### Tools
- **CORTX CLI:** `npm install -g @cortx/cli`
- **Schema Validator:** `pip install check-jsonschema`
- **VS Code Extension:** CORTX Pack Authoring (coming soon)

### Support
- **Slack:** #pack-authoring
- **Email:** pack-support@sinergysolutions.ai
- **Office Hours:** Wednesdays 2-3 PM ET

---

## Appendix: Complete Example

See the `cortx-packs` repository for complete examples:
- `/rulepacks/federal/gtas/federal-gtas-v1.json` (204 rules)
- `/workflowpacks/federal/gtas-submission/gtas-monthly-v1.yaml`
- `/rulepacks/healthcare/hipaa/hipaa-security-v1.json` (48 rules)

---

**Document Control**
- **Version:** 1.0.0
- **Last Updated:** 2025-10-01
- **Review Cycle:** Quarterly
- **Next Review:** 2026-01-01
- **Approvers:** Platform Architecture Team
