"""
Unit tests for database models
"""

import uuid
from datetime import datetime

import pytest
from app.models import OCRCache, OCRJob, OCRReview, OCRStatus, OCRTier

# ============================================================================
# Enum Tests
# ============================================================================


class TestOCRStatus:
    """Tests for OCRStatus enum"""

    def test_ocr_status_values(self):
        """Test OCRStatus enum has expected values"""
        assert OCRStatus.PENDING.value == "pending"
        assert OCRStatus.PROCESSING_TESSERACT.value == "processing_tesseract"
        assert OCRStatus.PROCESSING_AI.value == "processing_ai"
        assert OCRStatus.AWAITING_REVIEW.value == "awaiting_review"
        assert OCRStatus.COMPLETED.value == "completed"
        assert OCRStatus.FAILED.value == "failed"

    def test_ocr_status_all_states(self):
        """Test all OCR status states are defined"""
        statuses = [status.value for status in OCRStatus]
        assert len(statuses) == 6
        assert "pending" in statuses
        assert "completed" in statuses
        assert "failed" in statuses


class TestOCRTier:
    """Tests for OCRTier enum"""

    def test_ocr_tier_values(self):
        """Test OCRTier enum has expected values"""
        assert OCRTier.TESSERACT.value == "tesseract"
        assert OCRTier.AI_VISION.value == "ai_vision"
        assert OCRTier.HUMAN_REVIEW.value == "human_review"

    def test_ocr_tier_all_tiers(self):
        """Test all OCR tiers are defined"""
        tiers = [tier.value for tier in OCRTier]
        assert len(tiers) == 3


# ============================================================================
# OCRJob Model Tests
# ============================================================================


class TestOCRJob:
    """Tests for OCRJob model"""

    def test_create_ocr_job_minimal(self, db_session):
        """Test creating OCR job with minimal required fields"""
        job = OCRJob(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            document_hash="test-hash-123",
            status=OCRStatus.PENDING,
        )
        db_session.add(job)
        db_session.commit()

        assert job.id is not None
        assert job.tenant_id == "test-tenant"
        assert job.document_hash == "test-hash-123"
        assert job.status == OCRStatus.PENDING
        assert job.created_at is not None
        assert job.updated_at is not None

    def test_create_ocr_job_complete(
        self, db_session, sample_extracted_text, sample_extracted_fields
    ):
        """Test creating OCR job with all fields"""
        job_id = uuid.uuid4()
        job = OCRJob(
            id=job_id,
            tenant_id="test-tenant",
            document_hash="complete-hash-456",
            status=OCRStatus.COMPLETED,
            tier_used=OCRTier.TESSERACT,
            confidence_score=95.5,
            document_type="image/png",
            page_count=1,
            file_size_bytes=102400,
            extracted_text=sample_extracted_text,
            extracted_fields=sample_extracted_fields,
            processing_time_ms=250,
            tesseract_confidence=95.5,
            ai_confidence=None,
            warnings={"note": "test"},
            user_id="user-123",
            correlation_id="corr-456",
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        assert job.id == job_id
        assert job.status == OCRStatus.COMPLETED
        assert job.tier_used == OCRTier.TESSERACT
        assert job.confidence_score == 95.5
        assert job.extracted_text == sample_extracted_text
        assert job.extracted_fields == sample_extracted_fields
        assert job.processing_time_ms == 250

    def test_ocr_job_default_status(self, db_session):
        """Test OCR job defaults to PENDING status"""
        job = OCRJob(id=uuid.uuid4(), tenant_id="test-tenant", document_hash="default-hash")
        db_session.add(job)
        db_session.commit()

        assert job.status == OCRStatus.PENDING

    def test_ocr_job_timestamps(self, db_session):
        """Test OCR job automatically sets timestamps"""
        job = OCRJob(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            document_hash="timestamp-hash",
            status=OCRStatus.PENDING,
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        assert isinstance(job.created_at, datetime)
        assert isinstance(job.updated_at, datetime)
        assert job.created_at <= job.updated_at

    def test_ocr_job_update(self, db_session, sample_ocr_job):
        """Test updating OCR job"""
        original_updated = sample_ocr_job.updated_at

        sample_ocr_job.status = OCRStatus.COMPLETED
        sample_ocr_job.extracted_text = "New extracted text"
        sample_ocr_job.confidence_score = 92.0
        db_session.commit()
        db_session.refresh(sample_ocr_job)

        assert sample_ocr_job.status == OCRStatus.COMPLETED
        assert sample_ocr_job.extracted_text == "New extracted text"
        assert sample_ocr_job.confidence_score == 92.0

    def test_ocr_job_query_by_tenant(self, db_session):
        """Test querying jobs by tenant_id"""
        # Create jobs for different tenants
        job1 = OCRJob(
            id=uuid.uuid4(), tenant_id="tenant-1", document_hash="hash-1", status=OCRStatus.PENDING
        )
        job2 = OCRJob(
            id=uuid.uuid4(), tenant_id="tenant-2", document_hash="hash-2", status=OCRStatus.PENDING
        )
        db_session.add_all([job1, job2])
        db_session.commit()

        tenant1_jobs = db_session.query(OCRJob).filter(OCRJob.tenant_id == "tenant-1").all()

        assert len(tenant1_jobs) == 1
        assert tenant1_jobs[0].tenant_id == "tenant-1"

    def test_ocr_job_query_by_status(self, db_session):
        """Test querying jobs by status"""
        job1 = OCRJob(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            document_hash="hash-1",
            status=OCRStatus.COMPLETED,
        )
        job2 = OCRJob(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            document_hash="hash-2",
            status=OCRStatus.PENDING,
        )
        db_session.add_all([job1, job2])
        db_session.commit()

        completed_jobs = db_session.query(OCRJob).filter(OCRJob.status == OCRStatus.COMPLETED).all()

        assert len(completed_jobs) == 1
        assert completed_jobs[0].status == OCRStatus.COMPLETED

    def test_ocr_job_optional_fields_null(self, db_session):
        """Test OCR job with optional fields as None"""
        job = OCRJob(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            document_hash="null-test-hash",
            status=OCRStatus.PENDING,
            tier_used=None,
            confidence_score=None,
            extracted_text=None,
            extracted_fields=None,
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        assert job.tier_used is None
        assert job.confidence_score is None
        assert job.extracted_text is None
        assert job.extracted_fields is None

    def test_ocr_job_jsonb_fields(self, db_session):
        """Test OCR job JSONB fields (extracted_fields, warnings)"""
        job = OCRJob(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            document_hash="jsonb-hash",
            status=OCRStatus.COMPLETED,
            extracted_fields={"name": "John", "age": 30, "active": True},
            warnings={"low_quality": True, "pages": [1, 2, 3]},
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        assert isinstance(job.extracted_fields, dict)
        assert job.extracted_fields["name"] == "John"
        assert job.extracted_fields["age"] == 30
        assert isinstance(job.warnings, dict)
        assert job.warnings["low_quality"] is True


# ============================================================================
# OCRReview Model Tests
# ============================================================================


class TestOCRReview:
    """Tests for OCRReview model"""

    def test_create_review_minimal(self, db_session, sample_ocr_job):
        """Test creating review with minimal fields"""
        review = OCRReview(
            id=uuid.uuid4(),
            job_id=sample_ocr_job.id,
            reviewer_id="reviewer-123",
            confidence_after_review=100.0,
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        assert review.id is not None
        assert review.job_id == sample_ocr_job.id
        assert review.reviewer_id == "reviewer-123"
        assert review.confidence_after_review == 100.0
        assert review.reviewed_at is not None

    def test_create_review_complete(self, db_session, review_pending_job):
        """Test creating review with all fields"""
        review = OCRReview(
            id=uuid.uuid4(),
            job_id=review_pending_job.id,
            reviewer_id="reviewer-456",
            corrected_text="Fully corrected text",
            corrected_fields={"field1": "value1", "field2": "value2"},
            review_notes="Fixed multiple OCR errors",
            review_time_seconds=180,
            confidence_after_review=100.0,
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        assert review.corrected_text == "Fully corrected text"
        assert review.corrected_fields == {"field1": "value1", "field2": "value2"}
        assert review.review_notes == "Fixed multiple OCR errors"
        assert review.review_time_seconds == 180

    def test_review_default_confidence(self, db_session, sample_ocr_job):
        """Test review defaults to 100% confidence"""
        review = OCRReview(id=uuid.uuid4(), job_id=sample_ocr_job.id, reviewer_id="reviewer-789")
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        assert review.confidence_after_review == 100.0

    def test_review_timestamp(self, db_session, sample_ocr_job):
        """Test review automatically sets timestamp"""
        review = OCRReview(
            id=uuid.uuid4(),
            job_id=sample_ocr_job.id,
            reviewer_id="reviewer-999",
            confidence_after_review=100.0,
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        assert isinstance(review.reviewed_at, datetime)

    def test_review_query_by_job(self, db_session, sample_ocr_job):
        """Test querying reviews by job_id"""
        review1 = OCRReview(
            id=uuid.uuid4(),
            job_id=sample_ocr_job.id,
            reviewer_id="reviewer-1",
            confidence_after_review=100.0,
        )
        review2 = OCRReview(
            id=uuid.uuid4(),
            job_id=sample_ocr_job.id,
            reviewer_id="reviewer-2",
            confidence_after_review=100.0,
        )
        db_session.add_all([review1, review2])
        db_session.commit()

        reviews = db_session.query(OCRReview).filter(OCRReview.job_id == sample_ocr_job.id).all()

        assert len(reviews) == 2

    def test_review_query_by_reviewer(self, db_session, sample_ocr_job):
        """Test querying reviews by reviewer_id"""
        review = OCRReview(
            id=uuid.uuid4(),
            job_id=sample_ocr_job.id,
            reviewer_id="specific-reviewer",
            confidence_after_review=100.0,
        )
        db_session.add(review)
        db_session.commit()

        reviews = (
            db_session.query(OCRReview).filter(OCRReview.reviewer_id == "specific-reviewer").all()
        )

        assert len(reviews) == 1
        assert reviews[0].reviewer_id == "specific-reviewer"


# ============================================================================
# OCRCache Model Tests
# ============================================================================


class TestOCRCache:
    """Tests for OCRCache model"""

    def test_create_cache_entry(self, db_session):
        """Test creating cache entry"""
        cache = OCRCache(
            document_hash="cache-hash-123",
            extracted_text="Cached text",
            extracted_fields={"field": "value"},
            confidence_score=95.0,
            tier_used=OCRTier.TESSERACT,
            document_type="image/png",
            page_count=1,
            processing_time_ms=200,
        )
        db_session.add(cache)
        db_session.commit()
        db_session.refresh(cache)

        assert cache.document_hash == "cache-hash-123"
        assert cache.extracted_text == "Cached text"
        assert cache.confidence_score == 95.0
        assert cache.tier_used == OCRTier.TESSERACT
        assert cache.hit_count == 0

    def test_cache_default_hit_count(self, db_session):
        """Test cache entry defaults to 0 hit count"""
        cache = OCRCache(
            document_hash="default-cache-hash",
            extracted_text="Text",
            extracted_fields={},
            confidence_score=90.0,
            tier_used=OCRTier.TESSERACT,
            page_count=1,
            processing_time_ms=100,
        )
        db_session.add(cache)
        db_session.commit()
        db_session.refresh(cache)

        assert cache.hit_count == 0

    def test_cache_increment_hit_count(self, db_session, sample_cache_entry):
        """Test incrementing cache hit count"""
        original_count = sample_cache_entry.hit_count

        sample_cache_entry.hit_count += 1
        db_session.commit()
        db_session.refresh(sample_cache_entry)

        assert sample_cache_entry.hit_count == original_count + 1

    def test_cache_timestamps(self, db_session):
        """Test cache automatically sets timestamps"""
        cache = OCRCache(
            document_hash="timestamp-cache",
            extracted_text="Text",
            extracted_fields={},
            confidence_score=90.0,
            tier_used=OCRTier.TESSERACT,
            page_count=1,
            processing_time_ms=100,
        )
        db_session.add(cache)
        db_session.commit()
        db_session.refresh(cache)

        assert isinstance(cache.created_at, datetime)
        assert isinstance(cache.last_accessed_at, datetime)

    def test_cache_query_by_hash(self, db_session):
        """Test querying cache by document hash"""
        cache = OCRCache(
            document_hash="specific-hash-999",
            extracted_text="Specific text",
            extracted_fields={},
            confidence_score=92.0,
            tier_used=OCRTier.AI_VISION,
            page_count=1,
            processing_time_ms=500,
        )
        db_session.add(cache)
        db_session.commit()

        result = (
            db_session.query(OCRCache).filter(OCRCache.document_hash == "specific-hash-999").first()
        )

        assert result is not None
        assert result.document_hash == "specific-hash-999"
        assert result.extracted_text == "Specific text"

    def test_cache_unique_hash(self, db_session):
        """Test document_hash is unique (primary key)"""
        cache1 = OCRCache(
            document_hash="duplicate-hash",
            extracted_text="Text 1",
            extracted_fields={},
            confidence_score=90.0,
            tier_used=OCRTier.TESSERACT,
            page_count=1,
            processing_time_ms=100,
        )
        db_session.add(cache1)
        db_session.commit()

        # Try to add another with same hash
        cache2 = OCRCache(
            document_hash="duplicate-hash",
            extracted_text="Text 2",
            extracted_fields={},
            confidence_score=95.0,
            tier_used=OCRTier.TESSERACT,
            page_count=1,
            processing_time_ms=150,
        )
        db_session.add(cache2)

        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

    def test_cache_update_last_accessed(self, db_session, sample_cache_entry):
        """Test updating last_accessed_at timestamp"""
        from datetime import datetime

        original_accessed = sample_cache_entry.last_accessed_at

        # Simulate access after some time
        sample_cache_entry.last_accessed_at = datetime.utcnow()
        sample_cache_entry.hit_count += 1
        db_session.commit()
        db_session.refresh(sample_cache_entry)

        assert sample_cache_entry.last_accessed_at >= original_accessed
        assert sample_cache_entry.hit_count > 0

    def test_cache_empty_extracted_fields(self, db_session):
        """Test cache with empty extracted_fields dict"""
        cache = OCRCache(
            document_hash="empty-fields-hash",
            extracted_text="Text only",
            extracted_fields={},
            confidence_score=88.0,
            tier_used=OCRTier.TESSERACT,
            page_count=1,
            processing_time_ms=120,
        )
        db_session.add(cache)
        db_session.commit()
        db_session.refresh(cache)

        assert isinstance(cache.extracted_fields, dict)
        assert len(cache.extracted_fields) == 0

    def test_cache_all_tiers(self, db_session):
        """Test cache entries for all OCR tiers"""
        for tier in OCRTier:
            cache = OCRCache(
                document_hash=f"tier-{tier.value}-hash",
                extracted_text=f"Text from {tier.value}",
                extracted_fields={},
                confidence_score=90.0,
                tier_used=tier,
                page_count=1,
                processing_time_ms=200,
            )
            db_session.add(cache)

        db_session.commit()

        # Verify all tiers are represented
        for tier in OCRTier:
            result = db_session.query(OCRCache).filter(OCRCache.tier_used == tier).first()
            assert result is not None
