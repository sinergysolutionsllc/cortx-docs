# RulePack Schema Reference

This document defines the JSON schema for RulePacks in CORTX.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "RulePack",
  "type": "object",
  "required": ["metadata", "rules"],
  "properties": {
    "metadata": {
      "type": "object",
      "properties": {
        "pack_id": {"type": "string"},
        "version": {"type": "string"},
        "created_by": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"}
      }
    },
    "rules": {
      "type": "array",
      "items": {"$ref": "#/definitions/rule"}
    }
  },
  "definitions": {
    "rule": {
      "type": "object",
      "properties": {
        "rule_id": {"type": "string"},
        "type": {"enum": ["FATAL", "WARNING", "INFO"]},
        "field": {"type": "string"},
        "operator": {"type": "string"},
        "error_message": {"type": "string"}
      },
      "required": ["rule_id", "type", "field", "operator", "error_message"]
    }
  }
}