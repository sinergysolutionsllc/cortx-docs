# OCR Service (Port 8137)

**Status:** ✅ Implemented | **Version:** 1.0.0

## Overview

The OCR service provides AI-enhanced optical character recognition for the CORTX platform, extracting structured data and text from scanned documents, PDFs, and images using a multi-tier processing pipeline.

## Multi-Tier OCR Pipeline

### Tier 1: Tesseract OCR (Free, Fast)

- **Use Case:** Modern, clear documents with printed text
- **Speed:** 100-300ms per page
- **Accuracy:** 85-95% on clean documents
- **Cost:** Free
- **Confidence Threshold:** 80%

### Tier 2: Claude 3.5 Sonnet Vision (AI-Enhanced)

- **Use Case:** Historical documents, handwritten text, complex layouts
- **Speed:** 2-5 seconds per page
- **Accuracy:** 90-98% on complex documents
- **Cost:** ~$0.003 per image
- **Confidence Threshold:** 85%
- **Requires:** `ANTHROPIC_API_KEY` environment variable

### Tier 3: Human Review (Manual, 100% Accuracy)

- **Use Case:** Critical documents requiring perfect accuracy
- **Process:** Documents below AI threshold flagged for human review
- **Result:** Corrections stored and used to improve future processing

## Auto-Escalation Logic

```
Document → Cache Check → Tesseract
                            ↓ (if confidence < 80%)
                         Claude Vision
                            ↓ (if confidence < 85%)
                      Awaiting Human Review
                            ↓
                        Completed
```

## Key Features

### Smart Caching

- **SHA-256 hashing** prevents reprocessing identical documents
- **Hit count tracking** identifies frequently processed documents
- **Automatic cache invalidation** based on access patterns

### Document Preprocessing

- Adaptive thresholding for low-quality scans
- Denoising with OpenCV
- Automatic deskewing
- Multi-page PDF support

### Job Tracking

- Asynchronous background processing
- Real-time status updates
- Comprehensive audit trail
- Error logging and diagnostics

### Structured Data Extraction

- Raw text extraction
- Field mapping to JSON schema
- Confidence scores per field
- Multi-language support (Tesseract)

## API Endpoints

### Health & Status

- `GET /` - Service information
- `GET /health` - Detailed health check (Tesseract, Claude, DB)
- `GET /healthz` - Kubernetes liveness probe
- `GET /readyz` - Kubernetes readiness probe
- `GET /stats` - Service statistics (jobs, cache hits, tier usage)

### OCR Processing

- `POST /extract` - Submit document for OCR
  - Multipart file upload
  - Optional tier selection
  - Confidence threshold override
- `GET /jobs/{job_id}` - Get job status and results
- `PUT /jobs/{job_id}/review` - Submit human review corrections

### Caching

- `GET /cache/{document_hash}` - Check for cached results

## Database Schema

### OCR Jobs (`ocr_jobs`)

- Job tracking with status progression
- Multi-tenant isolation
- Processing metadata (time, tier used, confidence)
- Extracted text and structured fields
- Error logging

### OCR Reviews (`ocr_reviews`)

- Human review corrections
- Reviewer tracking
- Review time and confidence
- Training data for ML improvement

### OCR Cache (`ocr_cache`)

- Document hash-based lookup
- Tier and confidence tracking
- Hit count analytics
- Last accessed timestamp

## Configuration

### Environment Variables

```bash
# Database (required)
POSTGRES_URL=postgresql://cortx:cortx_dev_password@localhost:5432/cortx

# Anthropic API (optional, enables Claude Vision tier)
ANTHROPIC_API_KEY=sk-ant-xxx
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Confidence Thresholds
OCR_TESSERACT_THRESHOLD=80.0
OCR_AI_THRESHOLD=85.0

# Service
PORT=8137
LOG_LEVEL=INFO
```

### System Dependencies

```bash
# macOS
brew install tesseract poppler

# Ubuntu/Debian
apt-get install tesseract-ocr poppler-utils

# Python packages (see requirements.txt)
pip install -r requirements.txt
```

## Usage Examples

### Submit Document for OCR

```bash
curl -X POST http://localhost:8137/extract \
  -H "X-Tenant-ID: tenant-123" \
  -F "file=@invoice.pdf" \
  -F "tier=tesseract" \
  -F "confidence_threshold=75.0"
```

### Check Job Status

```bash
curl http://localhost:8137/jobs/{job_id} \
  -H "X-Tenant-ID: tenant-123"
```

### Submit Human Review

```bash
curl -X PUT http://localhost:8137/jobs/{job_id}/review \
  -H "X-Tenant-ID: tenant-123" \
  -H "Content-Type: application/json" \
  -d '{
    "corrected_text": "Corrected invoice text...",
    "corrected_fields": {"invoice_number": "INV-2024-001"},
    "reviewer_id": "user-456"
  }'
```

### Check Cache

```bash
curl http://localhost:8137/cache/{sha256_hash} \
  -H "X-Tenant-ID: tenant-123"
```

## Integration

### Gateway Routes

The Gateway service proxies OCR requests:

```
POST /api/v1/ocr/extract → http://ocr:8137/extract
GET  /api/v1/ocr/jobs/:id → http://ocr:8137/jobs/:id
```

### RAG Integration

OCR-extracted text can be ingested into the RAG service for document search and retrieval.

### Compliance Integration

OCR job metadata logged to Ledger service for audit compliance.

## Performance

### Throughput

- **Tesseract:** ~10-20 pages/second (parallel processing)
- **Claude Vision:** ~15-30 pages/minute (API rate limits)
- **Cache Hit:** <10ms response time

### Scalability

- Horizontal scaling via multiple service instances
- Database connection pooling (10 connections, 20 overflow)
- Background async processing with task queues

## Architecture Diagram

```mermaid
flowchart TB
    Gateway[Gateway Service] -->|POST /api/v1/ocr/extract| OCR[OCR Service]
    OCR -->|1. Check Cache| Cache[(OCR Cache)]
    Cache -->|Cache Miss| Processor[OCR Processor]
    Processor -->|2. Tesseract| Tesseract[Tesseract OCR]
    Processor -->|3. If Low Confidence| Claude[Claude 3.5 Sonnet Vision]
    Processor -->|4. If Still Low| Review[Human Review Queue]
    OCR -->|Store Results| DB[(PostgreSQL)]
    OCR -->|Log Events| Ledger[Ledger Service]
    OCR -->|Index Text| RAG[RAG Service]
```

## Monitoring & Logging

### Health Checks

- Database connectivity
- Tesseract availability
- Anthropic API status

### Metrics

- Jobs processed by tier
- Average confidence scores
- Cache hit rate
- Processing time per tier
- Error rates

### Logging

- Structured JSON logs
- Request correlation IDs
- Error stack traces
- Performance metrics

## Security

### Multi-Tenancy

- Tenant-scoped job queries
- Row-level security on database
- Tenant ID validation on all endpoints

### Data Protection

- Document hashing for deduplication
- PII/PHI redaction support
- Secure file handling (temp file cleanup)

## Error Handling

### Automatic Retry

- Network failures: 3 retries with exponential backoff
- API rate limits: Queue-based retry
- Tesseract errors: Auto-escalate to AI tier

### Degraded Mode

- Tesseract unavailable: Skip to Claude Vision
- Claude API unavailable: Flag for human review
- Database down: Return 503 with retry-after header

## Development

### Local Setup

```bash
cd /Users/michael/Development/sinergysolutionsllc/services/ocr
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8137 --reload
```

### Docker

```bash
docker build -f services/ocr/Dockerfile -t cortx-ocr:1.0.0 .
docker run -p 8137:8137 \
  -e POSTGRES_URL="postgresql://..." \
  -e ANTHROPIC_API_KEY="sk-ant-xxx" \
  cortx-ocr:1.0.0
```

## Documentation

- **OpenAPI Spec:** [openapi.yaml](./openapi.yaml)
- **Implementation Details:** `/services/ocr/IMPLEMENTATION_SUMMARY.md`
- **Quick Start:** `/services/ocr/QUICKSTART.md`
- **Source Code:** `/services/ocr/app/`

## Support

For issues or questions:

- GitHub Issues: [sinergysolutionsllc/sinergysolutionsllc](https://github.com/sinergysolutionsllc/sinergysolutionsllc/issues)
- Internal Documentation: `/docs/services/ocr/`
