# Validation Service Troubleshooting Guide

## Common Issues

### 1. RulePack Not Found

**Symptoms**: "RulePack domain not found"
**Solutions**:

- Verify RulePack registry is accessible
- Check domain name spelling
- Ensure RulePack is deployed

### 2. RAG Service Timeout

**Symptoms**: Validation hangs in RAG mode
**Solutions**:

- Check RAG service health
- Increase timeout: `export RAG_TIMEOUT_SECONDS=30`
- Fall back to static mode

### 3. Validation Cache Issues

**Symptoms**: Stale validation results
**Solutions**:

- Clear cache: `curl -X DELETE http://localhost:8083/v1/cache`
- Reduce TTL: `export CACHE_TTL_SECONDS=300`
- Disable caching: `export ENABLE_CACHING=false`
