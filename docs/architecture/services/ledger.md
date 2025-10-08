# Ledger Service Architecture

**Version**: 1.0
**Status**: Implemented

This document outlines the architecture of the Ledger Service (`svc-ledger`).

## Purpose

The Ledger Service provides a tamper-evident, append-only log for recording critical events across the CORTX platform. It is essential for compliance and auditing, creating an immutable history of operations.

## Architecture

The service is implemented as a PostgreSQL-based append-only ledger with hash chaining. This approach was chosen over a more complex blockchain implementation to reduce operational overhead while still providing a strong guarantee of data integrity for internal audit purposes.

### Key Features

- **Append-Only**: Events can be added to the ledger, but not modified or deleted.
- **Hash Chaining**: Each event is cryptographically linked to the previous event, creating a verifiable chain. Any tampering with an event will break the chain.
- **Multi-Tenancy**: All events are isolated by tenant.
- **CSV Export**: Provides a simple way for auditors to export and review the ledger.

### Database Schema

```sql
CREATE TABLE ledger.events (
    id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    content_hash TEXT, -- SHA-256 of event_data
    previous_hash TEXT, -- The chain_hash of the previous event
    chain_hash TEXT UNIQUE -- SHA-256 of (content_hash + previous_hash)
);
```

## API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/append` | POST | Appends a new event to the ledger. |
| `/verify` | GET | Verifies the integrity of the entire hash chain for a tenant. |
| `/events` | GET | Lists events for a tenant, with pagination. |
| `/export` | GET | Exports the ledger for a tenant as a CSV file. |
