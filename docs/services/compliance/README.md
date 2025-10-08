# Compliance Service (Port 8135)

**Status:** ✅ Implemented | **Version:** 0.1.0

## Overview

The Compliance service (Cortex) provides comprehensive audit logging, compliance reporting, and regulatory framework support for the CORTX platform. It maintains an immutable audit trail and generates compliance reports for FISMA, FedRAMP, HIPAA, and NIST 800-53 controls.

## Core Responsibilities

### Audit Logging

- **Immutable Event Log**: Append-only audit trail
- **Event Collection**: All platform events logged
- **Tamper Detection**: Cryptographic hashing for integrity
- **Event Correlation**: Link related events across services

### Compliance Reporting

- **FISMA Compliance**: Federal Information Security Management Act
- **FedRAMP Reports**: Federal Risk and Authorization Management Program
- **HIPAA Reporting**: Health Insurance Portability and Accountability Act
- **NIST 800-53**: Security and Privacy Controls

### Evidence Collection

- **Control Mapping**: Map events to NIST 800-53 controls
- **Evidence Gathering**: Automated compliance evidence
- **Audit Artifacts**: Generate compliance artifacts
- **Retention Policies**: Enforce data retention requirements

## Architecture Diagram

```mermaid
flowchart TB
    Services[Platform Services] -->|Compliance Events| Compliance[Compliance Service :8135]

    subgraph "Event Processing"
        Compliance -->|1. Validate Event| Validator[Event Validator]
        Validator -->|2. Hash & Store| EventStore[(Event Store)]
        EventStore -->|3. Link Events| Correlator[Event Correlator]
    end

    subgraph "Compliance Reporting"
        Compliance -->|Query Events| Reporter[Report Generator]
        Reporter -->|Map to Controls| ControlMapper[NIST 800-53 Mapper]
        ControlMapper -->|Generate Report| ReportBuilder[Report Builder]
    end

    subgraph "Storage Layer"
        EventStore -->|Persist| Ledger[Ledger Service :8136]
        EventStore -->|Index| DB[(PostgreSQL)]
    end

    ReportBuilder -->|Export| Formats[PDF/CSV/JSON]
```

## API Endpoints

### Health & Status

- `GET /healthz` - Liveness probe
- `GET /readyz` - Readiness probe
- `GET /` - Service metadata

### Event Logging

- `POST /log` - Log compliance event

  ```json
  {
    "event_type": "validation",
    "level": "info",
    "user_id": "user-123",
    "tenant_id": "tenant-456",
    "resource": "document",
    "action": "validated",
    "metadata": {...}
  }
  ```

- `GET /events` - Query audit events
  - Filters: `event_type`, `level`, `user_id`, `tenant_id`, `start_date`, `end_date`

### Compliance Reporting

- `GET /report` - Generate compliance report
  - Formats: `json`, `csv`, `pdf`
  - Frameworks: `fisma`, `fedramp`, `hipaa`, `nist-800-53`

- `GET /controls` - List NIST 800-53 controls
- `GET /controls/{control_id}/evidence` - Get evidence for specific control

### Evidence Management

- `POST /evidence` - Submit compliance evidence
- `GET /evidence/{evidence_id}` - Retrieve evidence artifact
- `GET /retention-policy` - Get data retention policy

## Compliance Event Model

```json
{
  "event_id": "evt-abc123",
  "event_type": "validation",
  "level": "info",
  "timestamp": "2025-10-07T10:00:00Z",
  "user_id": "user-123",
  "tenant_id": "tenant-456",
  "resource": "document",
  "action": "validated",
  "metadata": {
    "validation_result": "passed",
    "rule_pack_id": "rp-001"
  },
  "correlation_id": "req-def456",
  "event_hash": "sha256:..."
}
```

## NIST 800-53 Control Mapping

### Access Control (AC)

- `AC-2`: Account Management → User creation/deletion events
- `AC-3`: Access Enforcement → Authorization decisions
- `AC-6`: Least Privilege → Role assignment events

### Audit and Accountability (AU)

- `AU-2`: Audit Events → All logged events
- `AU-3`: Content of Audit Records → Event metadata
- `AU-9`: Protection of Audit Information → Tamper detection

### Identification and Authentication (IA)

- `IA-2`: User Identification → Login events
- `IA-5`: Authenticator Management → Password changes, MFA

### System and Information Integrity (SI)

- `SI-3`: Malicious Code Protection → Validation failures
- `SI-4`: System Monitoring → Health check events
- `SI-7`: Software Integrity → Code deployment events

## Configuration

### Environment Variables

```bash
# Service
PORT=8135
LOG_LEVEL=INFO

# Ledger Integration
CORTX_LEDGER_URL=http://localhost:8136

# Gateway Integration
CORTX_GATEWAY_URL=http://localhost:8080

# Database
POSTGRES_URL=postgresql://cortx:cortx_dev_password@localhost:5432/cortx

# Retention Policy
AUDIT_RETENTION_DAYS=2555  # 7 years for compliance

# Authentication
REQUIRE_AUTH=false  # Set to "true" for production
```

## Usage Examples

### Log Compliance Event

```bash
curl -X POST http://localhost:8135/log \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "validation",
    "level": "info",
    "user_id": "user-123",
    "tenant_id": "tenant-456",
    "resource": "document",
    "action": "validated",
    "metadata": {
      "validation_result": "passed",
      "rule_pack_id": "rp-001"
    }
  }'
```

### Query Audit Events

```bash
curl "http://localhost:8135/events?tenant_id=tenant-456&event_type=validation&start_date=2025-10-01" \
  -H "Authorization: Bearer <token>"
```

### Generate NIST 800-53 Report

```bash
curl "http://localhost:8135/report?framework=nist-800-53&format=json&start_date=2025-01-01&end_date=2025-10-07" \
  -H "Authorization: Bearer <token>"
```

Response:

```json
{
  "framework": "nist-800-53",
  "report_date": "2025-10-07T10:00:00Z",
  "controls": [
    {
      "control_id": "AC-2",
      "control_name": "Account Management",
      "status": "compliant",
      "evidence_count": 45,
      "last_evidence": "2025-10-06T15:30:00Z"
    },
    {
      "control_id": "AU-2",
      "control_name": "Audit Events",
      "status": "compliant",
      "evidence_count": 1250,
      "last_evidence": "2025-10-07T09:45:00Z"
    }
  ],
  "summary": {
    "total_controls": 75,
    "compliant": 73,
    "partial": 2,
    "non_compliant": 0
  }
}
```

### Get Evidence for Control

```bash
curl "http://localhost:8135/controls/AC-2/evidence?limit=10" \
  -H "Authorization: Bearer <token>"
```

## Security Features

### Immutability

- Append-only event log
- Cryptographic hashing (SHA-256)
- Tamper detection on read
- Write-once storage

### Multi-Tenancy

- Tenant-scoped event queries
- Row-level security
- Cross-tenant isolation

### Retention & Archival

- Automated retention policies
- Long-term archival (7 years)
- Compliance with regulatory requirements

## Performance

### Throughput

- **Event Logging**: ~1000 events/second
- **Query Performance**: <100ms for filtered queries
- **Report Generation**: 2-10s depending on date range

### Scalability

- Horizontal scaling for write throughput
- Read replicas for query performance
- Partitioned storage by date

## Documentation

- **OpenAPI Spec**: [openapi.yaml](./openapi.yaml)
- **Source Code**: `/services/compliance/app/main.py`
- **NIST 800-53**: [NIST SP 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)

## Support

For issues or questions:

- GitHub Issues: [sinergysolutionsllc/sinergysolutionsllc](https://github.com/sinergysolutionsllc/sinergysolutionsllc/issues)
- Internal Documentation: `/docs/services/compliance/`
