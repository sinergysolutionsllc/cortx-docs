# Ledger Service Troubleshooting

## Common Issues

### 1. Chain Integrity Failure

**Symptoms**: "Chain verification failed"
**Solutions**:

- **CRITICAL**: Do not modify any entries
- Identify first broken entry: `POST /v1/verify/chain`
- Check database logs for unauthorized modifications
- Restore from last known good backup
- Contact security team immediately

### 2. Slow Write Performance

**Symptoms**: Write latency > 100ms
**Solutions**:

- Enable batch writes: `export ENABLE_BATCH_WRITES=true`
- Increase batch size: `export BATCH_SIZE=200`
- Check database connection pool
- Verify database disk I/O

### 3. Storage Growth

**Symptoms**: Rapid storage consumption
**Solutions**:

- Enable compression: `export ENABLE_COMPRESSION=true`
- Archive old entries to cold storage
- Review data retention policies
- Monitor growth rate: `SELECT count(*), pg_size_pretty(pg_total_relation_size('ledger_entries'));`

### 4. Index Conflicts

**Symptoms**: "Duplicate key violation on index"
**Solutions**:

- Check for concurrent writes from multiple instances
- Verify index sequence is not corrupted
- Use advisory locks for writes
