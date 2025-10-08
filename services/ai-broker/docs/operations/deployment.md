# AI Broker Service Deployment Guide

## Local Development

```bash
cd services/ai-broker

# Install dependencies
pip install -r requirements.txt

# Configure Vertex AI
export VERTEX_PROJECT_ID="your-gcp-project"
export VERTEX_LOCATION="us-central1"

# Optional: OpenAI/Anthropic
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Run service
uvicorn app.main:app --host 0.0.0.0 --port 8085 --reload
```

## Docker

```bash
docker build -f services/ai-broker/Dockerfile -t cortx-ai-broker:latest .

docker run -d \
  -p 8085:8085 \
  -e VERTEX_PROJECT_ID="your-project" \
  -e GOOGLE_APPLICATION_CREDENTIALS="/keys/service-account.json" \
  -v /path/to/keys:/keys \
  cortx-ai-broker:latest
```

## Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-broker
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: ai-broker
        image: gcr.io/project/cortx-ai-broker:latest
        env:
        - name: VERTEX_PROJECT_ID
          value: "your-project"
        - name: GOOGLE_APPLICATION_CREDENTIALS
          value: "/var/secrets/google/key.json"
        volumeMounts:
        - name: google-cloud-key
          mountPath: /var/secrets/google
      volumes:
      - name: google-cloud-key
        secret:
          secretName: ai-broker-gcp-key
```

## GCP Service Account Setup

```bash
# Create service account
gcloud iam service-accounts create ai-broker \
  --display-name="AI Broker Service Account"

# Grant Vertex AI permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:ai-broker@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create key.json \
  --iam-account=ai-broker@PROJECT_ID.iam.gserviceaccount.com
```
