# CORTX OCR Service - Functional Design Document

**Version**: 1.0.0
**Last Updated**: 2025-10-08
**Status**: Active

## 1. Purpose and Scope

### 1.1 Purpose

Provides intelligent document text extraction using a three-tier approach that automatically escalates from fast/cheap Tesseract OCR to high-accuracy Claude Vision to guaranteed-accuracy human review based on confidence scores.

### 1.2 Scope

- Document text extraction (images, PDFs)
- Multi-tier OCR pipeline
- Confidence-based tier escalation
- Structured field extraction
- Hash-based result caching
- Background job processing
- Human review workflow

### 1.3 Out of Scope

- Document classification (future)
- Handwriting recognition (delegated to Claude)
- Document comparison/diff
- Document generation

## 2. Key Features

### 2.1 Three-Tier OCR Pipeline

#### Tier 1: Tesseract OCR

- **Speed**: 100-300ms
- **Cost**: Free (open-source)
- **Accuracy**: 85-95% (modern printed documents)
- **Use Case**: Clear, modern documents
- **Threshold**: Confidence >= 80%

#### Tier 2: Claude 3.5 Sonnet Vision

- **Speed**: 2-5 seconds
- **Cost**: $0.003 per image
- **Accuracy**: 90-98% (handles historical, handwritten, degraded)
- **Use Case**: Complex documents, poor quality scans
- **Threshold**: Confidence >= 85%

#### Tier 3: Human Review

- **Speed**: Minutes (manual)
- **Cost**: High (human labor)
- **Accuracy**: 100%
- **Use Case**: Critical accuracy requirements
- **Threshold**: Always 100% confidence after review

### 2.2 Automatic Tier Escalation

```
Document → Tesseract
          ↓ (confidence < 80%)
          Claude AI
          ↓ (confidence < 85%)
          Human Review → 100% Accuracy
```

### 2.3 Hash-Based Caching

- SHA-256 hash of document content
- Cache hit = instant results
- Avoids reprocessing identical documents
- Hit counter for popular documents
- Configurable TTL

### 2.4 Structured Field Extraction

- Extract specific fields (name, date, amount, address)
- Configurable field templates
- Validation against expected formats
- Confidence per field

### 2.5 Multi-Page Support

- PDF splitting and per-page processing
- Combined results across pages
- Page-level confidence scores
- Progress tracking

## 3. API Contracts

### 3.1 Extract Text

```
POST /extract
Body:
  {
    "document_hash": "sha256...",
    "document_data": "base64...",
    "document_type": "image/png",
    "tenant_id": "string",
    "force_tier": "tesseract|ai_vision|human_review",  // optional
    "confidence_threshold": 80.0,  // optional
    "extract_fields": ["name", "date", "amount"]  // optional
  }
Response: 202 Accepted
  {
    "job_id": "uuid",
    "status": "pending",
    "tenant_id": "string",
    "created_at": "ISO8601"
  }
```

### 3.2 Get Job Status

```
GET /jobs/{job_id}
Response: 200 OK
  {
    "job_id": "uuid",
    "status": "completed",
    "extracted_text": "...",
    "extracted_fields": {
      "name": "John Doe",
      "date": "2025-01-15",
      "amount": 1500.00
    },
    "confidence_score": 95.5,
    "tier_used": "tesseract",
    "processing_time_ms": 250,
    "page_count": 1
  }
```

### 3.3 Submit Human Review

```
PUT /jobs/{job_id}/review
Body:
  {
    "reviewer_id": "reviewer@example.com",
    "corrected_text": "Corrected text...",
    "corrected_fields": {...},
    "review_notes": "Fixed OCR errors in header"
  }
Response: 200 OK
  {
    "job_id": "uuid",
    "status": "completed",
    "confidence_score": 100.0,
    "tier_used": "human_review"
  }
```

### 3.4 Cache Lookup

```
GET /cache/{document_hash}
Response: 200 OK
  {
    "cached": true,
    "extracted_text": "...",
    "confidence_score": 95.5,
    "tier_used": "tesseract",
    "hit_count": 5,
    "created_at": "ISO8601"
  }
```

## 4. Dependencies

### 4.1 Upstream

- **Tesseract OCR**: System package for text extraction
- **Anthropic API**: Claude 3.5 Sonnet for AI vision
- **PostgreSQL**: Job storage and caching

### 4.2 Downstream

- **Gateway**: Document processing workflows
- **Validation**: Document validation workflows
- **Workflow**: Multi-step document processing
- **Compliance**: Document audit trails

## 5. Data Models

### 5.1 OCR Job

```python
@dataclass
class OCRJob:
    id: UUID
    tenant_id: str
    document_hash: str
    status: Literal["pending", "processing_tesseract", "processing_ai",
                    "awaiting_review", "completed", "failed"]
    tier_used: Optional[Literal["tesseract", "ai_vision", "human_review"]]
    confidence_score: Optional[float]
    extracted_text: Optional[str]
    extracted_fields: Optional[dict]
    page_count: int
    processing_time_ms: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
```

### 5.2 OCR Cache Entry

```python
@dataclass
class OCRCacheEntry:
    document_hash: str
    extracted_text: str
    extracted_fields: dict
    confidence_score: float
    tier_used: str
    page_count: int
    processing_time_ms: int
    created_at: datetime
    last_accessed_at: datetime
    hit_count: int
```

### 5.3 Human Review

```python
@dataclass
class OCRReview:
    id: UUID
    job_id: UUID
    reviewer_id: str
    reviewed_at: datetime
    corrected_text: str
    corrected_fields: dict
    review_notes: str
    review_time_seconds: int
```

## 6. Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_URL` | postgresql://cortx:password@localhost:5432/cortx | Database connection |
| `ANTHROPIC_API_KEY` | None | Claude API key |
| `ANTHROPIC_MODEL` | claude-3-5-sonnet-20241022 | Claude model |
| `OCR_TESSERACT_THRESHOLD` | 80.0 | Tesseract confidence threshold |
| `OCR_AI_THRESHOLD` | 85.0 | AI confidence threshold |
| `CACHE_ENABLED` | true | Enable result caching |
| `CACHE_TTL_DAYS` | 90 | Cache expiration |

## 7. OCR Pipeline Details

### 7.1 Pre-Processing

- Deskew (straighten tilted images)
- Denoise (remove noise)
- Threshold (convert to black/white)
- Resolution check (ensure 300+ DPI)

### 7.2 Tesseract Processing

- Run Tesseract with best settings
- Extract confidence per word/line
- Calculate overall confidence
- If < threshold, escalate to AI

### 7.3 Claude AI Processing

- Convert image to base64
- Send to Claude 3.5 Sonnet Vision
- Parse structured response
- Extract confidence from response
- If < threshold, queue for human review

### 7.4 Human Review Queue

- Assign to reviewer
- Present original document + AI results
- Capture corrections
- Update job with 100% confidence

## 8. Performance Characteristics

### 8.1 Latency by Tier

| Tier | Typical | Max |
|------|---------|-----|
| Tesseract | 100-300ms | 1s |
| Claude AI | 2-5s | 10s |
| Human Review | Minutes | Hours |
| Cache Hit | < 50ms | 100ms |

### 8.2 Throughput

- 100 Tesseract jobs/second
- 20 Claude AI jobs/second
- 10 human reviews/hour
- 1000 cache lookups/second

### 8.3 Resource Requirements

- CPU: 2 cores baseline, 8 cores under load
- Memory: 1GB baseline, 4GB under load
- Storage: 100GB for job data

## 9. Cost Analysis

### 9.1 Cost Per Document

| Tier | Cost | Accuracy |
|------|------|----------|
| Tesseract | $0 | 85-95% |
| Claude AI | $0.003 | 90-98% |
| Human Review | $5-20 | 100% |
| Cache Hit | $0 | Previous result |

### 9.2 Cost Optimization

- Use caching aggressively
- Tune confidence thresholds
- Force Tesseract for known document types
- Batch similar documents

## 10. Monitoring

### 10.1 Metrics

- Jobs by tier (tesseract/ai/human)
- Average confidence per tier
- Cache hit rate
- Processing time per tier
- Cost per document
- Queue depth (human review)

### 10.2 Alerts

- Low confidence rate > 30%
- Human review queue > 100
- API quota exhaustion
- Processing time > thresholds

## 11. Future Enhancements

- Table extraction from documents
- Form recognition
- Document classification
- Multi-language support
- Batch processing UI
- Active learning from corrections

## 12. Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-08 | Initial FDD creation |
