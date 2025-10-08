# Ledger Service Deployment

## Local Development

```bash
cd services/ledger
pip install -r requirements.txt
export DATABASE_URL="postgresql://cortx:password@localhost:5432/cortx"
uvicorn app.main:app --port 8136 --reload
```

## Database Schema

```sql
CREATE TABLE ledger_entries (
    entry_id UUID PRIMARY KEY,
    index BIGINT UNIQUE NOT NULL,
    data JSONB NOT NULL,
    metadata JSONB,
    entry_hash VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ledger_index ON ledger_entries(index);
CREATE INDEX idx_ledger_timestamp ON ledger_entries(timestamp);
CREATE INDEX idx_ledger_metadata ON ledger_entries USING gin(metadata);
```

## Docker

```bash
docker build -f services/ledger/Dockerfile -t cortx-ledger:latest .
docker run -d -p 8136:8136 \
  -e DATABASE_URL="postgresql://cortx:password@db:5432/cortx" \
  cortx-ledger:latest
```

## Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ledger
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: ledger
        image: gcr.io/project/cortx-ledger:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ledger-secrets
              key: database-url
        resources:
          requests:
            cpu: 1000m
            memory: 1Gi
```
