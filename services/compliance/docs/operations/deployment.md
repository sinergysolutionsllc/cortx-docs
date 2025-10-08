# Compliance Service Deployment

## Local Development

```bash
cd services/compliance
pip install -r requirements.txt
export DATABASE_URL="postgresql://cortx:password@localhost:5432/cortx"
export LEDGER_URL="http://localhost:8136"
uvicorn app.main:app --port 8135 --reload
```

## Docker

```bash
docker build -f services/compliance/Dockerfile -t cortx-compliance:latest .
docker run -d -p 8135:8135 \
  -e DATABASE_URL="postgresql://cortx:password@db:5432/cortx" \
  -e LEDGER_URL="http://ledger:8136" \
  cortx-compliance:latest
```

## Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: compliance
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: compliance
        image: gcr.io/project/cortx-compliance:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: compliance-secrets
              key: database-url
        - name: LEDGER_URL
          value: "http://ledger-service:8136"
```
