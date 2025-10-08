# Identity Service Deployment Guide

## Local Development

```bash
cd services/identity

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://cortx:cortx_dev_password@localhost:5432/cortx"
export JWT_SECRET="dev-secret-change-in-production"
export REFRESH_TOKEN_SECRET="dev-refresh-secret-change-in-production"

# Run service
uvicorn app.main:app --host 0.0.0.0 --port 8082 --reload
```

## Docker

```bash
# Build
docker build -f services/identity/Dockerfile -t cortx-identity:latest .

# Run
docker run -d \
  -p 8082:8082 \
  -e DATABASE_URL="postgresql://cortx:cortx_dev_password@db:5432/cortx" \
  -e JWT_SECRET="production-secret" \
  -e REFRESH_TOKEN_SECRET="production-refresh-secret" \
  cortx-identity:latest
```

## Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: identity
  namespace: cortx-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: identity
  template:
    metadata:
      labels:
        app: identity
    spec:
      containers:
      - name: identity
        image: gcr.io/your-project/cortx-identity:latest
        ports:
        - containerPort: 8082
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: identity-secrets
              key: database-url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: identity-secrets
              key: jwt-secret
        - name: REFRESH_TOKEN_SECRET
          valueFrom:
            secretKeyRef:
              name: identity-secrets
              key: refresh-token-secret
        livenessProbe:
          httpGet:
            path: /health
            port: 8082
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8082
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 1Gi
```

## Database Setup

```sql
-- Create database
CREATE DATABASE cortx;

-- Create tables (managed by migrations)
-- See alembic migrations in app/migrations/
```

## Environment-Specific Configuration

### Development

- Short token expiration for testing
- No rate limiting
- Verbose logging

### Production

- Strict token expiration
- Rate limiting enabled
- Secrets from Secret Manager
- High availability (3+ replicas)
