# RAG Service Deployment

## Local Development

```bash
cd services/rag
pip install -r requirements.txt

# PostgreSQL with pgvector extension required
export DATABASE_URL="postgresql://cortx:password@localhost:5432/cortx"
export AI_BROKER_URL="http://localhost:8085"

uvicorn app.main:app --port 8138 --reload
```

## PostgreSQL Setup with pgvector

```sql
CREATE EXTENSION vector;

CREATE TABLE chunks (
    chunk_id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),  -- 768 dimensions for gecko embeddings
    metadata JSONB
);

CREATE INDEX ON chunks USING ivfflat (embedding vector_cosine_ops);
```

## Docker

```bash
docker build -f services/rag/Dockerfile -t cortx-rag:latest .
docker run -d -p 8138:8138 \
  -e DATABASE_URL="postgresql://cortx:password@db:5432/cortx" \
  -e AI_BROKER_URL="http://ai-broker:8085" \
  cortx-rag:latest
```

## Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: rag
        image: gcr.io/project/cortx-rag:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: database-url
        resources:
          requests:
            cpu: 2000m
            memory: 4Gi
```
