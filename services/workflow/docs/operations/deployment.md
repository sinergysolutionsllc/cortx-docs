# Workflow Service Deployment Guide

## Local Development

```bash
cd services/workflow
pip install -e .
export DATABASE_URL="postgresql://cortx:password@localhost:5432/cortx"
uvicorn app.main:app --port 8130 --reload
```

## Docker

```bash
docker build -f services/workflow/Dockerfile -t cortx-workflow:latest .
docker run -d -p 8130:8130 \
  -e DATABASE_URL="postgresql://cortx:password@db:5432/cortx" \
  cortx-workflow:latest
```

## Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: workflow
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: workflow
        image: gcr.io/project/cortx-workflow:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: workflow-secrets
              key: database-url
        resources:
          requests:
            cpu: 1000m
            memory: 1Gi
```
