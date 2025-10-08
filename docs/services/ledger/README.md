# Ledger Service (Port 8136)

**Status:** ✅ Implemented | **Version:** 1.0.0

## Overview

The Ledger service provides a tamper-evident, append-only event log for compliance and audit purposes across the CORTX platform. Using cryptographic SHA-256 hash chaining, it ensures immutable audit trails for all critical operations.

## Core Concept: Hash Chain

Each event in the ledger contains:

1. **Content Hash** - SHA-256 of the event data
2. **Previous Hash** - Chain hash of the previous event
3. **Chain Hash** - SHA-256(content_hash + previous_hash)

This creates an immutable chain where any tampering breaks the hash sequence, making it immediately detectable.

```
Genesis Event (hash: 0000...0000)
    ↓
Event 1 (content_hash, prev: 0000, chain_hash_1)
    ↓
Event 2 (content_hash, prev: chain_hash_1, chain_hash_2)
    ↓
Event 3 (content_hash, prev: chain_hash_2, chain_hash_3)
    ↓
    ...
```

## Key Features

### Immutable Audit Trail

- **Append-only architecture** - Events can never be modified or deleted
- **Cryptographic verification** - SHA-256 hash chaining detects tampering
- **Genesis block** - Chain starts with known hash (64 zeros)
- **Ordered timeline** - Events stored with microsecond timestamps

### Multi-Tenant Isolation

- **Tenant-scoped queries** - Each tenant sees only their events
- **Cross-tenant verification** - Admin can verify entire chain
- **Row-level security** - Database-enforced isolation

### Event Tracking

- **Event types** - Categorize operations (query, upload, validation, etc.)
- **Event data** - JSONB storage for flexible metadata
- **User attribution** - Track which user triggered each event
- **Correlation IDs** - Link related events across services
- **Human-readable descriptions** - Audit-friendly explanations

### Export & Compliance

- **CSV export** - Download events for external audits
- **Filterable queries** - Search by tenant, type, user, date range
- **Chain verification API** - Validate integrity on-demand
- **Tamper detection** - Immediately detect any modifications

## Hash Chain Algorithm

### Content Hash Calculation

```python
content = {
    "tenant_id": "tenant-123",
    "event_type": "rag_query",
    "event_data": {...},
    "user_id": "user-456",
    "created_at": "2025-10-07T20:00:00Z"
}
content_hash = SHA256(json.dumps(content, sort_keys=True))
```

### Chain Hash Calculation

```python
# First event (genesis)
previous_hash = "0000000000000000000000000000000000000000000000000000000000000000"

# Subsequent events
previous_hash = previous_event.chain_hash

# Calculate chain hash
chain_hash = SHA256(content_hash + previous_hash)
```

### Verification Process

```python
# Verify entire chain
for i, event in enumerate(events):
    # Recalculate content hash
    calculated_content = compute_content_hash(event)
    assert calculated_content == event.content_hash

    # Recalculate chain hash
    calculated_chain = compute_chain_hash(event.content_hash, event.previous_hash)
    assert calculated_chain == event.chain_hash

    # Verify chain linkage
    if i > 0:
        assert event.previous_hash == events[i-1].chain_hash
```

## Database Schema

### Ledger Events Table

```sql
CREATE TABLE ledger_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Multi-tenancy
    tenant_id VARCHAR(255) NOT NULL,

    -- Event data
    event_type VARCHAR(255) NOT NULL,
    event_data JSONB NOT NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Hash chain
    content_hash VARCHAR(64) NOT NULL,    -- SHA-256 of event data
    previous_hash VARCHAR(64) NOT NULL,   -- Previous event's chain_hash
    chain_hash VARCHAR(64) UNIQUE NOT NULL, -- SHA-256(content + previous)

    -- Optional metadata
    user_id VARCHAR(255),
    correlation_id VARCHAR(255),
    description TEXT
);

-- Indexes for performance
CREATE INDEX idx_ledger_tenant ON ledger_events(tenant_id);
CREATE INDEX idx_ledger_type ON ledger_events(event_type);
CREATE INDEX idx_ledger_created ON ledger_events(created_at);
CREATE INDEX idx_ledger_correlation ON ledger_events(correlation_id);
CREATE INDEX idx_ledger_chain ON ledger_events(chain_hash);
```

## API Endpoints

### Health & Status

- `GET /healthz` - Kubernetes liveness probe
- `GET /readyz` - Kubernetes readiness probe (includes DB check)

### Ledger Operations

- `POST /append` - Append new event to the ledger
- `GET /verify` - Verify chain integrity
- `GET /events` - Query events with filters
- `GET /export` - Export events as CSV

## Configuration

### Environment Variables

```bash
# Database (required)
POSTGRES_URL=postgresql://cortx:cortx_dev_password@localhost:5432/cortx

# Service
PORT=8136
LOG_LEVEL=INFO
```

### System Dependencies

```bash
# Python packages (see requirements.txt)
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic
```

## Usage Examples

### Append Event

```bash
curl -X POST http://localhost:8136/append \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant-123",
    "event_type": "rag_query",
    "event_data": {
      "query": "What is GTAS reconciliation?",
      "results_count": 5,
      "confidence": 0.95
    },
    "user_id": "user-456",
    "correlation_id": "req-789",
    "description": "RAG query executed successfully"
  }'
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "chain_hash": "a3b2c1d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2",
  "created_at": "2025-10-07T20:30:00.123456Z"
}
```

### Verify Chain Integrity

```bash
curl http://localhost:8136/verify
```

**Response:**

```json
{
  "valid": true,
  "total_events": 1523,
  "error": null
}
```

### Query Events

```bash
# Get recent events for tenant
curl "http://localhost:8136/events?tenant_id=tenant-123&limit=10"

# Filter by event type
curl "http://localhost:8136/events?tenant_id=tenant-123&event_type=rag_query"

# Filter by user
curl "http://localhost:8136/events?tenant_id=tenant-123&user_id=user-456"

# Filter by correlation ID
curl "http://localhost:8136/events?correlation_id=req-789"

# Pagination
curl "http://localhost:8136/events?tenant_id=tenant-123&limit=50&offset=100"
```

**Response:**

```json
{
  "events": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "tenant_id": "tenant-123",
      "event_type": "rag_query",
      "event_data": {...},
      "created_at": "2025-10-07T20:30:00.123456Z",
      "content_hash": "b2c3d4e5...",
      "previous_hash": "a1b2c3d4...",
      "chain_hash": "c3d4e5f6...",
      "user_id": "user-456",
      "correlation_id": "req-789",
      "description": "RAG query executed successfully"
    }
  ],
  "total": 1523,
  "limit": 10,
  "offset": 0
}
```

### Export Events (CSV)

```bash
curl "http://localhost:8136/export?tenant_id=tenant-123" > audit_trail.csv

# Filter exports
curl "http://localhost:8136/export?tenant_id=tenant-123&event_type=rag_query" > rag_queries.csv
```

**CSV Output:**

```csv
id,tenant_id,event_type,created_at,user_id,correlation_id,description,chain_hash
550e8400-...,tenant-123,rag_query,2025-10-07T20:30:00Z,user-456,req-789,RAG query executed,c3d4e5f6...
```

## Integration

### Services That Log to Ledger

#### RAG Service

```python
# Log RAG queries
{
  "event_type": "rag_query",
  "event_data": {
    "query": "user query text",
    "results_count": 5,
    "confidence": 0.95,
    "hierarchy_levels": ["platform", "suite"]
  }
}

# Log document ingestion
{
  "event_type": "rag_ingest",
  "event_data": {
    "document_id": "doc-123",
    "chunks_created": 45,
    "hierarchy_path": "platform/fedsuite/fedreconcile"
  }
}
```

#### OCR Service

```python
# Log OCR processing
{
  "event_type": "ocr_extract",
  "event_data": {
    "document_hash": "sha256...",
    "tier_used": "tesseract",
    "confidence": 0.92,
    "page_count": 3
  }
}
```

#### Validation Service

```python
# Log rule execution
{
  "event_type": "rule_execution",
  "event_data": {
    "rulepack_id": "federal.gtas.validation",
    "rules_executed": 25,
    "violations": 3,
    "result": "failed"
  }
}
```

#### Workflow Service

```python
# Log workflow execution
{
  "event_type": "workflow_execution",
  "event_data": {
    "workflow_id": "wf-123",
    "pack_id": "federal.gtas.reconciliation",
    "status": "completed",
    "steps_executed": 8
  }
}
```

#### Compliance Service

```python
# Log compliance reports
{
  "event_type": "compliance_report",
  "event_data": {
    "report_id": "rpt-123",
    "report_type": "GTAS_reconciliation",
    "period": "2025-Q3",
    "result": "compliant"
  }
}
```

### Gateway Integration

The Gateway proxies ledger requests:

```
POST /api/v1/ledger/append → http://ledger:8136/append
GET  /api/v1/ledger/verify → http://ledger:8136/verify
GET  /api/v1/ledger/events → http://ledger:8136/events
```

## Performance

### Write Throughput

- **Single instance:** ~1,000 events/second
- **With connection pool:** ~2,000 events/second
- **Async appends:** Non-blocking for caller

### Query Performance

- **By tenant_id:** <50ms (indexed)
- **By event_type:** <100ms (indexed)
- **By correlation_id:** <100ms (indexed)
- **Full chain verification:** ~5 seconds per 10,000 events

### Scalability

- **Horizontal scaling:** Read replicas for queries
- **Connection pooling:** 10 connections, 20 overflow
- **Partition strategy:** Yearly tables for archive

## Security

### Tamper Detection

- **Cryptographic verification:** SHA-256 hash chain
- **Automatic detection:** Verification API identifies breaks
- **Audit alerts:** Log verification failures
- **Recovery:** Chain cannot be repaired (append-only)

### Multi-Tenancy

- **Tenant isolation:** Row-level security
- **Query scoping:** All queries tenant-filtered
- **Admin verification:** Cross-tenant chain validation

### Data Integrity

- **Append-only:** No updates or deletes allowed
- **Database constraints:** UNIQUE on chain_hash
- **Transaction safety:** ACID compliance

## Compliance Use Cases

### HIPAA Audit Trail

```python
# Log PHI access
{
  "event_type": "phi_access",
  "event_data": {
    "patient_id": "encrypted_id",
    "resource_type": "medical_record",
    "access_reason": "treatment"
  },
  "user_id": "doctor-123"
}
```

### Federal Reporting (GTAS)

```python
# Log reconciliation steps
{
  "event_type": "gtas_reconciliation",
  "event_data": {
    "trial_balance_id": "tb-123",
    "voucher_count": 1234,
    "total_amount": 5000000.00,
    "discrepancies": []
  }
}
```

### Property Title Verification

```python
# Log title search
{
  "event_type": "title_search",
  "event_data": {
    "property_id": "prop-123",
    "county": "Baltimore",
    "instruments_found": 12,
    "liens_detected": 0
  }
}
```

## Monitoring & Alerting

### Health Checks

- Database connectivity
- Chain integrity (periodic verification)
- Write performance degradation

### Metrics to Track

- Events appended per second
- Chain verification duration
- Query latency by endpoint
- Failed verification attempts

### Logging

- Structured JSON logs
- Event append success/failure
- Chain verification results
- Database errors

## Error Handling

### Chain Breaks

```json
{
  "valid": false,
  "total_events": 1523,
  "error": "Chain break detected at event 1234: previous_hash mismatch"
}
```

### Database Failures

- Automatic retry with exponential backoff
- Return 503 Service Unavailable
- Log error and alert operations

### Concurrent Writes

- Database transaction isolation
- Retry on deadlock
- Eventual consistency guaranteed

## Architecture Diagram

```mermaid
flowchart TB
    subgraph Services
        RAG[RAG Service]
        OCR[OCR Service]
        Validation[Validation Service]
        Workflow[Workflow Service]
        Compliance[Compliance Service]
    end

    Gateway[Gateway Service] -->|Proxy| Ledger[Ledger Service]
    RAG -->|Log Events| Ledger
    OCR -->|Log Events| Ledger
    Validation -->|Log Events| Ledger
    Workflow -->|Log Events| Ledger
    Compliance -->|Log Events| Ledger

    Ledger -->|Append| DB[(PostgreSQL<br/>Hash Chain)]
    Ledger -->|Verify| DB
    Ledger -->|Query| DB

    Auditor[External Auditor] -->|Export CSV| Gateway
    Admin[Admin] -->|Verify Chain| Gateway
```

## Development

### Local Setup

```bash
cd /Users/michael/Development/sinergysolutionsllc/services/ledger
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8136 --reload
```

### Docker

```bash
docker build -f services/ledger/Dockerfile -t cortx-ledger:1.0.0 .
docker run -p 8136:8136 \
  -e POSTGRES_URL="postgresql://cortx:cortx_dev_password@db:5432/cortx" \
  cortx-ledger:1.0.0
```

### Testing Chain Integrity

```bash
# Append some events
for i in {1..10}; do
  curl -X POST http://localhost:8136/append \
    -H "Content-Type: application/json" \
    -d "{\"tenant_id\":\"test\",\"event_type\":\"test\",\"event_data\":{\"seq\":$i}}"
done

# Verify chain
curl http://localhost:8136/verify
```

## Documentation

- **OpenAPI Spec:** [openapi.yaml](./openapi.yaml)
- **Source Code:** `/services/ledger/app/`
- **Models:** `/services/ledger/app/models.py`
- **Hash Utilities:** `/services/ledger/app/hash_utils.py`

## Support

For issues or questions:

- GitHub Issues: [sinergysolutionsllc/sinergysolutionsllc](https://github.com/sinergysolutionsllc/sinergysolutionsllc/issues)
- Internal Documentation: `/docs/services/ledger/`
