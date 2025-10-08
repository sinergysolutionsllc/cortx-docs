# Gateway Service Troubleshooting Guide

This guide covers common issues and their resolutions for the CORTX Gateway service.

## Quick Diagnostics

### Check Service Health

```bash
# Local
curl http://localhost:8080/health

# Production
curl https://api.cortx.ai/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "gateway",
  "version": "1.0.0",
  "timestamp": "2025-10-08T12:00:00Z"
}
```

### Check Service Info

```bash
curl http://localhost:8080/_info
```

Expected response:

```json
{
  "service": "gateway",
  "version": "1.0.0",
  "features": {
    "analytics_enabled": true,
    "rag_validation": true,
    "suite_proxies": ["fedsuite", "propverify"]
  }
}
```

### View Logs

```bash
# Docker
docker logs cortx-gateway

# Kubernetes
kubectl logs -n cortx-platform deployment/gateway --tail=100 -f

# Cloud Run
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=cortx-gateway" --limit 50
```

## Common Issues

### 1. Service Won't Start

#### Symptoms

- Container exits immediately
- "Connection refused" errors
- Health check failures

#### Possible Causes & Solutions

**Missing Environment Variables**

```bash
# Check required variables are set
docker exec cortx-gateway env | grep CORTX

# If missing, add to docker run or k8s configmap
-e CORTX_REGISTRY_URL=http://registry:8081
```

**Port Already in Use**

```bash
# Check what's using port 8080
lsof -i :8080

# Kill the process or use different port
docker run -p 8081:8080 cortx-gateway:latest
```

**Database Connection Failed**

```bash
# Test database connectivity
psql -h localhost -U cortx -d cortx

# Check DATABASE_URL format
postgresql://user:password@host:5432/database
```

### 2. Authentication Failures

#### Symptoms

- 401 Unauthorized errors
- "Invalid token" messages
- JWT verification failures

#### Possible Causes & Solutions

**Identity Service Unavailable**

```bash
# Check Identity service health
curl http://localhost:8082/health

# Verify CORTX_IDENTITY_URL is correct
echo $CORTX_IDENTITY_URL
```

**Expired JWT Token**

```bash
# Decode token to check expiration
# Use jwt.io or jwt-cli
jwt decode $TOKEN

# Get new token
curl -X POST http://localhost:8082/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

**Wrong JWT Secret**

```bash
# Verify JWT_SECRET matches Identity service
# Check Secret Manager or kubernetes secret
kubectl get secret gateway-secrets -n cortx-platform -o jsonpath='{.data.jwt-secret}' | base64 -d
```

**REQUIRE_AUTH Misconfiguration**

```bash
# For local dev, disable auth
export REQUIRE_AUTH=false

# For production, ensure it's enabled
export REQUIRE_AUTH=true
```

### 3. Upstream Service Errors (502 Bad Gateway)

#### Symptoms

- 502 Bad Gateway responses
- "Upstream connect error" in logs
- Timeout errors

#### Possible Causes & Solutions

**Validation Service Down**

```bash
# Check validation service
curl http://localhost:8083/health

# Check service URL configuration
echo $CORTX_VALIDATION_URL

# Update if incorrect
export CORTX_VALIDATION_URL=http://validation:8083
```

**RAG Service Timeout**

```bash
# Check RAG service response time
time curl http://localhost:8138/health

# Increase timeout in gateway config
UPSTREAM_TIMEOUT_SECONDS=30

# Check RAG service logs for performance issues
kubectl logs -n cortx-platform deployment/rag --tail=50
```

**Network Connectivity Issues**

```bash
# Test connectivity from gateway container
docker exec cortx-gateway curl http://validation:8083/health

# Check DNS resolution
docker exec cortx-gateway nslookup validation

# Verify service discovery
kubectl get svc -n cortx-platform
```

### 4. CORS Errors

#### Symptoms

- "CORS policy blocked" in browser console
- Preflight OPTIONS requests failing
- "No 'Access-Control-Allow-Origin' header"

#### Possible Causes & Solutions

**Missing Origin in ALLOWED_ORIGINS**

```bash
# Check current configuration
echo $ALLOWED_ORIGINS

# Add your origin
export ALLOWED_ORIGINS="http://localhost:3000,https://app.cortx.ai"

# Restart service
docker restart cortx-gateway
```

**Preflight Request Issues**

```bash
# Test OPTIONS request
curl -X OPTIONS http://localhost:8080/jobs/validate \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Should return Access-Control-Allow-Origin header
```

**Credentials Not Allowed**

```bash
# If using credentials, ensure CORS allows it
# Update FastAPI CORS middleware to include:
allow_credentials=True
```

### 5. High Latency / Performance Issues

#### Symptoms

- Slow API responses
- Timeouts under load
- High CPU/memory usage

#### Possible Causes & Solutions

**Too Few Replicas**

```bash
# Check current replicas
kubectl get deployment gateway -n cortx-platform

# Scale up
kubectl scale deployment gateway --replicas=5 -n cortx-platform
```

**Resource Constraints**

```bash
# Check resource usage
kubectl top pod -n cortx-platform -l app=gateway

# Increase resources in deployment
resources:
  requests:
    cpu: 1000m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 2Gi
```

**Slow Upstream Services**

```bash
# Check upstream service latency
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8083/health

# curl-format.txt:
time_namelookup:  %{time_namelookup}\n
time_connect:  %{time_connect}\n
time_starttransfer:  %{time_starttransfer}\n
time_total:  %{time_total}\n
```

**Database Connection Pool Exhausted**

```bash
# Increase connection pool size
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Monitor active connections
SELECT count(*) FROM pg_stat_activity WHERE datname='cortx';
```

### 6. Suite Proxy Errors

#### Symptoms

- 404 Not Found for suite routes
- Proxy routing failures
- "Suite not configured" errors

#### Possible Causes & Solutions

**Suite Backend Not Available**

```bash
# Check FedSuite backend
curl http://localhost:9000/health

# Update suite backend URL if needed
FEDSUITE_BACKEND_URL=http://fedsuite:9000
```

**Authentication Not Propagated**

```bash
# Verify JWT token is passed to backend
# Check proxy headers in logs

# Ensure Authorization header is forwarded
headers_to_forward = ["Authorization", "X-Tenant-ID", "X-Request-ID"]
```

**Path Rewriting Issues**

```bash
# Test proxy path
curl -X POST http://localhost:8080/fedsuite/reconcile \
  -H "Authorization: Bearer $TOKEN" \
  -v

# Check if path is correctly rewritten to backend
# /fedsuite/reconcile -> /reconcile
```

### 7. Memory Leaks

#### Symptoms

- Memory usage continuously increasing
- OOMKilled pod restarts
- Swap usage increasing

#### Diagnostics

```bash
# Monitor memory over time
kubectl top pod -n cortx-platform -l app=gateway --watch

# Check for memory leaks in application
# Use memory profiler
python -m memory_profiler app/main.py

# Review unclosed connections/resources
# Check for circular references in code
```

#### Solutions

```bash
# Increase memory limits
resources:
  limits:
    memory: 2Gi

# Enable periodic pod recycling
strategy:
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0

# Review code for resource cleanup
# Ensure all connections are properly closed
```

### 8. Database Connection Issues

#### Symptoms

- "Connection pool exhausted"
- "Too many connections"
- Slow query responses

#### Solutions

```bash
# Check active connections
SELECT count(*) FROM pg_stat_activity WHERE datname='cortx';

# Increase pool size
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=10

# Enable connection pooling
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true

# Close idle connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND state_change < now() - interval '10 minutes';
```

## Debugging Tips

### Enable Debug Logging

```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG

# Restart service
docker restart cortx-gateway

# Or for Kubernetes
kubectl set env deployment/gateway LOG_LEVEL=DEBUG -n cortx-platform
```

### Capture Request/Response

```bash
# Use verbose curl
curl -v -X POST http://localhost:8080/jobs/validate?domain=test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input_data": {}}'

# Or use httpie for better formatting
http POST localhost:8080/jobs/validate?domain=test \
  Authorization:"Bearer $TOKEN" \
  input_data:='{}' \
  --print=HhBb
```

### Test Authentication Flow

```bash
# 1. Login to get token
TOKEN=$(curl -X POST http://localhost:8082/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}' \
  | jq -r '.access_token')

# 2. Use token in request
curl -X GET http://localhost:8080/jobs/123 \
  -H "Authorization: Bearer $TOKEN"

# 3. Verify token
curl -X GET http://localhost:8082/v1/auth/verify \
  -H "Authorization: Bearer $TOKEN"
```

### Check Service Dependencies

```bash
# Create a test script
#!/bin/bash
services=(
  "http://localhost:8082/health:Identity"
  "http://localhost:8083/health:Validation"
  "http://localhost:8138/health:RAG"
  "http://localhost:8135/health:Compliance"
)

for service in "${services[@]}"; do
  url="${service%%:*}"
  name="${service##*:}"
  if curl -sf "$url" > /dev/null; then
    echo "✓ $name is healthy"
  else
    echo "✗ $name is down"
  fi
done
```

## Performance Profiling

### Request Timing

```bash
# Profile API endpoint
curl -w "@curl-timing.txt" -o /dev/null -s http://localhost:8080/jobs/validate

# curl-timing.txt
time_namelookup:    %{time_namelookup}s\n
time_connect:       %{time_connect}s\n
time_appconnect:    %{time_appconnect}s\n
time_pretransfer:   %{time_pretransfer}s\n
time_redirect:      %{time_redirect}s\n
time_starttransfer: %{time_starttransfer}s\n
time_total:         %{time_total}s\n
```

### Load Testing

```bash
# Install hey load testing tool
go install github.com/rakyll/hey@latest

# Run load test
hey -n 1000 -c 10 -m POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input_data": {}}' \
  http://localhost:8080/jobs/validate?domain=test
```

## Getting Help

### Collect Diagnostic Information

```bash
# Service logs
kubectl logs -n cortx-platform deployment/gateway --tail=500 > gateway-logs.txt

# Service configuration
kubectl describe deployment gateway -n cortx-platform > gateway-config.txt

# Pod status
kubectl get pods -n cortx-platform -l app=gateway -o wide > gateway-pods.txt

# Recent events
kubectl get events -n cortx-platform --sort-by='.lastTimestamp' > gateway-events.txt
```

### Contact Support

Include the following information:

1. Service version and deployment environment
2. Error message and stack trace
3. Recent logs (last 500 lines)
4. Request that triggered the issue (curl command or screenshots)
5. Service configuration (sanitized, no secrets)
6. Upstream service health status

Support channels:

- GitHub Issues: <https://github.com/sinergysolutionsllc/cortx/issues>
- Email: <support@sinergysolutionsllc.com>
- Slack: #cortx-platform-support
