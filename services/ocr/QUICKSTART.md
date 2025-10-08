# OCR Service - Quick Start Guide

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ (running on localhost:5432)
- Tesseract OCR installed
- (Optional) Anthropic API key for AI tier

## 1. Install System Dependencies

### macOS

```bash
brew install tesseract poppler
```

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils
```

### Verify Installation

```bash
tesseract --version
# Should output: tesseract 5.x.x
```

## 2. Install Python Dependencies

```bash
cd /Users/michael/Development/sinergysolutionsllc/services/ocr
pip install -r requirements.txt
```

## 3. Configure Environment

Create a `.env` file (or export variables):

```bash
# Required
export POSTGRES_URL="postgresql://cortx:cortx_dev_password@localhost:5432/cortx"

# Optional (for AI tier)
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Optional (tune confidence thresholds)
export OCR_TESSERACT_THRESHOLD="80.0"
export OCR_AI_THRESHOLD="85.0"
```

## 4. Initialize Database

The service will automatically create tables on startup, but you can verify the database is accessible:

```bash
psql postgresql://cortx:cortx_dev_password@localhost:5432/cortx -c "SELECT version();"
```

## 5. Start the Service

```bash
cd /Users/michael/Development/sinergysolutionsllc/services/ocr
python -m uvicorn app.main:app --host 0.0.0.0 --port 8137 --reload
```

You should see:

```
INFO:     Will watch for changes in these directories: ['/path/to/ocr']
INFO:     Uvicorn running on http://0.0.0.0:8137 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     OCR service starting up...
INFO:     Database initialized successfully
INFO:     Tesseract OCR is available
INFO:     Anthropic API configured: True
INFO:     Application startup complete.
```

## 6. Test the Service

### Check Health

```bash
curl http://localhost:8137/health | jq
```

Expected response:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "tesseract_available": true,
  "anthropic_api_available": true,
  "database_connected": true
}
```

### Submit a Test Document

Create a simple test image:

```bash
# Create a test PNG with text
convert -size 400x100 xc:white -pointsize 20 -draw "text 20,50 'Hello OCR World'" test.png
```

Or use Python to create a test image:

```python
from PIL import Image, ImageDraw, ImageFont
import base64
import hashlib

# Create test image
img = Image.new('RGB', (400, 100), color='white')
draw = ImageDraw.Draw(img)
draw.text((20, 40), "Hello OCR World", fill='black')
img.save('test.png')

# Prepare for API
with open('test.png', 'rb') as f:
    data = f.read()

doc_hash = hashlib.sha256(data).hexdigest()
doc_data = base64.b64encode(data).decode()

print(f"Document Hash: {doc_hash}")
print(f"Document Data (truncated): {doc_data[:50]}...")
```

Submit via curl:

```bash
DOC_HASH=$(sha256sum test.png | cut -d' ' -f1)
DOC_DATA=$(base64 -w 0 test.png)

curl -X POST http://localhost:8137/extract \
  -H "Content-Type: application/json" \
  -d "{
    \"document_hash\": \"$DOC_HASH\",
    \"document_data\": \"$DOC_DATA\",
    \"document_type\": \"image/png\",
    \"tenant_id\": \"test-tenant\"
  }" | jq
```

Expected response:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_id": "test-tenant",
  "status": "pending",
  "document_hash": "abc123...",
  "created_at": "2025-10-07T12:00:00Z",
  "updated_at": "2025-10-07T12:00:00Z"
}
```

### Check Job Status

```bash
JOB_ID="550e8400-e29b-41d4-a716-446655440000"  # Use actual job_id from previous response

curl http://localhost:8137/jobs/$JOB_ID | jq
```

Expected response (when complete):

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_id": "test-tenant",
  "status": "completed",
  "document_hash": "abc123...",
  "tier_used": "tesseract",
  "confidence_score": 95.5,
  "extracted_text": "Hello OCR World",
  "page_count": 1,
  "processing_time_ms": 250,
  "created_at": "2025-10-07T12:00:00Z",
  "updated_at": "2025-10-07T12:00:01Z"
}
```

## 7. Test AI Tier (Optional)

If you have an Anthropic API key configured:

```bash
# Force AI tier processing
curl -X POST http://localhost:8137/extract \
  -H "Content-Type: application/json" \
  -d "{
    \"document_hash\": \"$DOC_HASH\",
    \"document_data\": \"$DOC_DATA\",
    \"force_tier\": \"ai_vision\",
    \"tenant_id\": \"test-tenant\"
  }" | jq
```

## 8. View Service Statistics

```bash
curl http://localhost:8137/stats | jq
```

Expected response:

```json
{
  "total_jobs": 2,
  "jobs_by_status": {
    "completed": 2
  },
  "jobs_by_tier": {
    "tesseract": 1,
    "ai_vision": 1
  },
  "average_confidence": 95.5,
  "average_processing_time_ms": 350.0,
  "cache_hit_rate": 0.0
}
```

## 9. Access API Documentation

Open your browser to:

- **Interactive Docs**: <http://localhost:8137/docs>
- **ReDoc**: <http://localhost:8137/redoc>
- **OpenAPI Spec**: <http://localhost:8137/openapi.json>

## Common Issues

### "ModuleNotFoundError: No module named 'PIL'"

```bash
pip install Pillow
```

### "Tesseract not found"

```bash
# macOS
brew install tesseract

# Ubuntu
sudo apt-get install tesseract-ocr
```

### "Database connection failed"

```bash
# Verify PostgreSQL is running
pg_isready -h localhost -p 5432

# Create database if needed
createdb cortx
```

### "Anthropic API error"

```bash
# Verify API key is set
echo $ANTHROPIC_API_KEY

# Service will work without it (Tesseract only)
# AI tier will be unavailable but service remains functional
```

## Development Workflow

### Run with Auto-Reload

```bash
python -m uvicorn app.main:app --reload --port 8137
```

### Run Tests (when implemented)

```bash
pytest
```

### Check Code Quality

```bash
# Format code
black app/

# Lint code
ruff check app/

# Type check
mypy app/
```

## Docker Quick Start

### Build Image

```bash
cd /Users/michael/Development/sinergysolutionsllc
docker build -f services/ocr/Dockerfile -t ocr-service:latest .
```

### Run Container

```bash
docker run -d \
  -p 8137:8137 \
  -e POSTGRES_URL="postgresql://cortx:cortx_dev_password@host.docker.internal:5432/cortx" \
  -e ANTHROPIC_API_KEY="sk-ant-xxx" \
  --name ocr-service \
  ocr-service:latest
```

### View Logs

```bash
docker logs -f ocr-service
```

### Stop Container

```bash
docker stop ocr-service
docker rm ocr-service
```

## Next Steps

1. Explore the full API documentation at `/docs`
2. Test with your own documents (PDFs, images)
3. Tune confidence thresholds for your use case
4. Integrate with other CORTX services
5. Set up monitoring and alerting

## Support

For issues or questions:

- Check the README.md for detailed documentation
- Review IMPLEMENTATION_SUMMARY.md for architecture details
- GitHub: <https://github.com/sinergysolutionsllc>
- Email: <support@sinergysolutionsllc.com>
