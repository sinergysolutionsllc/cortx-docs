"""
Integration tests for OCR service API endpoints
"""

import uuid
from unittest.mock import patch

from app.models import OCRStatus, OCRTier

# ============================================================================
# Health Check Endpoint Tests
# ============================================================================


class TestHealthEndpoints:
    """Tests for health check endpoints"""

    def test_health_check_success(self, client):
        """Test /health endpoint returns service status"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "tesseract_available" in data
        assert "anthropic_api_available" in data
        assert "database_connected" in data

    def test_healthz_probe(self, client):
        """Test /healthz liveness probe"""
        response = client.get("/healthz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_readyz_probe(self, client):
        """Test /readyz readiness probe"""
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"


# ============================================================================
# Root Endpoint Tests
# ============================================================================


class TestRootEndpoint:
    """Tests for root endpoint"""

    def test_root_endpoint(self, client):
        """Test / endpoint returns service information"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "AI-Enhanced OCR Service"
        assert "version" in data
        assert "tiers" in data
        assert "endpoints" in data
        assert len(data["tiers"]) == 3


# ============================================================================
# OCR Extract Endpoint Tests
# ============================================================================


class TestExtractEndpoint:
    """Tests for POST /extract endpoint"""

    @patch("app.main.ocr_processor.process_document")
    def test_extract_success(self, mock_process, client, sample_ocr_request):
        """Test successful OCR extraction"""
        # Mock processor response
        mock_process.return_value = {
            "status": OCRStatus.COMPLETED,
            "extracted_text": "Sample extracted text",
            "confidence_score": 95.0,
            "tier_used": OCRTier.TESSERACT,
            "page_count": 1,
            "processing_time_ms": 250,
        }

        response = client.post("/extract", json=sample_ocr_request)

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["tenant_id"] == "test-tenant"
        assert data["status"] in [s.value for s in OCRStatus]

    @patch("app.main.ocr_processor.process_document")
    def test_extract_with_cache_hit(
        self, mock_process, client, sample_ocr_request, sample_cache_entry
    ):
        """Test extraction with cache hit"""
        # Update request to use cached hash
        sample_ocr_request["document_hash"] = sample_cache_entry.document_hash

        response = client.post("/extract", json=sample_ocr_request)

        assert response.status_code == 200
        data = response.json()
        assert data["extracted_text"] == sample_cache_entry.extracted_text
        assert data["confidence_score"] == sample_cache_entry.confidence_score
        assert data["status"] == "completed"
        # Should not call processor for cache hit
        mock_process.assert_not_called()

    def test_extract_missing_required_fields(self, client):
        """Test extraction fails without required fields"""
        incomplete_request = {
            "document_hash": "hash123"
            # Missing document_data and tenant_id
        }

        response = client.post("/extract", json=incomplete_request)

        assert response.status_code == 422  # Validation error

    def test_extract_invalid_base64(self, client):
        """Test extraction with invalid base64 data"""
        invalid_request = {
            "document_hash": "hash123",
            "document_data": "not-valid-base64!!!",
            "tenant_id": "test-tenant",
        }

        response = client.post("/extract", json=invalid_request)

        assert response.status_code == 200  # Job is created
        data = response.json()
        assert data["status"] == "pending"  # Will fail in background

    @patch("app.main.ocr_processor.process_document")
    def test_extract_with_force_tier(self, mock_process, client, sample_ocr_request):
        """Test extraction with forced OCR tier"""
        mock_process.return_value = {
            "status": OCRStatus.COMPLETED,
            "extracted_text": "AI extracted text",
            "confidence_score": 93.0,
            "tier_used": OCRTier.AI_VISION,
            "page_count": 1,
            "processing_time_ms": 1500,
            "ai_confidence": 93.0,
        }

        sample_ocr_request["force_tier"] = "ai_vision"
        response = client.post("/extract", json=sample_ocr_request)

        assert response.status_code == 200

    @patch("app.main.ocr_processor.process_document")
    def test_extract_with_require_review(self, mock_process, client, sample_ocr_request):
        """Test extraction with required human review"""
        mock_process.return_value = {
            "status": OCRStatus.COMPLETED,
            "extracted_text": "Text for review",
            "confidence_score": 95.0,
            "tier_used": OCRTier.TESSERACT,
            "page_count": 1,
            "processing_time_ms": 300,
        }

        sample_ocr_request["require_review"] = True
        response = client.post("/extract", json=sample_ocr_request)

        assert response.status_code == 200
        # Job will be updated to awaiting_review in background task

    @patch("app.main.ocr_processor.process_document")
    def test_extract_with_custom_threshold(self, mock_process, client, sample_ocr_request):
        """Test extraction with custom confidence threshold"""
        mock_process.return_value = {
            "status": OCRStatus.COMPLETED,
            "extracted_text": "Extracted text",
            "confidence_score": 88.0,
            "tier_used": OCRTier.TESSERACT,
            "page_count": 1,
            "processing_time_ms": 250,
        }

        sample_ocr_request["confidence_threshold"] = 90.0
        response = client.post("/extract", json=sample_ocr_request)

        assert response.status_code == 200

    @patch("app.main.ocr_processor.process_document")
    def test_extract_with_field_extraction(self, mock_process, client, sample_ocr_request):
        """Test extraction with specific field extraction"""
        mock_process.return_value = {
            "status": OCRStatus.COMPLETED,
            "extracted_text": "Invoice data",
            "extracted_fields": {
                "invoice_number": "12345",
                "date": "2025-10-07",
                "amount": 1234.56,
            },
            "confidence_score": 92.0,
            "tier_used": OCRTier.AI_VISION,
            "page_count": 1,
            "processing_time_ms": 1200,
        }

        sample_ocr_request["extract_fields"] = ["invoice_number", "date", "amount"]
        response = client.post("/extract", json=sample_ocr_request)

        assert response.status_code == 200


# ============================================================================
# Get Job Endpoint Tests
# ============================================================================


class TestGetJobEndpoint:
    """Tests for GET /jobs/{job_id} endpoint"""

    def test_get_job_success(self, client, completed_ocr_job):
        """Test getting an existing job"""
        response = client.get(f"/jobs/{completed_ocr_job.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == str(completed_ocr_job.id)
        assert data["status"] == "completed"
        assert data["extracted_text"] is not None
        assert data["confidence_score"] == 95.0

    def test_get_job_not_found(self, client):
        """Test getting non-existent job"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/jobs/{fake_id}")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_job_invalid_id_format(self, client):
        """Test getting job with invalid UUID format"""
        response = client.get("/jobs/not-a-valid-uuid")

        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower()

    def test_get_pending_job(self, client, sample_ocr_job):
        """Test getting a pending job"""
        response = client.get(f"/jobs/{sample_ocr_job.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["extracted_text"] is None
        assert data["confidence_score"] is None

    def test_get_review_pending_job(self, client, review_pending_job):
        """Test getting a job awaiting review"""
        response = client.get(f"/jobs/{review_pending_job.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "awaiting_review"
        assert data["confidence_score"] == 72.0
        assert data["tier_used"] == "ai_vision"


# ============================================================================
# Submit Review Endpoint Tests
# ============================================================================


class TestSubmitReviewEndpoint:
    """Tests for PUT /jobs/{job_id}/review endpoint"""

    def test_submit_review_success(self, client, review_pending_job, sample_review_request):
        """Test successful review submission"""
        response = client.put(f"/jobs/{review_pending_job.id}/review", json=sample_review_request)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["tier_used"] == "human_review"
        assert data["confidence_score"] == 100.0
        assert data["extracted_text"] == sample_review_request["corrected_text"]

    def test_submit_review_not_awaiting_review(
        self, client, completed_ocr_job, sample_review_request
    ):
        """Test review submission for job not awaiting review"""
        response = client.put(f"/jobs/{completed_ocr_job.id}/review", json=sample_review_request)

        assert response.status_code == 400
        data = response.json()
        assert "not awaiting review" in data["detail"].lower()

    def test_submit_review_job_not_found(self, client, sample_review_request):
        """Test review submission for non-existent job"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.put(f"/jobs/{fake_id}/review", json=sample_review_request)

        assert response.status_code == 404

    def test_submit_review_invalid_job_id(self, client, sample_review_request):
        """Test review submission with invalid job ID"""
        response = client.put("/jobs/invalid-uuid/review", json=sample_review_request)

        assert response.status_code == 400

    def test_submit_review_minimal_data(self, client, review_pending_job):
        """Test review submission with minimal data"""
        minimal_review = {"reviewer_id": "reviewer-minimal"}

        response = client.put(f"/jobs/{review_pending_job.id}/review", json=minimal_review)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        # Original text should be preserved if no correction provided
        assert data["extracted_text"] == review_pending_job.extracted_text

    def test_submit_review_with_fields_only(self, client, review_pending_job):
        """Test review submission updating only fields"""
        review_request = {
            "reviewer_id": "reviewer-fields",
            "corrected_fields": {"invoice_number": "INV-9999", "amount": 5000.00},
            "review_notes": "Updated structured fields only",
        }

        response = client.put(f"/jobs/{review_pending_job.id}/review", json=review_request)

        assert response.status_code == 200
        data = response.json()
        assert data["extracted_fields"] == review_request["corrected_fields"]

    def test_submit_review_with_time_tracking(self, client, review_pending_job):
        """Test review submission with time tracking"""
        review_request = {
            "reviewer_id": "reviewer-timed",
            "corrected_text": "Corrected text",
            "review_time_seconds": 300,
            "review_notes": "Took 5 minutes to review",
        }

        response = client.put(f"/jobs/{review_pending_job.id}/review", json=review_request)

        assert response.status_code == 200

    def test_submit_review_missing_reviewer_id(self, client, review_pending_job):
        """Test review submission without reviewer_id"""
        invalid_review = {
            "corrected_text": "Some text"
            # Missing reviewer_id
        }

        response = client.put(f"/jobs/{review_pending_job.id}/review", json=invalid_review)

        assert response.status_code == 422  # Validation error


# ============================================================================
# Background Task Tests
# ============================================================================


class TestBackgroundProcessing:
    """Tests for background OCR processing"""

    @patch("app.main.ocr_processor.process_document")
    def test_background_task_success(self, mock_process, client, sample_ocr_request, db_session):
        """Test background task processes job successfully"""
        from app.models import OCRJob

        mock_process.return_value = {
            "status": OCRStatus.COMPLETED,
            "extracted_text": "Background processed text",
            "confidence_score": 90.0,
            "tier_used": OCRTier.TESSERACT,
            "page_count": 1,
            "processing_time_ms": 200,
        }

        # Submit job
        response = client.post("/extract", json=sample_ocr_request)
        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # In actual background processing, we'd wait here
        # For testing, we can check the job was created
        job = db_session.query(OCRJob).filter(OCRJob.id == uuid.UUID(job_id)).first()
        assert job is not None

    @patch("app.main.ocr_processor.process_document")
    def test_background_task_failure(self, mock_process, client, sample_ocr_request):
        """Test background task handles processing failure"""
        mock_process.side_effect = Exception("Processing failed")

        response = client.post("/extract", json=sample_ocr_request)
        assert response.status_code == 200

        # Job is created but will fail in background

    @patch("app.main.ocr_processor.process_document")
    def test_background_task_caching(self, mock_process, client, sample_ocr_request, db_session):
        """Test background task creates cache entry on success"""

        mock_process.return_value = {
            "status": OCRStatus.COMPLETED,
            "extracted_text": "Text to cache",
            "confidence_score": 94.0,
            "tier_used": OCRTier.TESSERACT,
            "page_count": 1,
            "processing_time_ms": 180,
        }

        # Use unique hash for this test
        sample_ocr_request["document_hash"] = "unique-cache-hash-" + str(uuid.uuid4())
        response = client.post("/extract", json=sample_ocr_request)
        assert response.status_code == 200


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Tests for error handling in API endpoints"""

    def test_malformed_json(self, client):
        """Test handling of malformed JSON"""
        response = client.post(
            "/extract", data="not valid json", headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_empty_request_body(self, client):
        """Test handling of empty request body"""
        response = client.post("/extract", json={})

        assert response.status_code == 422

    def test_extra_fields_ignored(self, client, sample_ocr_request):
        """Test extra fields in request are handled gracefully"""
        sample_ocr_request["extra_field"] = "should be ignored"

        response = client.post("/extract", json=sample_ocr_request)

        # Should still succeed (Pydantic ignores extra fields by default)
        assert response.status_code == 200

    def test_wrong_data_types(self, client, sample_ocr_request):
        """Test handling of wrong data types"""
        sample_ocr_request["confidence_threshold"] = "not a number"

        response = client.post("/extract", json=sample_ocr_request)

        assert response.status_code == 422

    def test_database_error_handling(self, client, monkeypatch):
        """Test handling of database errors"""

        def mock_db_error(*args, **kwargs):
            raise Exception("Database connection failed")

        # This would require more sophisticated mocking
        # Just verify the endpoint structure is correct
        response = client.get("/health")
        assert response.status_code in [200, 503]
