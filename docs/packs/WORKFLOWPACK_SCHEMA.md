# WorkflowPack Schema Reference

This document defines the YAML schema for WorkflowPacks in CORTX.

```yaml
workflow_id: string  # Unique identifier
version: string      # Semantic version
description: string
metadata:
  compliance: [string]
  created_by: string
  created_at: datetime
steps:
  - id: string
    type: one_of [data-source, validation, calculation, decision, approval, ai-inference, data-sink]
    config: object   # Step-specific config
    depends_on: [string]  # Optional