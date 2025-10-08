# CORTX Ownership Matrix

**Date:** 2025-10-08
**Purpose:** Define module ownership and CODEOWNERS for all CORTX repositories
**Status:** Ready for Implementation

---

## Overview

This document defines clear ownership for critical paths across all CORTX repositories, ensuring proper review processes and accountability.

---

## Repository-Level Ownership

| Repository | Primary Owners | Secondary Owners |
|------------|----------------|------------------|
| **cortx-gateway** | @sinergysolutionsllc/platform-team | @sinergysolutionsllc/api-leads |
| **cortx-identity** | @sinergysolutionsllc/security-team | @sinergysolutionsllc/platform-team |
| **cortx-validation** | @sinergysolutionsllc/platform-team | @sinergysolutionsllc/compliance-team |
| **cortx-workflow** | @sinergysolutionsllc/platform-team | @sinergysolutionsllc/business-logic-team |
| **cortx-compliance** | @sinergysolutionsllc/compliance-team | @sinergysolutionsllc/audit-team |
| **cortx-ai-broker** | @sinergysolutionsllc/ai-team | @sinergysolutionsllc/platform-team |
| **cortx-rag** | @sinergysolutionsllc/ai-team | @sinergysolutionsllc/data-team |
| **cortx-ocr** | @sinergysolutionsllc/ai-team | @sinergysolutionsllc/document-team |
| **cortx-ledger** | @sinergysolutionsllc/billing-team | @sinergysolutionsllc/platform-team |
| **cortx-ci** | @sinergysolutionsllc/platform-ops | @sinergysolutionsllc/sre-team |
| **cortx-infra** | @sinergysolutionsllc/platform-ops | @sinergysolutionsllc/security-team |
| **cortx-packs** | @sinergysolutionsllc/compliance-team | @sinergysolutionsllc/business-logic-team |
| **cortx-designer** | @sinergysolutionsllc/ui-team | @sinergysolutionsllc/ai-team |
| **cortx-sdks** | @sinergysolutionsllc/sdk-team | @sinergysolutionsllc/api-leads |
| **cortx-e2e** | @sinergysolutionsllc/qa-team | @sinergysolutionsllc/platform-team |
| **cortx-docs** | @sinergysolutionsllc/docs-team | @sinergysolutionsllc/tech-leads |
| **fedsuite** | @sinergysolutionsllc/fed-team | @sinergysolutionsllc/compliance-team |
| **corpsuite** | @sinergysolutionsllc/corp-team | @sinergysolutionsllc/business-logic-team |
| **medsuite** | @sinergysolutionsllc/med-team | @sinergysolutionsllc/compliance-team |
| **govsuite** | @sinergysolutionsllc/gov-team | @sinergysolutionsllc/platform-team |

---

## Critical Path Ownership

Certain paths require mandatory review from specific teams across all repositories.

### /openapi/** (API Contracts)

**Mandatory Reviewers:**

- @sinergysolutionsllc/api-leads (all changes)
- @sinergysolutionsllc/tech-leads (breaking changes)

**Rationale:** API contracts affect all consumers. Changes must be reviewed for backward compatibility.

**CODEOWNERS Entry:**

```
/openapi/** @sinergysolutionsllc/api-leads
```

### /infra/** (Infrastructure)

**Mandatory Reviewers:**

- @sinergysolutionsllc/platform-ops (all changes)
- @sinergysolutionsllc/security-team (production changes)

**Rationale:** Infrastructure changes affect deployment, security, and availability.

**CODEOWNERS Entry:**

```
/infra/** @sinergysolutionsllc/platform-ops
/infra/helm/** @sinergysolutionsllc/platform-ops @sinergysolutionsllc/security-team
/infra/Dockerfile @sinergysolutionsllc/platform-ops @sinergysolutionsllc/security-team
```

### /policy/** (Security & Compliance Policies)

**Mandatory Reviewers:**

- @sinergysolutionsllc/security-team (all changes)
- @sinergysolutionsllc/compliance-team (compliance-related)

**Rationale:** Policy changes affect compliance posture and security controls.

**CODEOWNERS Entry:**

```
/policy/** @sinergysolutionsllc/security-team @sinergysolutionsllc/compliance-team
```

### /schemas/** (Data Schemas)

**Mandatory Reviewers:**

- @sinergysolutionsllc/api-leads (all changes)
- @sinergysolutionsllc/data-team (data model changes)

**Rationale:** Schema changes affect data validation and interoperability.

**CODEOWNERS Entry:**

```
/schemas/** @sinergysolutionsllc/api-leads @sinergysolutionsllc/data-team
```

### /.github/workflows/** (CI/CD Pipelines)

**Mandatory Reviewers:**

- @sinergysolutionsllc/platform-ops (all changes)
- @sinergysolutionsllc/security-team (secrets/permissions)

**Rationale:** CI/CD changes affect build, test, and deployment processes.

**CODEOWNERS Entry:**

```
/.github/workflows/** @sinergysolutionsllc/platform-ops
```

---

## Service-Specific CODEOWNERS

### cortx-gateway

```
# CORTX Gateway Service Owners
* @sinergysolutionsllc/platform-team

# API contracts
/openapi/** @sinergysolutionsllc/api-leads

# Infrastructure
/infra/** @sinergysolutionsllc/platform-ops

# Routing logic
/app/routers/** @sinergysolutionsllc/api-leads @sinergysolutionsllc/platform-team

# Policy decisions
/app/policy/** @sinergysolutionsllc/security-team @sinergysolutionsllc/compliance-team

# CI/CD
/.github/workflows/** @sinergysolutionsllc/platform-ops
```

### cortx-identity

```
# CORTX Identity Service Owners
* @sinergysolutionsllc/security-team

# API contracts
/openapi/** @sinergysolutionsllc/api-leads @sinergysolutionsllc/security-team

# Infrastructure
/infra/** @sinergysolutionsllc/platform-ops @sinergysolutionsllc/security-team

# Authentication logic
/app/auth/** @sinergysolutionsllc/security-team

# RBAC/ABAC
/app/rbac/** @sinergysolutionsllc/security-team @sinergysolutionsllc/compliance-team

# JWT/tokens
/app/tokens/** @sinergysolutionsllc/security-team

# CI/CD
/.github/workflows/** @sinergysolutionsllc/platform-ops
```

### cortx-validation

```
# CORTX Validation Service Owners
* @sinergysolutionsllc/platform-team

# API contracts
/openapi/** @sinergysolutionsllc/api-leads

# Infrastructure
/infra/** @sinergysolutionsllc/platform-ops

# Rule engine
/app/rules/** @sinergysolutionsllc/business-logic-team @sinergysolutionsllc/compliance-team

# Schemas
/schemas/** @sinergysolutionsllc/api-leads @sinergysolutionsllc/data-team

# CI/CD
/.github/workflows/** @sinergysolutionsllc/platform-ops
```

### cortx-packs

```
# CORTX Packs Repository Owners
* @sinergysolutionsllc/compliance-team

# RulePacks
/rulepacks/** @sinergysolutionsllc/compliance-team @sinergysolutionsllc/business-logic-team

# WorkflowPacks
/workflowpacks/** @sinergysolutionsllc/business-logic-team @sinergysolutionsllc/compliance-team

# Schemas
/schemas/** @sinergysolutionsllc/api-leads @sinergysolutionsllc/data-team

# Test data
/tests/data/** @sinergysolutionsllc/qa-team

# Signing
/signing/** @sinergysolutionsllc/security-team

# CI/CD
/.github/workflows/** @sinergysolutionsllc/platform-ops
```

### cortx-ci

```
# CORTX CI/CD Workflows Owners
* @sinergysolutionsllc/platform-ops

# All workflows require ops review
/.github/workflows/** @sinergysolutionsllc/platform-ops @sinergysolutionsllc/sre-team

# Security-sensitive workflows
/.github/workflows/*deploy* @sinergysolutionsllc/platform-ops @sinergysolutionsllc/security-team
/.github/workflows/*publish* @sinergysolutionsllc/platform-ops @sinergysolutionsllc/security-team
```

### cortx-infra

```
# CORTX Infrastructure Owners
* @sinergysolutionsllc/platform-ops

# Terraform
/terraform/** @sinergysolutionsllc/platform-ops @sinergysolutionsllc/sre-team

# Production environments
/terraform/envs/prod/** @sinergysolutionsllc/platform-ops @sinergysolutionsllc/security-team @sinergysolutionsllc/tech-leads

# Helm charts
/helm/** @sinergysolutionsllc/platform-ops

# Security policies
/policies/** @sinergysolutionsllc/security-team @sinergysolutionsllc/compliance-team

# Network/Cloud Armor
/policies/cloud-armor/** @sinergysolutionsllc/security-team @sinergysolutionsllc/platform-ops

# OPA/Gatekeeper
/policies/opa/** @sinergysolutionsllc/security-team @sinergysolutionsllc/platform-ops
```

---

## Functional Boundaries

### Platform Services (cortx-* services)

**Responsibility:** Core orchestration, execution, and infrastructure
**Owner:** Platform Team
**Scope:**

- Service implementations
- API contracts
- Infrastructure
- CI/CD

**NOT Responsible For:**

- Business rules (belong in cortx-packs)
- Domain-specific UI (belong in suites)
- Client SDKs (belong in cortx-sdks)

### Packs (cortx-packs)

**Responsibility:** Business rules and workflow definitions
**Owner:** Compliance Team + Business Logic Team
**Scope:**

- RulePacks (validation rules)
- WorkflowPacks (process definitions)
- Schemas
- Test data

**NOT Responsible For:**

- Rule execution (cortx-validation handles execution)
- Workflow orchestration (cortx-workflow handles execution)
- UI for rule creation (cortx-designer handles this)

### Designer (cortx-designer)

**Responsibility:** Visual authoring tools for packs
**Owner:** UI Team + AI Team
**Scope:**

- Visual workflow builder
- Pack compilation
- AI assistant
- Pack publishing

**NOT Responsible For:**

- Pack storage (cortx-packs handles this)
- Pack execution (platform services handle this)

### Suites (fedsuite, corpsuite, medsuite, govsuite)

**Responsibility:** Domain-specific applications and UIs
**Owner:** Domain-specific teams
**Scope:**

- Domain modules
- Suite-specific frontends
- Suite-specific workflows

**NOT Responsible For:**

- Platform services (cortx-* services handle this)
- General-purpose rules (cortx-packs handles this)

---

## Separation Verification

### ✅ Business Rules Separated from Platform

**Verification:**

- [x] No RulePack definitions in platform service directories
- [x] All rules in cortx-packs repository
- [x] Platform services only execute rules, don't define them

### ✅ Platform Separated from Suites

**Verification:**

- [x] Platform services are domain-agnostic
- [x] Domain logic in suite repositories
- [x] Platform provides APIs, suites consume them

### ✅ Designer Separated from Execution

**Verification:**

- [x] Designer compiles packs
- [x] Platform services execute packs
- [x] Clear handoff via pack registry

---

## Enforcement

### Branch Protection Requirements

All critical paths require:

1. **PR required** (no direct commits to main)
2. **CODEOWNERS review** (automatic based on paths changed)
3. **CI green** (all checks must pass)
4. **Security scan pass** (Gitleaks, Trivy/Grype)
5. **Coverage threshold** (≥85% for services)

### Production Changes

Additional requirements for production:

1. **Manual approval** from @sinergysolutionsllc/tech-leads
2. **Change log entry** (CHANGELOG.md updated)
3. **Deployment window** (scheduled maintenance window)
4. **Rollback plan** (documented in PR)

---

## Team Definitions (Placeholder)

**Note:** Actual GitHub teams need to be created in organization settings.

Required teams:

- `platform-team`
- `security-team`
- `compliance-team`
- `ai-team`
- `platform-ops`
- `sre-team`
- `api-leads`
- `tech-leads`
- `qa-team`
- `docs-team`
- `ui-team`
- `sdk-team`
- `business-logic-team`
- `data-team`
- `billing-team`
- `audit-team`
- `fed-team`
- `corp-team`
- `med-team`
- `gov-team`

---

**Status:** ✅ Ownership Matrix Complete
**Next:** Service Contracts Definition
