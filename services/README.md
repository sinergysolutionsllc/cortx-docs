# CORTX Platform Services - OpenAPI Specifications

This directory contains **OpenAPI specifications only** for CORTX platform services.

**The actual service implementations live in their respective GitHub repositories:**

- `sinergysolutionsllc/gateway` - Gateway service implementation
- `sinergysolutionsllc/identity` - Identity service implementation
- `sinergysolutionsllc/validation` - Validation service implementation
- `sinergysolutionsllc/ai-broker` - AI Broker service implementation
- `sinergysolutionsllc/workflow` - Workflow service implementation
- `sinergysolutionsllc/compliance` - Compliance service implementation
- `sinergysolutionsllc/ledger` - Ledger service implementation
- `sinergysolutionsllc/ocr` - OCR service implementation
- `sinergysolutionsllc/rag` - RAG service implementation

## Directory Structure

```
services/
├── gateway/
│   └── openapi.yaml         # OpenAPI spec synced from gateway repo
├── identity/
│   └── openapi.yaml         # OpenAPI spec synced from identity repo
├── validation/
│   └── openapi.yaml         # OpenAPI spec synced from validation repo
└── [other services...]
```

## Syncing OpenAPI Specs

OpenAPI specifications are synced from their respective service repositories using:

```bash
bash scripts/sync_openapi.sh
```

This script pulls the canonical `openapi.yaml` from each service repo.

## Documentation

These specs are used to generate the live documentation at:
https://sinergysolutionsllc.github.io/cortx-docs/

## Important Notes

- **DO NOT** add service implementation code to this directory
- **DO NOT** manually edit the OpenAPI specs here - edit them in the service repos
- Service implementations belong in their respective `sinergysolutionsllc/<service>` repos
- This is a documentation-only repository
