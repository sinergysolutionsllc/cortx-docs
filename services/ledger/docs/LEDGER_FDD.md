# CORTX Ledger Service - Functional Design Document

**Version**: 1.0.0
**Last Updated**: 2025-10-08
**Status**: Active

## 1. Purpose and Scope

### 1.1 Purpose

Provides an immutable, append-only ledger with cryptographic hash chaining to ensure data integrity and tamper detection for audit trails and compliance evidence.

### 1.2 Scope

- Append-only entry storage
- SHA-256 hash chaining
- Entry verification and tamper detection
- Chain integrity verification
- High-throughput writes
- Entry retrieval and query

### 1.3 Out of Scope

- Blockchain consensus mechanisms (simplified single-node ledger)
- Smart contracts
- Cryptocurrency features
- Distributed ledger technology (DLT)

## 2. Key Features

### 2.1 Immutability

- **Append-Only**: Entries cannot be modified or deleted
- **Hash Chaining**: Each entry includes hash of previous entry
- **Tamper Detection**: Modified entries break the chain
- **Cryptographic Proof**: SHA-256 hashing

### 2.2 Entry Management

- **Write Entry**: Append new entry to ledger
- **Read Entry**: Retrieve entry by ID
- **Query Entries**: Search entries by criteria
- **Batch Write**: Write multiple entries efficiently

### 2.3 Verification

- **Entry Verification**: Verify single entry hash
- **Chain Verification**: Verify entire chain integrity
- **Partial Verification**: Verify chain from entry to current
- **Merkle Proof**: Generate proof of inclusion

### 2.4 Performance

- **High Throughput**: 10,000+ writes/second
- **Low Latency**: < 10ms write latency
- **Scalability**: Horizontal scaling via sharding (future)

## 3. API Contracts

### 3.1 Append Entry

```
POST /v1/entries
Body:
  {
    "data": {...},
    "metadata": {
      "source": "compliance-service",
      "event_type": "user_decision",
      "tenant_id": "tenant-123"
    }
  }
Response: 201 Created
  {
    "entry_id": "uuid",
    "entry_hash": "sha256...",
    "previous_hash": "sha256...",
    "index": 12345,
    "timestamp": "ISO8601"
  }
```

### 3.2 Get Entry

```
GET /v1/entries/{entry_id}
Response: 200 OK
  {
    "entry_id": "uuid",
    "data": {...},
    "metadata": {...},
    "entry_hash": "sha256...",
    "previous_hash": "sha256...",
    "index": 12345,
    "timestamp": "ISO8601"
  }
```

### 3.3 Verify Entry

```
POST /v1/verify/{entry_id}
Response: 200 OK
  {
    "valid": true,
    "entry_id": "uuid",
    "computed_hash": "sha256...",
    "stored_hash": "sha256...",
    "chain_valid": true
  }
```

### 3.4 Verify Chain

```
POST /v1/verify/chain?from_index={index}
Response: 200 OK
  {
    "valid": true,
    "start_index": 0,
    "end_index": 12345,
    "total_entries": 12346,
    "verification_time_ms": 1250
  }
```

## 4. Dependencies

### 4.1 Upstream

- **PostgreSQL**: Entry storage with ACID guarantees

### 4.2 Downstream

- **Compliance Service**: Audit log storage
- **Validation Service**: Decision evidence
- **Workflow Service**: Execution audit trail
- **All Services**: Immutable logging

## 5. Data Models

### 5.1 Ledger Entry

```python
@dataclass
class LedgerEntry:
    entry_id: UUID
    index: int
    data: dict
    metadata: dict
    entry_hash: str  # SHA-256
    previous_hash: str  # SHA-256
    timestamp: datetime
    created_at: datetime
```

### 5.2 Hash Calculation

```python
def calculate_hash(entry: LedgerEntry) -> str:
    content = f"{entry.index}|{entry.data}|{entry.metadata}|{entry.previous_hash}|{entry.timestamp}"
    return hashlib.sha256(content.encode()).hexdigest()
```

### 5.3 Verification Result

```python
@dataclass
class VerificationResult:
    valid: bool
    entry_id: UUID
    computed_hash: str
    stored_hash: str
    chain_valid: bool
    errors: List[str]
```

## 6. Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Required | PostgreSQL connection |
| `ENABLE_BATCH_WRITES` | true | Batch multiple writes |
| `BATCH_SIZE` | 100 | Entries per batch |
| `BATCH_TIMEOUT_MS` | 100 | Max batch wait time |
| `ENABLE_COMPRESSION` | false | Compress entry data |
| `HASH_ALGORITHM` | SHA256 | Hash algorithm |

## 7. Hash Chain Structure

### 7.1 Genesis Entry

```python
{
  "entry_id": "00000000-0000-0000-0000-000000000000",
  "index": 0,
  "data": {"genesis": true},
  "entry_hash": "sha256...",
  "previous_hash": "0" * 64,  # All zeros for first entry
  "timestamp": "2025-01-01T00:00:00Z"
}
```

### 7.2 Subsequent Entries

```python
{
  "entry_id": "uuid",
  "index": n,
  "data": {...},
  "entry_hash": hash(index + data + previous_hash + timestamp),
  "previous_hash": <hash of entry n-1>,
  "timestamp": "ISO8601"
}
```

### 7.3 Chain Verification

```python
def verify_chain(start_index: int, end_index: int) -> bool:
    for i in range(start_index, end_index):
        entry = get_entry(i)
        if entry.entry_hash != calculate_hash(entry):
            return False
        if i > 0:
            prev_entry = get_entry(i - 1)
            if entry.previous_hash != prev_entry.entry_hash:
                return False
    return True
```

## 8. Performance Characteristics

### 8.1 Latency

- Single write: < 10ms
- Batch write: < 50ms (100 entries)
- Read: < 5ms
- Verify entry: < 10ms
- Verify chain (1000 entries): < 1s

### 8.2 Throughput

- 10,000 writes/second (single instance)
- 50,000 reads/second
- 1,000 verifications/second

### 8.3 Resource Requirements

- CPU: 1 core baseline, 4 cores under load
- Memory: 512MB baseline, 2GB under load
- Storage: 1GB per 10K entries (uncompressed)

## 9. Security Considerations

### 9.1 Data Integrity

- SHA-256 cryptographic hashing
- Hash chaining prevents tampering
- Verification detects any modifications
- Immutable storage

### 9.2 Access Control

- Write access restricted (admin/service accounts only)
- Read access based on tenant isolation
- Audit all access attempts

### 9.3 Backup and Recovery

- Regular database backups
- Point-in-time recovery
- Chain verification after restore
- Genesis entry protection

## 10. Monitoring

### 10.1 Metrics

- Write throughput (entries/second)
- Read latency (p50, p95, p99)
- Verification count
- Chain integrity status
- Storage growth rate

### 10.2 Alerts

- Chain integrity failure
- Write latency > 100ms
- Verification failures
- Storage capacity < 20%

## 11. Future Enhancements

- Distributed ledger (multi-node)
- Sharding for horizontal scaling
- Merkle tree proofs
- Compression algorithms
- Archive old entries to cold storage

## 12. Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-08 | Initial FDD creation |
