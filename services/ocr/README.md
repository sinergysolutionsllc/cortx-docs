# AI-Enhanced OCR Service

Multi-tier OCR pipeline with automatic escalation from Tesseract to Claude Vision to human review.

## Overview

The OCR service provides intelligent document text extraction using a three-tier approach:

1. **Tesseract OCR** - Fast, cost-effective OCR for modern, clear documents
2. **Claude 3.5 Sonnet Vision** - AI-powered OCR for historical, handwritten, or degraded documents
3. **Human Review** - 100% accuracy guarantee for critical documents

## Features

- **Automatic Tier Selection** - Service escalates to higher tiers based on confidence scores
- **Hash-based Caching** - Avoid reprocessing identical documents (SHA-256)
- **Multi-page Support** - Handles PDFs and multi-page documents
- **Structured Field Extraction** - Extract specific fields (name, date, amount, etc.)
- **Background Processing** - Async job processing with status polling
- **Comprehensive Preprocessing** - Deskew, denoise, threshold for better accuracy

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /extract (base64 doc)
       ▼
┌─────────────┐
│ Cache Check │◄──────────── SHA-256 hash
└──────┬──────┘
       │ Cache miss
       ▼
┌─────────────┐
│  Tesseract  │ Confidence >= 80%? ──► COMPLETED
└──────┬──────┘
       │ Confidence < 80%
       ▼
┌─────────────┐
│ Claude AI   │ Confidence >= 85%? ──► COMPLETED
└──────┬──────┘
       │ Confidence < 85%
       ▼
┌─────────────┐
│Human Review │ ──────────────────► COMPLETED (100%)
└─────────────┘
```

## API Endpoints

### Core OCR Operations

- `POST /extract` - Submit document for OCR
- `GET /jobs/{job_id}` - Get job status and results
- `PUT /jobs/{job_id}/review` - Submit human review corrections

### Cache & Stats

- `GET /cache/{document_hash}` - Check cache for existing results
- `GET /stats` - Service statistics (optionally by tenant)

### Health

- `GET /health` - Detailed health check
- `GET /healthz` - Liveness probe
- `GET /readyz` - Readiness probe

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Install Tesseract (macOS)
brew install tesseract

# Install Tesseract (Ubuntu/Debian)
apt-get install tesseract-ocr tesseract-ocr-eng

# Set environment variables
export POSTGRES_URL="postgresql://cortx:cortx_dev_password@localhost:5432/cortx"
export ANTHROPIC_API_KEY="your-api-key-here"
export OCR_TESSERACT_THRESHOLD="80.0"
export OCR_AI_THRESHOLD="85.0"

# Run service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8137 --reload
```

### Docker

```bash
# Build image
docker build -f services/ocr/Dockerfile -t ocr-service:latest .

# Run container
docker run -d \
  -p 8137:8137 \
  -e POSTGRES_URL="postgresql://cortx:cortx_dev_password@db:5432/cortx" \
  -e ANTHROPIC_API_KEY="your-api-key" \
  --name ocr-service \
  ocr-service:latest
```

## Usage Examples

### Extract Text from Image

```bash
# Prepare document
DOC_HASH=$(sha256sum document.png | cut -d' ' -f1)
DOC_DATA=$(base64 -w 0 document.png)

# Submit for OCR
curl -X POST http://localhost:8137/extract \
  -H "Content-Type: application/json" \
  -d '{
    "document_hash": "'$DOC_HASH'",
    "document_data": "'$DOC_DATA'",
    "document_type": "image/png",
    "tenant_id": "my-tenant"
  }'

# Response
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "tenant_id": "my-tenant",
  ...
}
```

### Check Job Status

```bash
curl http://localhost:8137/jobs/550e8400-e29b-41d4-a716-446655440000

# Response
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "extracted_text": "Sample document text...",
  "confidence_score": 95.5,
  "tier_used": "tesseract",
  "processing_time_ms": 250,
  ...
}
```

### Force Specific Tier

```bash
# Force AI tier for handwritten documents
curl -X POST http://localhost:8137/extract \
  -H "Content-Type: application/json" \
  -d '{
    "document_hash": "'$DOC_HASH'",
    "document_data": "'$DOC_DATA'",
    "force_tier": "ai_vision",
    "tenant_id": "my-tenant"
  }'
```

### Submit Human Review

```bash
curl -X PUT http://localhost:8137/jobs/550e8400-e29b-41d4-a716-446655440000/review \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer_id": "reviewer@example.com",
    "corrected_text": "Corrected document text",
    "review_notes": "Fixed OCR errors in header"
  }'
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_URL` | `postgresql://cortx:cortx_dev_password@localhost:5432/cortx` | Database connection string |
| `ANTHROPIC_API_KEY` | None | Anthropic API key for Claude Vision |
| `ANTHROPIC_MODEL` | `claude-3-5-sonnet-20241022` | Claude model to use |
| `OCR_TESSERACT_THRESHOLD` | `80.0` | Confidence threshold for Tesseract (0-100) |
| `OCR_AI_THRESHOLD` | `85.0` | Confidence threshold for AI tier (0-100) |

### Confidence Thresholds

- **Tesseract Threshold (80%)** - If Tesseract confidence is below this, escalate to AI tier
- **AI Threshold (85%)** - If AI confidence is below this, queue for human review
- **Custom Thresholds** - Can be overridden per-request via `confidence_threshold` parameter

## Database Schema

### OCR Jobs

Tracks all OCR extraction jobs with status, results, and audit trail.

```sql
CREATE TABLE ocr_jobs (
    id UUID PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    document_hash VARCHAR(64) NOT NULL,  -- SHA-256
    status VARCHAR(50) NOT NULL,         -- pending|processing_tesseract|processing_ai|awaiting_review|completed|failed
    tier_used VARCHAR(50),               -- tesseract|ai_vision|human_review
    confidence_score FLOAT,
    extracted_text TEXT,
    extracted_fields JSONB,
    page_count INT,
    processing_time_ms INT,
    tesseract_confidence FLOAT,
    ai_confidence FLOAT,
    warnings JSONB,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    user_id VARCHAR(255),
    correlation_id VARCHAR(255)
);
```

### OCR Reviews

Human review corrections and verification.

```sql
CREATE TABLE ocr_reviews (
    id UUID PRIMARY KEY,
    job_id UUID NOT NULL,
    reviewer_id VARCHAR(255) NOT NULL,
    reviewed_at TIMESTAMP NOT NULL,
    corrected_text TEXT,
    corrected_fields JSONB,
    review_notes TEXT,
    review_time_seconds INT,
    confidence_after_review FLOAT DEFAULT 100.0
);
```

### OCR Cache

Hash-based cache to avoid reprocessing.

```sql
CREATE TABLE ocr_cache (
    document_hash VARCHAR(64) PRIMARY KEY,  -- SHA-256
    extracted_text TEXT NOT NULL,
    extracted_fields JSONB NOT NULL,
    confidence_score FLOAT NOT NULL,
    tier_used VARCHAR(50) NOT NULL,
    document_type VARCHAR(255),
    page_count INT NOT NULL,
    processing_time_ms INT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    last_accessed_at TIMESTAMP NOT NULL,
    hit_count INT DEFAULT 0
);
```

## Performance

### Benchmarks (Typical)

| Tier | Speed | Cost | Accuracy | Use Case |
|------|-------|------|----------|----------|
| Tesseract | 100-300ms | Free | 85-95% | Modern printed documents |
| Claude AI | 2-5s | $0.003/image | 90-98% | Historical/handwritten docs |
| Human | Minutes | High | 100% | Critical accuracy required |

### Optimization Tips

1. **Enable Caching** - Documents with same hash skip reprocessing
2. **Batch Processing** - Submit multiple documents as separate jobs
3. **Set Thresholds** - Tune confidence thresholds for your use case
4. **Preprocess Images** - Higher quality inputs = better results
5. **Use Appropriate Tier** - Force tier for known document types

## Development

### Project Structure

```
services/ocr/
├── app/
│   ├── __init__.py          # Service metadata
│   ├── main.py              # FastAPI application
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── database.py          # Database configuration
│   └── processor.py         # OCR processing engine
├── requirements.txt         # Python dependencies
├── Dockerfile              # Multi-stage Docker build
├── .dockerignore           # Docker build exclusions
├── openapi.yaml            # OpenAPI 3.1 specification
└── README.md               # This file
```

### Testing

The service is designed to integrate with:

- PostgreSQL database at `localhost:5432`
- Anthropic API (requires API key)
- Tesseract OCR (system package)

For local testing without all dependencies:

- Service will start without Anthropic API (AI tier disabled)
- Database must be available for service to start
- Tesseract required for base functionality

## Integration

### With Other CORTX Services

The OCR service is designed to work with:

- **Gateway** - Routes requests through API gateway
- **Identity** - Authentication and authorization
- **Compliance** - Audit logging for OCR operations
- **Workflow** - Orchestrate multi-step document processing

### Client Libraries

```python
import requests
import hashlib
import base64

class OCRClient:
    def __init__(self, base_url="http://localhost:8137"):
        self.base_url = base_url

    def extract_text(self, file_path, tenant_id):
        # Read and hash document
        with open(file_path, 'rb') as f:
            data = f.read()

        doc_hash = hashlib.sha256(data).hexdigest()
        doc_data = base64.b64encode(data).decode()

        # Submit for OCR
        response = requests.post(
            f"{self.base_url}/extract",
            json={
                "document_hash": doc_hash,
                "document_data": doc_data,
                "tenant_id": tenant_id
            }
        )
        return response.json()

    def get_results(self, job_id):
        response = requests.get(f"{self.base_url}/jobs/{job_id}")
        return response.json()
```

## Troubleshooting

### Tesseract Not Found

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Verify installation
tesseract --version
```

### Low Confidence Scores

1. Check image quality (300+ DPI recommended)
2. Ensure proper contrast (black text on white background)
3. Try preprocessing with deskew/denoise
4. Force AI tier for complex documents

### Database Connection Errors

1. Verify PostgreSQL is running
2. Check connection string format
3. Ensure database `cortx` exists
4. Verify credentials (default: `cortx`/`cortx_dev_password`)

## License

Proprietary - Sinergy Solutions LLC

## Support

For issues or questions:

- GitHub Issues: [sinergysolutionsllc](https://github.com/sinergysolutionsllc)
- Email: <support@sinergysolutionsllc.com>
