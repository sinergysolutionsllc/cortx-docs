# AI Broker Troubleshooting Guide

## Common Issues

### 1. Vertex AI Authentication Errors

**Symptoms**: "Could not authenticate with Vertex AI"

**Solutions**:

```bash
# Verify service account key exists
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# Test authentication
gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS

# Verify permissions
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:ai-broker@PROJECT_ID.iam.gserviceaccount.com"
```

### 2. Rate Limit Errors

**Symptoms**: "Quota exceeded" or "Too many requests"

**Solutions**:

```bash
# Check quota usage
gcloud alpha ai quotas list --project=PROJECT_ID

# Request quota increase in GCP Console
# Implement exponential backoff in code
```

### 3. High Costs

**Symptoms**: Unexpected AI API costs

**Solutions**:

```bash
# Enable cost tracking
export ENABLE_COST_TRACKING=true

# Monitor usage
curl http://localhost:8085/metrics | grep ai_cost

# Set usage limits
export MAX_TOKENS_PER_DAY=1000000

# Review expensive requests
SELECT * FROM ai_requests ORDER BY cost_usd DESC LIMIT 100;
```

### 4. Slow Response Times

**Symptoms**: Requests taking >5 seconds

**Solutions**:

```bash
# Use streaming for long responses
curl -N http://localhost:8085/v1/generate -d '{"prompt": "...", "stream": true}'

# Reduce max_tokens
# Use smaller models for simple tasks
# Implement caching for repeated prompts
```
