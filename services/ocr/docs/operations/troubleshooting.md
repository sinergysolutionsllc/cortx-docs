# OCR Service Troubleshooting Guide

See also: [../README.md#troubleshooting](../README.md#troubleshooting)

## Common Issues

### 1. Tesseract Not Found

**Symptoms**: "tesseract: command not found" or "TesseractNotFoundError"

**Solutions**:

```bash
# macOS
brew install tesseract
tesseract --version  # Verify installation

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng
tesseract --version

# Verify Python can find it
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

### 2. Low Confidence Scores

**Symptoms**: Documents constantly escalating to AI tier

**Solutions**:

1. **Check Image Quality**
   - Ensure 300+ DPI resolution
   - Verify proper contrast (black text on white)
   - Check for skew/rotation

2. **Pre-processing**
   - Enable deskew
   - Apply denoising
   - Adjust threshold settings

3. **Adjust Thresholds**

   ```bash
   # Lower threshold for acceptable Tesseract results
   export OCR_TESSERACT_THRESHOLD="75.0"
   ```

4. **Force AI Tier for Known Complex Documents**

   ```bash
   curl -X POST /extract -d '{"force_tier": "ai_vision", ...}'
   ```

### 3. Anthropic API Errors

**Symptoms**: "API key invalid" or "Rate limit exceeded"

**Solutions**:

```bash
# Verify API key
echo $ANTHROPIC_API_KEY

# Check API quota
# Visit: https://console.anthropic.com/settings/limits

# Enable retry logic
export ANTHROPIC_MAX_RETRIES="3"
export ANTHROPIC_RETRY_DELAY="1"

# Implement exponential backoff
# (handled automatically by client library)
```

### 4. Database Connection Errors

**Symptoms**: "Connection refused" or "Database unavailable"

**Solutions**:

```bash
# Test database connectivity
psql $POSTGRES_URL

# Verify connection string format
# postgresql://user:password@host:5432/database

# Check PostgreSQL is running
docker ps | grep postgres

# Verify database exists
psql $POSTGRES_URL -c "SELECT 1;"

# Check table schema
psql $POSTGRES_URL -c "\dt ocr_*"
```

### 5. High Memory Usage

**Symptoms**: OOMKilled, swap usage high

**Solutions**:

```bash
# Monitor memory
docker stats ocr-service

# Reduce concurrent jobs
export MAX_CONCURRENT_JOBS="5"

# Enable caching to reduce reprocessing
export CACHE_ENABLED="true"

# Clear old jobs
psql $POSTGRES_URL -c "DELETE FROM ocr_jobs WHERE created_at < NOW() - INTERVAL '90 days';"
```

### 6. Cache Not Working

**Symptoms**: Same documents being reprocessed

**Solutions**:

```bash
# Verify cache is enabled
curl http://localhost:8137/health
# Check cache_enabled in response

# Check cache table
psql $POSTGRES_URL -c "SELECT count(*) FROM ocr_cache;"

# Verify hash calculation
# Document hash must be SHA-256 of content
sha256sum document.pdf

# Check cache hit rate
psql $POSTGRES_URL -c "SELECT AVG(hit_count) FROM ocr_cache;"
```

### 7. Slow Processing Times

**Symptoms**: Jobs taking > 10 seconds for simple documents

**Solutions**:

```bash
# Check Tesseract performance
time tesseract test-doc.png stdout

# Verify not hitting AI tier unnecessarily
# Check job status to see which tier was used

# Enable batch processing
# Process multiple documents concurrently

# Check database query performance
psql $POSTGRES_URL -c "EXPLAIN ANALYZE SELECT * FROM ocr_jobs WHERE id = 'uuid';"
```

### 8. Human Review Queue Backlog

**Symptoms**: > 100 jobs awaiting review

**Solutions**:

```bash
# Check queue depth
curl http://localhost:8137/stats | jq '.awaiting_review_count'

# Increase AI threshold to reduce escalations
export OCR_AI_THRESHOLD="80.0"

# Assign more reviewers
# (implement reviewer assignment system)

# Alert on queue depth
# Set up monitoring alert when queue > 50
```

## Performance Profiling

### Analyze Job Processing Times

```bash
# Get average time by tier
psql $POSTGRES_URL <<EOF
SELECT
    tier_used,
    COUNT(*) as job_count,
    AVG(processing_time_ms) as avg_ms,
    MAX(processing_time_ms) as max_ms,
    MIN(processing_time_ms) as min_ms
FROM ocr_jobs
WHERE status = 'completed'
GROUP BY tier_used;
EOF
```

### Monitor Cache Hit Rate

```bash
# Calculate cache effectiveness
psql $POSTGRES_URL <<EOF
SELECT
    COUNT(*) as cached_docs,
    SUM(hit_count) as total_hits,
    AVG(hit_count) as avg_hits_per_doc,
    SUM(processing_time_ms * hit_count) as time_saved_ms
FROM ocr_cache;
EOF
```

### Check Cost Metrics

```bash
# Estimate monthly costs
psql $POSTGRES_URL <<EOF
SELECT
    tier_used,
    COUNT(*) as job_count,
    CASE
        WHEN tier_used = 'tesseract' THEN 0
        WHEN tier_used = 'ai_vision' THEN COUNT(*) * 0.003
        WHEN tier_used = 'human_review' THEN COUNT(*) * 10.0
    END as estimated_cost_usd
FROM ocr_jobs
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY tier_used;
EOF
```

## Getting Help

For additional support:

1. **Check Existing Documentation**
   - [Service README](../README.md)
   - [Implementation Summary](../IMPLEMENTATION_SUMMARY.md)
   - [Quick Start Guide](../QUICKSTART.md)

2. **Collect Diagnostic Information**

   ```bash
   # Service logs
   docker logs ocr-service --tail=500 > ocr-logs.txt

   # Service health
   curl http://localhost:8137/health > ocr-health.json

   # Database state
   psql $POSTGRES_URL -c "\d+ ocr_jobs" > ocr-schema.txt
   psql $POSTGRES_URL -c "SELECT status, COUNT(*) FROM ocr_jobs GROUP BY status;" > ocr-status.txt
   ```

3. **Contact Support**
   - GitHub Issues: <https://github.com/sinergysolutionsllc/cortx/issues>
   - Email: <support@sinergysolutionsllc.com>
   - Include logs, health check, and steps to reproduce
