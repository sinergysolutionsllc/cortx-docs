"""
Unit tests for Pydantic schemas
"""

from datetime import datetime

import pytest
from app.models import OCRStatus, OCRTier
from app.schemas import (
    HealthResponse,
    OCRCacheResponse,
    OCRJobResponse,
    OCRRequest,
    OCRReviewRequest,
    OCRStatsResponse,
)
from pydantic import ValidationError

# ============================================================================
# OCRRequest Schema Tests
# ============================================================================


class TestOCRRequest:
    """Tests for OCRRequest schema"""

    def test_ocr_request_valid_minimal(self, sample_document_hash, sample_image_base64):
        """Test OCR request with minimal required fields"""
        data = {
            "document_hash": sample_document_hash,
            "document_data": sample_image_base64,
            "tenant_id": "test-tenant",
        }
        request = OCRRequest(**data)

        assert request.document_hash == sample_document_hash
        assert request.document_data == sample_image_base64
        assert request.tenant_id == "test-tenant"
        assert request.require_review is False
        assert request.document_type is None

    def test_ocr_request_valid_complete(self, sample_document_hash, sample_image_base64):
        """Test OCR request with all fields"""
        data = {
            "document_hash": sample_document_hash,
            "document_data": sample_image_base64,
            "document_type": "image/png",
            "tenant_id": "test-tenant",
            "user_id": "user-123",
            "force_tier": OCRTier.TESSERACT,
            "require_review": True,
            "confidence_threshold": 85.0,
            "extract_fields": ["invoice_number", "date", "amount"],
            "correlation_id": "corr-456",
        }
        request = OCRRequest(**data)

        assert request.document_type == "image/png"
        assert request.user_id == "user-123"
        assert request.force_tier == OCRTier.TESSERACT
        assert request.require_review is True
        assert request.confidence_threshold == 85.0
        assert request.extract_fields == ["invoice_number", "date", "amount"]
        assert request.correlation_id == "corr-456"

    def test_ocr_request_missing_required_fields(self):
        """Test OCR request fails without required fields"""
        with pytest.raises(ValidationError) as exc_info:
            OCRRequest(document_hash="hash123")

        errors = exc_info.value.errors()
        assert any(e["loc"][0] == "document_data" for e in errors)
        assert any(e["loc"][0] == "tenant_id" for e in errors)

    def test_ocr_request_invalid_tier(self, sample_document_hash, sample_image_base64):
        """Test OCR request with invalid tier"""
        data = {
            "document_hash": sample_document_hash,
            "document_data": sample_image_base64,
            "tenant_id": "test-tenant",
            "force_tier": "invalid_tier",
        }
        with pytest.raises(ValidationError):
            OCRRequest(**data)

    def test_ocr_request_valid_tiers(self, sample_document_hash, sample_image_base64):
        """Test OCR request with all valid tiers"""
        for tier in OCRTier:
            data = {
                "document_hash": sample_document_hash,
                "document_data": sample_image_base64,
                "tenant_id": "test-tenant",
                "force_tier": tier,
            }
            request = OCRRequest(**data)
            assert request.force_tier == tier


# ============================================================================
# OCRJobResponse Schema Tests
# ============================================================================


class TestOCRJobResponse:
    """Tests for OCRJobResponse schema"""

    def test_job_response_from_model(self, completed_ocr_job):
        """Test creating job response from database model"""
        response = OCRJobResponse.model_validate(completed_ocr_job)

        assert str(response.job_id) == str(completed_ocr_job.id)
        assert response.tenant_id == completed_ocr_job.tenant_id
        assert response.status == completed_ocr_job.status
        assert response.document_hash == completed_ocr_job.document_hash
        assert response.tier_used == completed_ocr_job.tier_used
        assert response.confidence_score == completed_ocr_job.confidence_score
        assert response.extracted_text == completed_ocr_job.extracted_text

    def test_job_response_pending_job(self, sample_ocr_job):
        """Test job response for pending job"""
        response = OCRJobResponse.model_validate(sample_ocr_job)

        assert response.status == OCRStatus.PENDING
        assert response.tier_used is None
        assert response.extracted_text is None
        assert response.confidence_score is None

    def test_job_response_with_all_fields(self, db_session, sample_extracted_text):
        """Test job response with all optional fields populated"""
        import uuid

        from app.models import OCRJob

        job = OCRJob(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            document_hash="full-response-hash",
            status=OCRStatus.COMPLETED,
            tier_used=OCRTier.AI_VISION,
            confidence_score=94.5,
            extracted_text=sample_extracted_text,
            extracted_fields={"field": "value"},
            document_type="application/pdf",
            page_count=3,
            processing_time_ms=1500,
            tesseract_confidence=75.0,
            ai_confidence=94.5,
            warnings={"note": "test warning"},
            error_message=None,
            user_id="user-789",
            correlation_id="corr-999",
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        response = OCRJobResponse.model_validate(job)

        assert response.page_count == 3
        assert response.processing_time_ms == 1500
        assert response.tesseract_confidence == 75.0
        assert response.ai_confidence == 94.5
        assert response.warnings == {"note": "test warning"}
        assert response.user_id == "user-789"
        assert response.correlation_id == "corr-999"

    def test_job_response_serialization(self, completed_ocr_job):
        """Test job response can be serialized to JSON"""
        response = OCRJobResponse.model_validate(completed_ocr_job)
        json_data = response.model_dump(mode="json")

        assert isinstance(json_data, dict)
        assert "job_id" in json_data
        assert "tenant_id" in json_data
        assert "status" in json_data


# ============================================================================
# OCRReviewRequest Schema Tests
# ============================================================================


class TestOCRReviewRequest:
    """Tests for OCRReviewRequest schema"""

    def test_review_request_minimal(self):
        """Test review request with minimal fields"""
        data = {"reviewer_id": "reviewer-123"}
        request = OCRReviewRequest(**data)

        assert request.reviewer_id == "reviewer-123"
        assert request.corrected_text is None
        assert request.corrected_fields is None
        assert request.review_notes is None
        assert request.review_time_seconds is None

    def test_review_request_complete(self):
        """Test review request with all fields"""
        data = {
            "reviewer_id": "reviewer-456",
            "corrected_text": "Corrected OCR text",
            "corrected_fields": {"name": "John Doe", "amount": 1500.00},
            "review_notes": "Fixed multiple errors",
            "review_time_seconds": 180,
        }
        request = OCRReviewRequest(**data)

        assert request.reviewer_id == "reviewer-456"
        assert request.corrected_text == "Corrected OCR text"
        assert request.corrected_fields == {"name": "John Doe", "amount": 1500.00}
        assert request.review_notes == "Fixed multiple errors"
        assert request.review_time_seconds == 180

    def test_review_request_missing_reviewer_id(self):
        """Test review request fails without reviewer_id"""
        with pytest.raises(ValidationError) as exc_info:
            OCRReviewRequest(corrected_text="Some text")

        errors = exc_info.value.errors()
        assert any(e["loc"][0] == "reviewer_id" for e in errors)

    def test_review_request_with_complex_fields(self):
        """Test review request with complex field structures"""
        data = {
            "reviewer_id": "reviewer-789",
            "corrected_fields": {
                "items": [{"name": "Item 1", "price": 100.00}, {"name": "Item 2", "price": 200.00}],
                "metadata": {"reviewed_by": "John", "confidence": 100},
            },
        }
        request = OCRReviewRequest(**data)

        assert isinstance(request.corrected_fields, dict)
        assert "items" in request.corrected_fields
        assert len(request.corrected_fields["items"]) == 2


# ============================================================================
# OCRCacheResponse Schema Tests
# ============================================================================


class TestOCRCacheResponse:
    """Tests for OCRCacheResponse schema"""

    def test_cache_response_hit(self):
        """Test cache response with cache hit"""
        data = {
            "cache_hit": True,
            "document_hash": "cached-hash",
            "extracted_text": "Cached text",
            "extracted_fields": {"field": "value"},
            "confidence_score": 95.0,
            "tier_used": OCRTier.TESSERACT,
            "page_count": 1,
            "processing_time_ms": 200,
            "cached_at": datetime.utcnow(),
            "last_accessed_at": datetime.utcnow(),
            "hit_count": 5,
        }
        response = OCRCacheResponse(**data)

        assert response.cache_hit is True
        assert response.extracted_text == "Cached text"
        assert response.confidence_score == 95.0
        assert response.hit_count == 5

    def test_cache_response_miss(self):
        """Test cache response with cache miss"""
        data = {"cache_hit": False, "document_hash": "uncached-hash"}
        response = OCRCacheResponse(**data)

        assert response.cache_hit is False
        assert response.document_hash == "uncached-hash"
        assert response.extracted_text is None
        assert response.confidence_score is None
        assert response.hit_count is None

    def test_cache_response_serialization(self):
        """Test cache response serialization"""
        data = {
            "cache_hit": True,
            "document_hash": "hash-123",
            "extracted_text": "Text",
            "confidence_score": 90.0,
            "tier_used": OCRTier.AI_VISION,
            "page_count": 2,
            "processing_time_ms": 500,
            "cached_at": datetime.utcnow(),
        }
        response = OCRCacheResponse(**data)
        json_data = response.model_dump(mode="json")

        assert isinstance(json_data, dict)
        assert json_data["cache_hit"] is True
        assert json_data["tier_used"] == "ai_vision"


# ============================================================================
# OCRStatsResponse Schema Tests
# ============================================================================


class TestOCRStatsResponse:
    """Tests for OCRStatsResponse schema"""

    def test_stats_response_complete(self):
        """Test stats response with all fields"""
        data = {
            "total_jobs": 1000,
            "jobs_by_status": {"completed": 950, "failed": 20, "awaiting_review": 30},
            "jobs_by_tier": {"tesseract": 800, "ai_vision": 150, "human_review": 50},
            "average_confidence": 92.5,
            "average_processing_time_ms": 350.0,
            "cache_hit_rate": 15.5,
        }
        response = OCRStatsResponse(**data)

        assert response.total_jobs == 1000
        assert response.jobs_by_status["completed"] == 950
        assert response.jobs_by_tier["tesseract"] == 800
        assert response.average_confidence == 92.5
        assert response.cache_hit_rate == 15.5

    def test_stats_response_zero_jobs(self):
        """Test stats response with zero jobs"""
        data = {
            "total_jobs": 0,
            "jobs_by_status": {},
            "jobs_by_tier": {},
            "average_confidence": 0.0,
            "average_processing_time_ms": 0.0,
            "cache_hit_rate": 0.0,
        }
        response = OCRStatsResponse(**data)

        assert response.total_jobs == 0
        assert len(response.jobs_by_status) == 0
        assert response.average_confidence == 0.0

    def test_stats_response_missing_required_fields(self):
        """Test stats response fails without required fields"""
        with pytest.raises(ValidationError):
            OCRStatsResponse(total_jobs=100)

    def test_stats_response_serialization(self):
        """Test stats response serialization"""
        data = {
            "total_jobs": 500,
            "jobs_by_status": {"completed": 450},
            "jobs_by_tier": {"tesseract": 400},
            "average_confidence": 90.0,
            "average_processing_time_ms": 300.0,
            "cache_hit_rate": 10.0,
        }
        response = OCRStatsResponse(**data)
        json_data = response.model_dump(mode="json")

        assert isinstance(json_data, dict)
        assert json_data["total_jobs"] == 500


# ============================================================================
# HealthResponse Schema Tests
# ============================================================================


class TestHealthResponse:
    """Tests for HealthResponse schema"""

    def test_health_response_healthy(self):
        """Test health response when all services are healthy"""
        data = {
            "status": "healthy",
            "version": "1.0.0",
            "tesseract_available": True,
            "anthropic_api_available": True,
            "database_connected": True,
        }
        response = HealthResponse(**data)

        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.tesseract_available is True
        assert response.anthropic_api_available is True
        assert response.database_connected is True

    def test_health_response_degraded(self):
        """Test health response when service is degraded"""
        data = {
            "status": "degraded",
            "version": "1.0.0",
            "tesseract_available": True,
            "anthropic_api_available": False,
            "database_connected": True,
        }
        response = HealthResponse(**data)

        assert response.status == "degraded"
        assert response.anthropic_api_available is False

    def test_health_response_unhealthy(self):
        """Test health response when service is unhealthy"""
        data = {
            "status": "unhealthy",
            "version": "1.0.0",
            "tesseract_available": False,
            "anthropic_api_available": False,
            "database_connected": False,
        }
        response = HealthResponse(**data)

        assert response.status == "unhealthy"
        assert response.tesseract_available is False
        assert response.database_connected is False

    def test_health_response_missing_fields(self):
        """Test health response fails without required fields"""
        with pytest.raises(ValidationError):
            HealthResponse(status="healthy")

    def test_health_response_serialization(self):
        """Test health response serialization"""
        data = {
            "status": "healthy",
            "version": "1.0.0",
            "tesseract_available": True,
            "anthropic_api_available": True,
            "database_connected": True,
        }
        response = HealthResponse(**data)
        json_data = response.model_dump(mode="json")

        assert isinstance(json_data, dict)
        assert json_data["status"] == "healthy"
        assert json_data["version"] == "1.0.0"


# ============================================================================
# Schema Integration Tests
# ============================================================================


class TestSchemaIntegration:
    """Tests for schema interactions and conversions"""

    def test_job_response_from_dict(self):
        """Test creating job response from dictionary"""
        data = {
            "job_id": "12345678-1234-5678-1234-567812345678",
            "tenant_id": "test-tenant",
            "status": "completed",
            "document_hash": "hash123",
            "tier_used": "tesseract",
            "confidence_score": 95.0,
            "extracted_text": "Sample text",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        response = OCRJobResponse(**data)

        assert response.status == "completed"
        assert response.tier_used == "tesseract"

    def test_ocr_request_json_example(self):
        """Test OCR request matches documented example"""
        example = {
            "document_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "document_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "document_type": "image/png",
            "tenant_id": "tenant-123",
            "user_id": "user-456",
            "require_review": False,
            "correlation_id": "req-789",
        }
        request = OCRRequest(**example)

        assert request.tenant_id == "tenant-123"
        assert request.user_id == "user-456"
        assert request.require_review is False
