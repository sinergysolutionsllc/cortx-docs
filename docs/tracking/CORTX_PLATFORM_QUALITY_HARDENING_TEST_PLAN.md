# Test Plan - CORTX Platform Quality Hardening (Amended)

**Date:** 2025-10-08

## 1. Scope

This Test Plan outlines the testing and documentation activities required to elevate the CORTX platform, its suites, and core repositories to a production-ready state, addressing the gaps identified in the recent QA audit.

## 2. Test Objectives

* ✅ Establish a baseline of **>80% unit test coverage** for all critical repositories (`cortx-platform`, `cortx-sdks`, `cortx-designer`).
* ✅ Verify the **correct integration and functionality of the new navigation system** across all frontend applications.
* ✅ Validate the **end-to-end lifecycle of a WorkflowPack**, from creation in the Designer to execution via a Suite.
* ✅ Ensure all microservices within `cortx-platform` have **robust API integration tests**.
* ✅ Formalize the E2E testing process in the `cortx-e2e` repository with meaningful, real-world scenarios.
* ✅ **(New)** Implement a standardized documentation strategy across all repositories.

## 3. Standardized Documentation Strategy

To ensure clarity, consistency, and ease of maintenance, all repositories must adhere to the following documentation standards.

### 3.1. Platform Documentation

All documentation will be co-located with the code it describes, following this standard directory structure within each repository:

```
docs/
├── README.md                # High-level overview of the repo's docs
├── {REPO_NAME}_FDD.md       # Functional Design Document (The "What" and "Why")
├── architecture/            # ADRs, diagrams (The "How")
│   ├── adr/                 # Architecture Decision Records
│   └── diagrams/            # C4 models, sequence diagrams, etc.
├── operations/              # Runbooks for DevOps (The "Run")
│   ├── deployment.md
│   └── troubleshooting.md
└── testing/                 # Test plans for major features
```

* **`README.md`:** Every repository, service, and module requires a `README.md` following the standard template (Overview, Quick Start, Development, etc.).
* **Org-Level Docs:** The root `/docs` directory remains the single source of truth for cross-cutting concerns like AI Governance, as defined in the standardization plan.

### 3.2. Test Documentation

* **Unit/Integration Tests:** Code should be self-documenting. Use clear, descriptive names for test functions (e.g., `test_create_workflow_fails_if_user_not_authorized`).
* **E2E Tests:** Each E2E test file must include a module-level docstring explaining the user journey it validates.
* **Test Execution Reports:** CI/CD pipelines will be configured to output `pytest` reports and `pytest-cov` coverage reports as build artifacts for every run.

## 4. Testing Layers & Priorities

_(This section remains the same as the previous plan: Unit Tests, Integration Tests, and E2E Tests)_

* **TC-E2E-001: "Golden Path" Workflow Execution**
* **TC-E2E-002: Cross-Domain Navigation & UI Integration**
* **TC-E2E-003: ThinkTank Contextual Awareness**

## 5. Test Environment

_(This section remains the same)_

## 6. Risks & Mitigation

_(This section remains the same)_

## 7. Sign-off Criteria for Production Readiness

* [ ] Unit test coverage for `cortx-platform` and `cortx-sdks` **exceeds 80%**.
* [ ] All high-priority API integration tests for `cortx-platform` services are passing.
* [ ] The three critical E2E scenarios (TC-E2E-001, 002, 003) are **implemented and passing reliably** in the CI/CD pipeline.
* [ ] The new navigation system is **fully integrated and verified** in all frontend applications.
* [ ] **(New)** All repositories conform to the standardized `docs/` structure, and each has a completed FDD.
