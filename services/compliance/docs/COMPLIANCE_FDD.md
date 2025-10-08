# CORTX Compliance Service - Functional Design Document

**Version**: 1.0.0
**Last Updated**: 2025-10-08
**Status**: Active

## 1. Purpose and Scope

### 1.1 Purpose

Provides comprehensive audit logging, compliance reporting, and regulatory tracking for all CORTX platform operations to ensure accountability, traceability, and regulatory compliance.

### 1.2 Scope

- Audit event logging
- Compliance report generation
- User decision tracking
- Policy enforcement verification
- Regulatory requirement mapping
- Evidence collection
- Compliance dashboard data

### 1.3 Out of Scope

- Policy authoring (handled by RulePack system)
- Real-time alerting (handled by monitoring)
- Data retention management (handled by infrastructure)

## 2. Key Features

### 2.1 Audit Logging

- **Event Recording**: Log all user actions and system events
- **Immutability**: Append-only logs with integrity verification
- **Contextual Metadata**: User, tenant, timestamp, action details
- **Searchability**: Query logs by various criteria

### 2.2 Compliance Reporting

- **Report Generation**: Generate compliance reports for specific periods
- **Multiple Formats**: PDF, CSV, JSON
- **Custom Reports**: Configurable report templates
- **Automated Scheduling**: Periodic report generation

### 2.3 Decision Tracking

- **User Decisions**: Track accept/reject/override decisions
- **Justification**: Capture decision rationale
- **Approver Chain**: Multi-level approval workflows
- **Decision History**: Complete audit trail

### 2.4 Evidence Management

- **Evidence Collection**: Gather supporting documents
- **Evidence Linking**: Associate evidence with decisions
- **Evidence Verification**: Validate evidence integrity
- **Evidence Retrieval**: Query evidence by criteria

## 3. API Contracts

### 3.1 Log Event

```
POST /v1/events
Body:
  {
    "event_type": "validation_decision",
    "user_id": "uuid",
    "tenant_id": "string",
    "action": "override",
    "resource": "validation_failure",
    "resource_id": "uuid",
    "metadata": {...}
  }
Response: 201 Created
  {
    "event_id": "uuid",
    "ledger_hash": "sha256..."
  }
```

### 3.2 Generate Report

```
POST /v1/reports
Body:
  {
    "report_type": "user_decisions",
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "tenant_id": "string",
    "format": "pdf"
  }
Response: 202 Accepted
  {
    "report_id": "uuid",
    "status": "generating"
  }
```

### 3.3 Query Events

```
GET /v1/events?user_id={id}&start_date={date}&limit=100
Response: 200 OK
  {
    "events": [...],
    "total": 1500,
    "page": 1,
    "pages": 15
  }
```

## 4. Dependencies

### 4.1 Upstream

- **Ledger Service**: Immutable hash-chained storage
- **Identity Service**: User information
- **PostgreSQL**: Queryable event storage

### 4.2 Downstream

- **Gateway**: Event logging
- **Validation**: Decision tracking
- **Workflow**: Workflow audit trail
- **All Services**: Audit logging

## 5. Data Models

### 5.1 Audit Event

```python
@dataclass
class AuditEvent:
    event_id: UUID
    event_type: str
    user_id: Optional[UUID]
    tenant_id: str
    timestamp: datetime
    action: str
    resource: str
    resource_id: Optional[UUID]
    metadata: dict
    ledger_hash: str
```

### 5.2 Compliance Report

```python
@dataclass
class ComplianceReport:
    report_id: UUID
    report_type: str
    start_date: date
    end_date: date
    tenant_id: str
    generated_at: datetime
    generated_by: UUID
    format: Literal["pdf", "csv", "json"]
    url: str
    status: Literal["generating", "completed", "failed"]
```

### 5.3 User Decision

```python
@dataclass
class UserDecision:
    decision_id: UUID
    user_id: UUID
    tenant_id: str
    decision_type: Literal["accept", "reject", "override"]
    resource_type: str
    resource_id: UUID
    justification: str
    timestamp: datetime
    approver_id: Optional[UUID]
```

## 6. Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Required | PostgreSQL connection |
| `LEDGER_URL` | <http://localhost:8136> | Ledger service URL |
| `REPORT_STORAGE_PATH` | /var/reports | Report storage location |
| `RETENTION_DAYS` | 2555 | 7 years retention |
| `ENABLE_REAL_TIME_SYNC` | true | Sync to ledger immediately |

## 7. Compliance Standards

### 7.1 Supported Standards

- **FedRAMP**: Federal Risk and Authorization Management Program
- **FISMA**: Federal Information Security Management Act
- **HIPAA**: Health Insurance Portability and Accountability Act
- **SOX**: Sarbanes-Oxley Act
- **GDPR**: General Data Protection Regulation

### 7.2 Audit Requirements

- User action logging
- Data access tracking
- Configuration changes
- Security events
- System errors

## 8. Performance Characteristics

### 8.1 Latency

- Event logging: < 50ms
- Event query: < 200ms
- Report generation: < 30s (typical)

### 8.2 Throughput

- 1000 events/second
- 10 concurrent report generations

## 9. Security Considerations

### 9.1 Data Protection

- Audit logs are immutable
- PII redaction in logs (configurable)
- Encrypted at rest and in transit
- Access controls (admin only)

### 9.2 Integrity Verification

- SHA-256 hashing via Ledger service
- Chain verification
- Tamper detection

## 10. Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-08 | Initial FDD creation |
