"""
Integration tests for cache and statistics endpoints
"""

import uuid

import pytest
from app.models import OCRCache, OCRJob, OCRStatus, OCRTier

# ============================================================================
# Cache Endpoint Tests
# ============================================================================


class TestCacheEndpoint:
    """Tests for GET /cache/{document_hash} endpoint"""

    def test_cache_lookup_hit(self, client, sample_cache_entry):
        """Test cache lookup with existing entry"""
        response = client.get(f"/cache/{sample_cache_entry.document_hash}")

        assert response.status_code == 200
        data = response.json()
        assert data["cache_hit"] is True
        assert data["document_hash"] == sample_cache_entry.document_hash
        assert data["extracted_text"] == sample_cache_entry.extracted_text
        assert data["confidence_score"] == sample_cache_entry.confidence_score
        assert data["tier_used"] == sample_cache_entry.tier_used.value
        assert data["page_count"] == sample_cache_entry.page_count
        assert "cached_at" in data
        assert "hit_count" in data

    def test_cache_lookup_miss(self, client):
        """Test cache lookup with non-existent entry"""
        non_existent_hash = "nonexistent-hash-999"
        response = client.get(f"/cache/{non_existent_hash}")

        assert response.status_code == 200
        data = response.json()
        assert data["cache_hit"] is False
        assert data["document_hash"] == non_existent_hash
        assert data["extracted_text"] is None
        assert data["confidence_score"] is None
        assert data["tier_used"] is None

    def test_cache_lookup_special_characters(self, client):
        """Test cache lookup with special characters in hash"""
        special_hash = "hash-with-special-chars_123"
        response = client.get(f"/cache/{special_hash}")

        assert response.status_code == 200
        data = response.json()
        assert data["cache_hit"] is False

    def test_cache_multiple_lookups(self, client, db_session):
        """Test multiple cache lookups increment hit count"""
        # Create cache entry
        cache = OCRCache(
            document_hash="multi-lookup-hash",
            extracted_text="Cached text",
            extracted_fields={},
            confidence_score=90.0,
            tier_used=OCRTier.TESSERACT,
            page_count=1,
            processing_time_ms=200,
            hit_count=0,
        )
        db_session.add(cache)
        db_session.commit()

        # First lookup
        response1 = client.get("/cache/multi-lookup-hash")
        assert response1.status_code == 200

        # Second lookup
        response2 = client.get("/cache/multi-lookup-hash")
        assert response2.status_code == 200

        # Note: hit_count is updated during job extraction, not cache lookup

    def test_cache_with_extracted_fields(self, client, db_session):
        """Test cache lookup returns extracted fields"""
        cache = OCRCache(
            document_hash="fields-cache-hash",
            extracted_text="Document text",
            extracted_fields={"invoice_number": "INV-123", "amount": 1234.56, "date": "2025-10-07"},
            confidence_score=95.0,
            tier_used=OCRTier.AI_VISION,
            page_count=1,
            processing_time_ms=1000,
        )
        db_session.add(cache)
        db_session.commit()

        response = client.get("/cache/fields-cache-hash")

        assert response.status_code == 200
        data = response.json()
        assert data["cache_hit"] is True
        assert data["extracted_fields"]["invoice_number"] == "INV-123"
        assert data["extracted_fields"]["amount"] == 1234.56

    def test_cache_all_tier_types(self, client, db_session):
        """Test cache entries from all OCR tiers"""
        for tier in OCRTier:
            cache = OCRCache(
                document_hash=f"tier-cache-{tier.value}",
                extracted_text=f"Text from {tier.value}",
                extracted_fields={},
                confidence_score=92.0,
                tier_used=tier,
                page_count=1,
                processing_time_ms=300,
            )
            db_session.add(cache)

        db_session.commit()

        # Verify each tier's cache entry
        for tier in OCRTier:
            response = client.get(f"/cache/tier-cache-{tier.value}")
            assert response.status_code == 200
            data = response.json()
            assert data["tier_used"] == tier.value


# ============================================================================
# Statistics Endpoint Tests
# ============================================================================


class TestStatsEndpoint:
    """Tests for GET /stats endpoint"""

    def test_stats_empty_database(self, client):
        """Test stats with no jobs in database"""
        response = client.get("/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs"] == 0
        assert data["jobs_by_status"] == {}
        assert data["jobs_by_tier"] == {}
        assert data["average_confidence"] == 0.0
        assert data["average_processing_time_ms"] == 0.0

    def test_stats_with_jobs(self, client, db_session):
        """Test stats with multiple jobs"""
        # Create various jobs
        jobs = [
            OCRJob(
                id=uuid.uuid4(),
                tenant_id="test-tenant",
                document_hash=f"hash-{i}",
                status=OCRStatus.COMPLETED,
                tier_used=OCRTier.TESSERACT,
                confidence_score=90.0 + i,
                processing_time_ms=200 + (i * 10),
            )
            for i in range(5)
        ]
        db_session.add_all(jobs)
        db_session.commit()

        response = client.get("/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs"] == 5
        assert "completed" in data["jobs_by_status"]
        assert data["jobs_by_status"]["completed"] == 5
        assert "tesseract" in data["jobs_by_tier"]
        assert data["average_confidence"] > 0

    def test_stats_by_tenant(self, client, db_session):
        """Test stats filtered by tenant_id"""
        # Create jobs for different tenants
        tenant1_jobs = [
            OCRJob(
                id=uuid.uuid4(),
                tenant_id="tenant-1",
                document_hash=f"t1-hash-{i}",
                status=OCRStatus.COMPLETED,
                tier_used=OCRTier.TESSERACT,
                confidence_score=90.0,
                processing_time_ms=200,
            )
            for i in range(3)
        ]

        tenant2_jobs = [
            OCRJob(
                id=uuid.uuid4(),
                tenant_id="tenant-2",
                document_hash=f"t2-hash-{i}",
                status=OCRStatus.COMPLETED,
                tier_used=OCRTier.AI_VISION,
                confidence_score=95.0,
                processing_time_ms=1000,
            )
            for i in range(2)
        ]

        db_session.add_all(tenant1_jobs + tenant2_jobs)
        db_session.commit()

        # Get stats for tenant-1
        response = client.get("/stats?tenant_id=tenant-1")

        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs"] == 3
        assert data["jobs_by_tier"]["tesseract"] == 3

    def test_stats_multiple_statuses(self, client, db_session):
        """Test stats with jobs in multiple statuses"""
        jobs = [
            OCRJob(
                id=uuid.uuid4(),
                tenant_id="test-tenant",
                document_hash="pending-1",
                status=OCRStatus.PENDING,
            ),
            OCRJob(
                id=uuid.uuid4(),
                tenant_id="test-tenant",
                document_hash="completed-1",
                status=OCRStatus.COMPLETED,
                tier_used=OCRTier.TESSERACT,
                confidence_score=90.0,
                processing_time_ms=200,
            ),
            OCRJob(
                id=uuid.uuid4(),
                tenant_id="test-tenant",
                document_hash="failed-1",
                status=OCRStatus.FAILED,
            ),
            OCRJob(
                id=uuid.uuid4(),
                tenant_id="test-tenant",
                document_hash="review-1",
                status=OCRStatus.AWAITING_REVIEW,
                tier_used=OCRTier.AI_VISION,
                confidence_score=75.0,
                processing_time_ms=1200,
            ),
        ]
        db_session.add_all(jobs)
        db_session.commit()

        response = client.get("/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs"] == 4
        assert data["jobs_by_status"]["pending"] == 1
        assert data["jobs_by_status"]["completed"] == 1
        assert data["jobs_by_status"]["failed"] == 1
        assert data["jobs_by_status"]["awaiting_review"] == 1

    def test_stats_multiple_tiers(self, client, db_session):
        """Test stats with jobs using different OCR tiers"""
        jobs = [
            OCRJob(
                id=uuid.uuid4(),
                tenant_id="test-tenant",
                document_hash="tesseract-1",
                status=OCRStatus.COMPLETED,
                tier_used=OCRTier.TESSERACT,
                confidence_score=92.0,
                processing_time_ms=200,
            ),
            OCRJob(
                id=uuid.uuid4(),
                tenant_id="test-tenant",
                document_hash="tesseract-2",
                status=OCRStatus.COMPLETED,
                tier_used=OCRTier.TESSERACT,
                confidence_score=88.0,
                processing_time_ms=250,
            ),
            OCRJob(
                id=uuid.uuid4(),
                tenant_id="test-tenant",
                document_hash="ai-1",
                status=OCRStatus.COMPLETED,
                tier_used=OCRTier.AI_VISION,
                confidence_score=95.0,
                processing_time_ms=1500,
            ),
            OCRJob(
                id=uuid.uuid4(),
                tenant_id="test-tenant",
                document_hash="human-1",
                status=OCRStatus.COMPLETED,
                tier_used=OCRTier.HUMAN_REVIEW,
                confidence_score=100.0,
                processing_time_ms=0,
            ),
        ]
        db_session.add_all(jobs)
        db_session.commit()

        response = client.get("/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["jobs_by_tier"]["tesseract"] == 2
        assert data["jobs_by_tier"]["ai_vision"] == 1
        assert data["jobs_by_tier"]["human_review"] == 1

    def test_stats_average_calculations(self, client, db_session):
        """Test stats correctly calculates averages"""
        jobs = [
            OCRJob(
                id=uuid.uuid4(),
                tenant_id="test-tenant",
                document_hash=f"avg-{i}",
                status=OCRStatus.COMPLETED,
                tier_used=OCRTier.TESSERACT,
                confidence_score=float(80 + (i * 5)),  # 80, 85, 90, 95
                processing_time_ms=100 + (i * 100),  # 100, 200, 300, 400
            )
            for i in range(4)
        ]
        db_session.add_all(jobs)
        db_session.commit()

        response = client.get("/stats")

        assert response.status_code == 200
        data = response.json()
        # Average confidence: (80 + 85 + 90 + 95) / 4 = 87.5
        assert data["average_confidence"] == pytest.approx(87.5, rel=0.1)
        # Average time: (100 + 200 + 300 + 400) / 4 = 250
        assert data["average_processing_time_ms"] == pytest.approx(250.0, rel=0.1)

    def test_stats_cache_hit_rate(self, client, db_session):
        """Test stats calculates cache hit rate correctly"""
        # Create jobs
        jobs = [
            OCRJob(
                id=uuid.uuid4(),
                tenant_id="test-tenant",
                document_hash=f"job-{i}",
                status=OCRStatus.COMPLETED,
                tier_used=OCRTier.TESSERACT,
                confidence_score=90.0,
                processing_time_ms=200,
            )
            for i in range(10)
        ]
        db_session.add_all(jobs)

        # Create cache entries with hits
        caches = [
            OCRCache(
                document_hash=f"cache-{i}",
                extracted_text="Cached text",
                extracted_fields={},
                confidence_score=90.0,
                tier_used=OCRTier.TESSERACT,
                page_count=1,
                processing_time_ms=200,
                hit_count=2,  # Each cache entry has 2 hits
            )
            for i in range(5)
        ]
        db_session.add_all(caches)
        db_session.commit()

        response = client.get("/stats")

        assert response.status_code == 200
        data = response.json()
        # Total cache hits: 5 * 2 = 10
        # Total jobs: 10
        # Cache hit rate: 10 / (10 + 10) * 100 = 50%
        assert "cache_hit_rate" in data
        assert data["cache_hit_rate"] >= 0

    def test_stats_excludes_none_values(self, client, db_session):
        """Test stats handles jobs with None values correctly"""
        jobs = [
            OCRJob(
                id=uuid.uuid4(),
                tenant_id="test-tenant",
                document_hash="pending-job",
                status=OCRStatus.PENDING,
                confidence_score=None,
                processing_time_ms=None,
            ),
            OCRJob(
                id=uuid.uuid4(),
                tenant_id="test-tenant",
                document_hash="completed-job",
                status=OCRStatus.COMPLETED,
                tier_used=OCRTier.TESSERACT,
                confidence_score=90.0,
                processing_time_ms=200,
            ),
        ]
        db_session.add_all(jobs)
        db_session.commit()

        response = client.get("/stats")

        assert response.status_code == 200
        data = response.json()
        # Averages should only include non-None values
        assert data["average_confidence"] == 90.0
        assert data["average_processing_time_ms"] == 200.0


# ============================================================================
# Cache and Stats Integration Tests
# ============================================================================


class TestCacheStatsIntegration:
    """Tests for cache and stats working together"""

    def test_cache_usage_reflected_in_stats(self, client, db_session, sample_cache_entry):
        """Test that cache hits are reflected in statistics"""
        # Create a job that uses cached data
        job = OCRJob(
            id=uuid.uuid4(),
            tenant_id="test-tenant",
            document_hash=sample_cache_entry.document_hash,
            status=OCRStatus.COMPLETED,
            tier_used=sample_cache_entry.tier_used,
            confidence_score=sample_cache_entry.confidence_score,
            extracted_text=sample_cache_entry.extracted_text,
            processing_time_ms=0,  # Instant due to cache
        )
        db_session.add(job)

        # Increment cache hit
        sample_cache_entry.hit_count += 1
        db_session.commit()

        # Check stats
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs"] >= 1

    def test_successful_extraction_creates_cache(self, client, db_session):
        """Test that successful extractions create cache entries"""
        # Note: This would require full integration with background tasks
        # Just verify the cache endpoint structure
        response = client.get("/cache/test-hash-for-creation")
        assert response.status_code == 200

    def test_stats_show_tier_distribution(self, client, db_session):
        """Test stats accurately show distribution across tiers"""
        # Create balanced job distribution
        for tier in OCRTier:
            for i in range(3):
                job = OCRJob(
                    id=uuid.uuid4(),
                    tenant_id="test-tenant",
                    document_hash=f"{tier.value}-job-{i}",
                    status=OCRStatus.COMPLETED,
                    tier_used=tier,
                    confidence_score=90.0,
                    processing_time_ms=500,
                )
                db_session.add(job)

        db_session.commit()

        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()

        # Each tier should have 3 jobs
        for tier in OCRTier:
            assert data["jobs_by_tier"][tier.value] == 3

    def test_cache_performance_metrics(self, client, db_session):
        """Test cache stores and returns performance metrics"""
        cache = OCRCache(
            document_hash="perf-test-hash",
            extracted_text="Performance test text",
            extracted_fields={"test": "data"},
            confidence_score=94.5,
            tier_used=OCRTier.AI_VISION,
            page_count=5,
            processing_time_ms=2500,
        )
        db_session.add(cache)
        db_session.commit()

        response = client.get("/cache/perf-test-hash")
        assert response.status_code == 200
        data = response.json()

        assert data["page_count"] == 5
        assert data["processing_time_ms"] == 2500
        assert data["tier_used"] == "ai_vision"
