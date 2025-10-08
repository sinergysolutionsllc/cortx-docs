# ADR-001: Ledger Service Implementation

- **Status**: Accepted
- **Date**: 2025-10-07
- **Deciders**: AI Platform Team

---

## Context and Problem Statement

The CORTX platform requires a centralized Ledger Service for immutable audit trails. The existing implementation in `cortx-hashtrack` is a sophisticated blockchain-based service, while the platform specification calls for a simpler append-only event log. This ADR resolves the mismatch between the existing implementation and the platform's requirements.

---

## Decision Drivers

- **Simplicity**: The platform needs a solution that is easy to deploy and maintain.
- **Cost**: The solution should have low operational costs.
- **Speed of Implementation**: The service needs to be implemented quickly to support other platform features.
- **Compliance Needs**: The solution must be "good enough" for internal audit trails and compliance requirements.

---

## Considered Options

### Option 1: Use `cortx-hashtrack` Implementation As-Is

This option involves porting the existing blockchain-based hash anchoring service from `cortx-hashtrack` to the platform.

- **Pros**:
  - Uses production-ready code.
  - More sophisticated and provides a higher degree of trust via an external blockchain.
  - Privacy-preserving (anchors hashes only).
- **Cons**:
  - Requires external blockchain infrastructure (e.g., Hyperledger), which adds complexity and cost.
  - Overkill for the platform's immediate need for a simple audit log.
  - The implementation is PropVerify-specific and would require generalization.

### Option 2: Build a Simpler, PostgreSQL-Based Hash-Chain Ledger

This option involves building a new service based on the platform specification, using PostgreSQL to store an append-only log with a cryptographic hash chain.

- **Pros**:
  - Aligns perfectly with the platform specification.
  - Much simpler to deploy and operate, as it only requires PostgreSQL.
  - Lower operational cost.
  - Sufficient for internal audit and compliance needs.
  - Faster to implement by following the patterns of other platform services like `svc-rag`.
- **Cons**:
  - Less theoretically "immutable" than a true blockchain, as the database could be modified by a privileged user.
  - Loses the blockchain abstraction layer.

### Option 3: Hybrid Approach

This option involves implementing the PostgreSQL-based ledger (Option 2) but adding an optional feature to periodically anchor the state of the ledger to an external blockchain.

- **Pros**:
  - Provides the best of both worlds: fast local operations with the option for higher-trust external verification.
- **Cons**:
  - The most complex option to implement, combining both systems.

---

## Decision Outcome

**Chosen Option**: Option 2: Build a Simpler, PostgreSQL-Based Hash-Chain Ledger

This option was chosen because it directly meets the platform's specified requirements while being the simplest and most cost-effective solution. The primary use case is for internal audit trails, for which a PostgreSQL-based hash-chain is sufficient. This approach allows for rapid implementation and avoids the significant operational overhead of managing a blockchain infrastructure.

### Consequences

- **Positive**:
  - The Ledger Service can be developed and deployed quickly.
  - The platform's infrastructure remains simple, with no new external dependencies like a blockchain.
  - The implementation will be consistent with other platform services.
- **Negative**:
  - The ledger is not as theoretically immutable as a blockchain-based solution. This is an acceptable trade-off for the current requirements.
  - The advanced blockchain-anchoring logic from `cortx-hashtrack` will be shelved for now, to be potentially revisited in the future.
