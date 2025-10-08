# Workflow Service Troubleshooting Guide

## Common Issues

### 1. Workflow Stuck in Running State

**Symptoms**: Execution never completes
**Solutions**:

- Check step timeouts
- Review service dependencies
- Check for circular dependencies
- Cancel and retry: `curl -X POST /v1/workflows/executions/{id}/cancel`

### 2. Step Failures

**Symptoms**: Workflow fails at specific step
**Solutions**:

- Review step logs
- Check service availability
- Verify step inputs
- Test step independently

### 3. Database Connection Pool Exhausted

**Symptoms**: "Too many connections"
**Solutions**:

- Increase pool size: `export DB_POOL_SIZE=30`
- Review long-running transactions
- Enable connection pooling
