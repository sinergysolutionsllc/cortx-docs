# Suites

## FedSuite (Federal Finance)

- **Modules**: FedReconcile, DataFlow, FedConfig
- **Primary services**: DataFlow Service, Ingestion Service, Workflow, Validation, Compliance Scanner, Ledger
- **Focus**: Treasury GTAS/CARS reconciliation, agency trial-balance normalization, OMB A-136 reporting packs

## CorpSuite (Corporate Compliance)

- **Modules**: PropVerify, Greenlight, InvestmAit
- **Primary services**: Ingestion Service, OCR, AI Broker, Workflow, Ledger, Observability
- **Focus**: Property/title verification, procurement vetting, investment scenario modeling with pack-governed workflows

## MedSuite (Healthcare)

- **Modules**: ClaimsVerify, HIPAAAudit (roadmap: PriorAuthFlow)
- **Primary services**: DataFlow Service for payer data normalization, OCR, Compliance Scanner, AI Broker, Config Service
- **Focus**: Claims anomaly detection, HIPAA control attestation, PHI-aware workflow automation seeded by healthcare RulePacks

## GovSuite (State & Local)

- **Modules**: GrantsFlow (planned), ProcurementGuard (planned)
- **Primary services**: Ingestion adapters for SAM/EVA data, DataFlow Service, Events Service, Observability, Compliance Scanner
- **Focus**: Grants management, vendor risk analytics, municipal compliance packs built atop shared platform services

_All suites leverage centralized OCR, Ledger, RAG, Config, and Packs Registry services to stay contract-aligned with the platform._
