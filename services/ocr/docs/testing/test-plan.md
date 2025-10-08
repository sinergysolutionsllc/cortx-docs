# OCR Service Test Plan

## Test Objectives

1. Verify OCR accuracy across all tiers
2. Test tier escalation logic
3. Validate caching behavior
4. Confirm field extraction accuracy
5. Measure performance targets

## Test Coverage

### Unit Tests (>80% coverage)

```python
# test_preprocessing.py
def test_deskew_image()
def test_denoise_image()
def test_threshold_image()
def test_image_resolution_check()

# test_tesseract.py
def test_tesseract_ocr_clear_document()
def test_tesseract_confidence_calculation()
def test_tesseract_multi_page()

# test_claude_ai.py
def test_claude_vision_api()
def test_claude_confidence_parsing()
def test_claude_error_handling()

# test_tier_escalation.py
def test_escalate_to_ai_on_low_confidence()
def test_escalate_to_human_on_very_low_confidence()
def test_no_escalation_on_high_confidence()

# test_caching.py
def test_cache_hit_returns_cached_result()
def test_cache_miss_processes_document()
def test_cache_hash_calculation()
def test_cache_hit_count_increment()

# test_field_extraction.py
def test_extract_name_field()
def test_extract_date_field()
def test_extract_amount_field()
def test_extract_custom_fields()
```

### Integration Tests

```python
# test_end_to_end.py
def test_complete_ocr_pipeline_tesseract()
def test_complete_ocr_pipeline_with_ai_escalation()
def test_complete_ocr_pipeline_with_human_review()

def test_multi_page_pdf_processing()
def test_batch_document_processing()

def test_cache_integration():
    """
    1. Process document (cache miss)
    2. Process same document (cache hit)
    3. Verify cache hit is faster
    """

def test_field_extraction_integration():
    """
    1. Upload form with known fields
    2. Extract fields
    3. Verify accuracy
    """
```

### Accuracy Tests

```python
# test_accuracy.py
def test_tesseract_accuracy_clear_docs():
    """Test Tesseract on 100 clear printed documents"""
    # Target: >90% accuracy

def test_claude_accuracy_complex_docs():
    """Test Claude on 50 handwritten/degraded documents"""
    # Target: >95% accuracy

def test_field_extraction_accuracy():
    """Test field extraction on 200 forms"""
    # Target: >85% per-field accuracy
```

### Performance Tests

```python
# test_performance.py
def test_tesseract_latency():
    """Verify Tesseract processing time < 1s"""

def test_claude_latency():
    """Verify Claude processing time < 10s"""

def test_cache_lookup_latency():
    """Verify cache lookup < 100ms"""

def test_concurrent_processing():
    """Process 100 documents concurrently"""
    # Target: All complete within 30s

def test_throughput():
    """Measure jobs/second"""
    # Target: 100 Tesseract jobs/sec
```

### Load Tests (Locust)

```python
# locustfile.py
from locust import HttpUser, task, between
import base64
import hashlib

class OCRUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def extract_cached_document(self):
        """Test cache hit performance"""
        # Use well-known document hash for cache hit
        response = self.client.get(f"/cache/{known_hash}")

    @task(2)
    def extract_new_document(self):
        """Test fresh OCR processing"""
        with open("test-doc.png", "rb") as f:
            data = base64.b64encode(f.read()).decode()
        doc_hash = hashlib.sha256(data.encode()).hexdigest()

        self.client.post("/extract", json={
            "document_hash": doc_hash,
            "document_data": data,
            "tenant_id": "load-test"
        })

    @task(1)
    def check_job_status(self):
        """Test job status queries"""
        self.client.get(f"/jobs/{recent_job_id}")
```

**Run load test:**

```bash
locust -f tests/performance/locustfile.py \
  --host http://localhost:8137 \
  --users 50 \
  --spawn-rate 10 \
  --run-time 5m
```

## Performance Targets

| Operation | Target | Acceptable | Notes |
|-----------|--------|------------|-------|
| Tesseract OCR | < 300ms | < 1s | Per page |
| Claude AI OCR | < 5s | < 10s | Per image |
| Human Review | < 24h | < 72h | SLA |
| Cache Lookup | < 50ms | < 100ms | Database query |
| Field Extraction | +100ms | +200ms | On top of OCR |

## Test Data Sets

### Clean Documents (Tesseract Target)

- Modern printed documents
- High DPI (300+)
- Good contrast
- No degradation

### Complex Documents (Claude AI Target)

- Historical documents
- Handwritten text
- Low quality scans
- Degraded/faded text

### Form Documents (Field Extraction)

- W-2 tax forms
- Invoices
- Government forms
- Custom business forms

## Continuous Integration

### GitHub Actions

```yaml
name: OCR Service Tests

on:
  push:
    paths:
      - 'services/ocr/**'
  pull_request:
    paths:
      - 'services/ocr/**'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s

    steps:
      - uses: actions/checkout@v3

      - name: Install Tesseract
        run: |
          sudo apt-get update
          sudo apt-get install -y tesseract-ocr tesseract-ocr-eng

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd services/ocr
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run unit tests
        run: |
          cd services/ocr
          pytest tests/unit/ --cov=app --cov-report=xml
        env:
          POSTGRES_URL: postgresql://postgres:postgres@localhost:5432/test
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY_TEST }}

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'

    steps:
      - uses: actions/checkout@v3

      - name: Start services
        run: docker-compose up -d ocr postgres

      - name: Wait for services
        run: |
          sleep 10
          curl --retry 10 --retry-delay 5 http://localhost:8137/health

      - name: Run integration tests
        run: |
          cd services/ocr
          pytest tests/integration/ -v
```

## Sign-off Criteria

Service is ready for production when:

- [ ] Unit test coverage > 80%
- [ ] All integration tests passing
- [ ] Accuracy tests meet targets (>90% Tesseract, >95% Claude)
- [ ] Performance tests meet targets
- [ ] Load tests demonstrate 100 jobs/sec
- [ ] Zero critical or high severity bugs
- [ ] Documentation complete
- [ ] Deployment tested in staging
- [ ] Cost analysis reviewed
- [ ] Human review workflow implemented
- [ ] Monitoring and alerts configured
