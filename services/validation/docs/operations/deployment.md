# Validation Service Deployment Guide

## Local Development

```bash
cd services/validation
pip install -e .
export CORTX_RAG_URL=http://localhost:8138
export CORTX_COMPLIANCE_URL=http://localhost:8135
uvicorn app.main:app --port 8083 --reload
```

## Docker

```bash
docker build -f services/validation/Dockerfile -t cortx-validation:latest .
docker run -d -p 8083:8083 cortx-validation:latest
```

## Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: validation
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: validation
        image: gcr.io/project/cortx-validation:latest
        ports:
        - containerPort: 8083
        env:
        - name: CORTX_RAG_URL
          value: "http://rag-service:8138"
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
```
