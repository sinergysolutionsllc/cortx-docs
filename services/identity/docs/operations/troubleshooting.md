# Identity Service Troubleshooting Guide

## Common Issues

### 1. Login Failures

**Symptoms**: 401 Unauthorized on login

**Solutions**:

```bash
# Check user exists
psql -d cortx -c "SELECT id, username, is_active FROM users WHERE username='testuser';"

# Check password hash
# Passwords must be bcrypt hashed

# Check user is active
# is_active column must be true
```

### 2. Token Verification Failures

**Symptoms**: "Invalid token" or "Token expired"

**Solutions**:

```bash
# Check JWT_SECRET matches across services
echo $JWT_SECRET

# Decode token to check expiration
jwt decode $TOKEN

# Verify token algorithm matches (HS256 default)
```

### 3. Database Connection Errors

**Symptoms**: "Connection refused" or "Database unavailable"

**Solutions**:

```bash
# Test database connectivity
psql $DATABASE_URL

# Check DATABASE_URL format
# postgresql://user:password@host:5432/database

# Verify PostgreSQL is running
docker ps | grep postgres
```

### 4. High Failed Login Rate

**Symptoms**: Many 401 errors in logs

**Solutions**:

```bash
# Check for brute force attempts
tail -f logs/identity.log | grep "401"

# Implement rate limiting
# Configure LOGIN_RATE_LIMIT env variable

# Enable account lockout
# Configure MAX_LOGIN_ATTEMPTS
```

## Performance Issues

### Slow Token Verification

```bash
# Add Redis cache for token verification
export REDIS_URL="redis://localhost:6379"

# Cache user data
# Reduce database queries
```

### Database Connection Pool Exhausted

```bash
# Increase pool size
export DB_POOL_SIZE=20
export DB_MAX_OVERFLOW=10

# Monitor active connections
SELECT count(*) FROM pg_stat_activity WHERE datname='cortx';
```

## Security Incidents

### Compromised JWT Secret

```bash
# Rotate JWT secret immediately
kubectl create secret generic identity-secrets \
  --from-literal=jwt-secret='new-secret' \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart all services
kubectl rollout restart deployment/identity -n cortx-platform

# Invalidate all existing tokens
# Users must re-authenticate
```

## Monitoring

```bash
# Check service health
curl http://localhost:8082/health

# View recent logins
psql -d cortx -c "SELECT username, last_login FROM users ORDER BY last_login DESC LIMIT 10;"

# Check failed login attempts
grep "Login failed" logs/identity.log | wc -l
```
