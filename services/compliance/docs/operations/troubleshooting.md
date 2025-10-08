# Compliance Service Troubleshooting

## Common Issues

### 1. Event Logging Failures

**Symptoms**: Events not being logged
**Solutions**:

- Check database connectivity
- Verify Ledger service is accessible
- Check disk space for report storage

### 2. Report Generation Failures

**Symptoms**: Reports stuck in "generating" status
**Solutions**:

- Check report worker process
- Verify storage path permissions
- Review report query performance

### 3. Ledger Sync Issues

**Symptoms**: Events logged but not in ledger
**Solutions**:

- Check LEDGER_URL configuration
- Verify ledger service health
- Enable retry: `export LEDGER_RETRY_COUNT=3`
