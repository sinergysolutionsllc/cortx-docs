# OCR Service Deployment Guide

See [../QUICKSTART.md](../QUICKSTART.md) for detailed setup instructions.

## Local Development

```bash
cd services/ocr

# Install dependencies
pip install -r requirements.txt

# Install Tesseract
# macOS
brew install tesseract

# Ubuntu/Debian
apt-get install tesseract-ocr tesseract-ocr-eng

# Set environment variables
export POSTGRES_URL="postgresql://cortx:cortx_dev_password@localhost:5432/cortx"
export ANTHROPIC_API_KEY="your-api-key-here"
export OCR_TESSERACT_THRESHOLD="80.0"
export OCR_AI_THRESHOLD="85.0"

# Run service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8137 --reload
```

## Docker

```bash
# Build image (includes Tesseract)
docker build -f services/ocr/Dockerfile -t ocr-service:latest .

# Run container
docker run -d \
  -p 8137:8137 \
  -e POSTGRES_URL="postgresql://cortx:cortx_dev_password@db:5432/cortx" \
  -e ANTHROPIC_API_KEY="your-api-key" \
  --name ocr-service \
  ocr-service:latest
```

## Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ocr
  namespace: cortx-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ocr
  template:
    metadata:
      labels:
        app: ocr
    spec:
      containers:
      - name: ocr
        image: gcr.io/your-project/cortx-ocr:latest
        ports:
        - containerPort: 8137
        env:
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: ocr-secrets
              key: postgres-url
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: ocr-secrets
              key: anthropic-api-key
        - name: OCR_TESSERACT_THRESHOLD
          value: "80.0"
        - name: OCR_AI_THRESHOLD
          value: "85.0"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8137
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8137
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            cpu: 2000m
            memory: 2Gi
          limits:
            cpu: 4000m
            memory: 4Gi
---
apiVersion: v1
kind: Service
metadata:
  name: ocr-service
  namespace: cortx-platform
spec:
  selector:
    app: ocr
  ports:
  - port: 8137
    targetPort: 8137
    protocol: TCP
```

## Database Setup

```sql
-- See database schema in ../README.md lines 199-262
-- Tables: ocr_jobs, ocr_reviews, ocr_cache
```

## Environment-Specific Configuration

### Development

- Tesseract only (disable AI to save costs)
- Low confidence thresholds
- No caching TTL
- Verbose logging

### Staging

- Enable Claude AI
- Standard thresholds (80/85)
- Cache TTL: 30 days
- Standard logging

### Production

- Full pipeline enabled
- Strict thresholds (85/90 for critical docs)
- Cache TTL: 90 days
- Minimal logging (PII concerns)
- Monitoring and alerts enabled
