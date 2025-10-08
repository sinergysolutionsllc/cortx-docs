# Gateway Service Deployment Guide

## Prerequisites

### Development Environment

- Python 3.11+
- Docker and docker-compose
- Access to CORTX service registry
- PostgreSQL database (for session storage)

### Production Environment

- Kubernetes cluster (GKE recommended)
- Cloud SQL PostgreSQL instance
- Secret Manager for sensitive configuration
- Load balancer with SSL termination
- Monitoring infrastructure (Cloud Monitoring/Prometheus)

## Local Development Deployment

### 1. Install Dependencies

```bash
cd /Users/michael/Development/sinergysolutionsllc/services/gateway

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```bash
# Core configuration
CORTX_ENV=dev
LOG_LEVEL=DEBUG

# Service URLs
CORTX_REGISTRY_URL=http://localhost:8081
CORTX_IDENTITY_URL=http://localhost:8082
CORTX_VALIDATION_URL=http://localhost:8083
CORTX_RAG_URL=http://localhost:8138

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Auth (optional for dev)
REQUIRE_AUTH=false
```

### 3. Run Service

```bash
# Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Or using the dev helper script
python app/dev_main.py
```

### 4. Verify Health

```bash
curl http://localhost:8080/health
# Expected: {"status": "healthy", "service": "gateway", ...}

curl http://localhost:8080/_info
# Expected: {"service": "gateway", "version": "...", "features": {...}}
```

## Docker Deployment

### 1. Build Image

```bash
# From repository root
docker build -f services/gateway/Dockerfile -t cortx-gateway:latest .
```

### 2. Run Container

```bash
docker run -d \
  --name cortx-gateway \
  -p 8080:8080 \
  -e CORTX_ENV=dev \
  -e CORTX_REGISTRY_URL=http://host.docker.internal:8081 \
  -e CORTX_IDENTITY_URL=http://host.docker.internal:8082 \
  -e CORTX_VALIDATION_URL=http://host.docker.internal:8083 \
  cortx-gateway:latest
```

### 3. View Logs

```bash
docker logs -f cortx-gateway
```

## Docker Compose Deployment

The gateway is included in the main `docker-compose.yml`:

```bash
# From repository root
docker-compose up gateway

# Or start all services
docker-compose up
```

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl create namespace cortx-platform
```

### 2. Create ConfigMap

```yaml
# k8s/gateway/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: gateway-config
  namespace: cortx-platform
data:
  CORTX_ENV: "production"
  LOG_LEVEL: "INFO"
  CORTX_REGISTRY_URL: "http://registry-service:8081"
  CORTX_IDENTITY_URL: "http://identity-service:8082"
  CORTX_VALIDATION_URL: "http://validation-service:8083"
  CORTX_RAG_URL: "http://rag-service:8138"
  ALLOWED_ORIGINS: "https://app.cortx.ai,https://designer.cortx.ai"
  REQUIRE_AUTH: "true"
```

Apply:

```bash
kubectl apply -f k8s/gateway/configmap.yaml
```

### 3. Create Secrets

```bash
# Create JWT secret
kubectl create secret generic gateway-secrets \
  --namespace=cortx-platform \
  --from-literal=jwt-secret='your-jwt-secret-here'
```

### 4. Create Deployment

```yaml
# k8s/gateway/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
  namespace: cortx-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gateway
  template:
    metadata:
      labels:
        app: gateway
    spec:
      containers:
      - name: gateway
        image: gcr.io/your-project/cortx-gateway:latest
        ports:
        - containerPort: 8080
          name: http
        envFrom:
        - configMapRef:
            name: gateway-config
        env:
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: gateway-secrets
              key: jwt-secret
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
```

Apply:

```bash
kubectl apply -f k8s/gateway/deployment.yaml
```

### 5. Create Service

```yaml
# k8s/gateway/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: gateway-service
  namespace: cortx-platform
spec:
  type: LoadBalancer
  selector:
    app: gateway
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
```

Apply:

```bash
kubectl apply -f k8s/gateway/service.yaml
```

### 6. Configure Ingress (Optional)

```yaml
# k8s/gateway/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: gateway-ingress
  namespace: cortx-platform
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.cortx.ai
    secretName: gateway-tls
  rules:
  - host: api.cortx.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: gateway-service
            port:
              number: 80
```

Apply:

```bash
kubectl apply -f k8s/gateway/ingress.yaml
```

## Google Cloud Run Deployment

### 1. Build and Push Image

```bash
# Configure gcloud
gcloud auth configure-docker

# Build for Cloud Run
docker build -f services/gateway/Dockerfile -t gcr.io/your-project/cortx-gateway:latest .

# Push to GCR
docker push gcr.io/your-project/cortx-gateway:latest
```

### 2. Deploy to Cloud Run

```bash
gcloud run deploy cortx-gateway \
  --image gcr.io/your-project/cortx-gateway:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --set-env-vars "CORTX_ENV=production" \
  --set-env-vars "LOG_LEVEL=INFO" \
  --set-env-vars "CORTX_REGISTRY_URL=https://registry.cortx.ai" \
  --set-env-vars "CORTX_IDENTITY_URL=https://identity.cortx.ai" \
  --set-secrets "JWT_SECRET=gateway-jwt-secret:latest"
```

## Environment-Specific Configurations

### Development

- `REQUIRE_AUTH=false` - Disable JWT for easier testing
- `LOG_LEVEL=DEBUG` - Verbose logging
- `ALLOWED_ORIGINS=*` - Permissive CORS

### Staging

- `REQUIRE_AUTH=true` - Enable authentication
- `LOG_LEVEL=INFO` - Standard logging
- `ALLOWED_ORIGINS=https://staging.cortx.ai` - Restricted CORS
- Cloud SQL connection
- Secret Manager integration

### Production

- `REQUIRE_AUTH=true` - Strict authentication
- `LOG_LEVEL=WARNING` - Minimal logging
- `ALLOWED_ORIGINS=https://app.cortx.ai` - Production domains only
- High availability (3+ replicas)
- Auto-scaling enabled
- Full monitoring and alerting
- Backup and disaster recovery

## Database Migration

The gateway service is stateless but may require database setup for session storage:

```bash
# Run migrations (if applicable)
python -m alembic upgrade head
```

## Health Check Verification

After deployment, verify all endpoints:

```bash
# Basic health
curl https://api.cortx.ai/health

# Service info
curl https://api.cortx.ai/_info

# Test validation endpoint (requires auth)
curl -X POST https://api.cortx.ai/jobs/validate?domain=test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input_data": {}}'
```

## Rollback Procedures

### Kubernetes

```bash
# View deployment history
kubectl rollout history deployment/gateway -n cortx-platform

# Rollback to previous version
kubectl rollout undo deployment/gateway -n cortx-platform

# Rollback to specific revision
kubectl rollout undo deployment/gateway --to-revision=2 -n cortx-platform
```

### Cloud Run

```bash
# List revisions
gcloud run revisions list --service cortx-gateway --region us-central1

# Route traffic to previous revision
gcloud run services update-traffic cortx-gateway \
  --to-revisions REVISION_NAME=100 \
  --region us-central1
```

## Monitoring Setup

### Cloud Monitoring

Create uptime checks:

```bash
gcloud monitoring uptime-checks create https-uptime-check \
  --display-name="Gateway Health Check" \
  --host-name=api.cortx.ai \
  --path=/health \
  --period=60
```

### Prometheus Metrics

The gateway exposes Prometheus metrics at `/metrics`:

```yaml
# prometheus-config.yaml
scrape_configs:
  - job_name: 'cortx-gateway'
    static_configs:
      - targets: ['gateway-service:8080']
    metrics_path: /metrics
```

## Scaling Guidelines

### Vertical Scaling

- Increase CPU/memory for higher throughput per instance
- Monitor resource utilization before scaling

### Horizontal Scaling

- Add more replicas for increased capacity
- Configure auto-scaling based on CPU/memory/request rate

```yaml
# HPA example
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gateway-hpa
  namespace: cortx-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gateway
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Security Hardening

### Production Checklist

- [ ] JWT secrets stored in Secret Manager
- [ ] HTTPS only (no HTTP)
- [ ] Rate limiting enabled
- [ ] CORS restricted to production domains
- [ ] Audit logging enabled
- [ ] Network policies configured
- [ ] Container runs as non-root user
- [ ] Image scanning enabled
- [ ] Secrets rotation configured
- [ ] Backup and recovery tested
