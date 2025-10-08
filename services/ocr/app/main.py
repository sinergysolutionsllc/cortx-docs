"""
AI-Enhanced OCR Service - FastAPI Application
"""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import __version__
from .database import get_db_session, init_db
from .models import OCRCache, OCRJob, OCRReview, OCRStatus, OCRTier
from .processor import OCRProcessor
from .schemas import (
    HealthResponse,
    OCRCacheResponse,
    OCRJobResponse,
    OCRRequest,
    OCRReviewRequest,
    OCRStatsResponse,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the FastAPI application"""
    logger.info("OCR service starting up...")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Test Tesseract availability
    try:
        import pytesseract

        pytesseract.get_tesseract_version()
        logger.info("Tesseract OCR is available")
    except Exception as e:
        logger.warning(f"Tesseract not available: {e}")

    # Test Anthropic API
    anthropic_available = bool(os.getenv("ANTHROPIC_API_KEY"))
    logger.info(f"Anthropic API configured: {anthropic_available}")

    yield

    logger.info("OCR service shutting down...")


# Create FastAPI app
app = FastAPI(
    title="AI-Enhanced OCR Service",
    description=(
        "Multi-tier OCR pipeline with Tesseract, Claude Vision, and human review. "
        "Automatically escalates from fast OCR to AI-powered vision based on confidence."
    ),
    version=__version__,
    lifespan=lifespan,
)

# Initialize OCR processor
ocr_processor = OCRProcessor()


# ============================================================================
# Health Check Endpoints
# ============================================================================


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check(db: Session = Depends(get_db_session)) -> HealthResponse:
    """
    Health check endpoint with detailed service status
    """
    # Check Tesseract
    tesseract_available = False
    try:
        import pytesseract

        pytesseract.get_tesseract_version()
        tesseract_available = True
    except Exception:
        pass

    # Check Anthropic API
    anthropic_api_available = bool(os.getenv("ANTHROPIC_API_KEY"))

    # Check database
    database_connected = False
    try:
        db.execute(func.now())
        database_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    status = "healthy" if (tesseract_available and database_connected) else "degraded"

    return HealthResponse(
        status=status,
        version=__version__,
        tesseract_available=tesseract_available,
        anthropic_api_available=anthropic_api_available,
        database_connected=database_connected,
    )


@app.get("/healthz", tags=["health"])
async def healthz() -> JSONResponse:
    """Kubernetes liveness probe"""
    return JSONResponse({"status": "ok"})


@app.get("/readyz", tags=["health"])
async def readyz(db: Session = Depends(get_db_session)) -> JSONResponse:
    """Kubernetes readiness probe"""
    try:
        db.execute(func.now())
        return JSONResponse({"status": "ready"})
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse({"status": "not ready", "error": str(e)}, status_code=503)


# ============================================================================
# OCR Processing Endpoints
# ============================================================================


@app.post("/extract", response_model=OCRJobResponse, tags=["ocr"])
async def extract_text(
    request: OCRRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db_session)
) -> OCRJobResponse:
    """
    Submit a document for OCR extraction

    The service will:
    1. Check cache for existing results
    2. Process with Tesseract OCR (fast tier)
    3. Escalate to Claude Vision if confidence is low
    4. Queue for human review if still below threshold

    Returns immediately with a job ID. Use GET /jobs/{job_id} to retrieve results.
    """
    # Check cache first
    cache_entry = db.query(OCRCache).filter(OCRCache.document_hash == request.document_hash).first()

    if cache_entry:
        logger.info(f"Cache hit for document {request.document_hash}")

        # Update cache stats
        cache_entry.last_accessed_at = datetime.utcnow()
        cache_entry.hit_count += 1
        db.commit()

        # Create job with cached results
        job = OCRJob(
            id=uuid.uuid4(),
            tenant_id=request.tenant_id,
            document_hash=request.document_hash,
            status=OCRStatus.COMPLETED,
            tier_used=cache_entry.tier_used,
            confidence_score=cache_entry.confidence_score,
            extracted_text=cache_entry.extracted_text,
            extracted_fields=cache_entry.extracted_fields,
            page_count=cache_entry.page_count,
            processing_time_ms=0,  # Cached result
            user_id=request.user_id,
            correlation_id=request.correlation_id,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        return OCRJobResponse.model_validate(job)

    # Create new job
    job = OCRJob(
        id=uuid.uuid4(),
        tenant_id=request.tenant_id,
        document_hash=request.document_hash,
        status=OCRStatus.PENDING,
        document_type=request.document_type,
        user_id=request.user_id,
        correlation_id=request.correlation_id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Process in background
    background_tasks.add_task(
        process_ocr_job,
        job.id,
        request.document_data,
        request.document_type,
        request.force_tier,
        request.require_review,
        request.confidence_threshold,
        request.extract_fields,
    )

    return OCRJobResponse.model_validate(job)


def process_ocr_job(
    job_id: uuid.UUID,
    document_data: str,
    document_type: Optional[str],
    force_tier: Optional[OCRTier],
    require_review: bool,
    confidence_threshold: Optional[float],
    extract_fields: Optional[list],
) -> None:
    """
    Background task to process OCR job
    """
    from .database import SessionLocal

    db = SessionLocal()
    try:
        # Get job
        job = db.query(OCRJob).filter(OCRJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        # Update status
        job.status = OCRStatus.PROCESSING_TESSERACT
        db.commit()

        # Process document
        result = ocr_processor.process_document(
            document_data=document_data,
            document_type=document_type,
            force_tier=force_tier,
            confidence_threshold=confidence_threshold,
            extract_fields=extract_fields,
        )

        # Update job with results
        job.status = result.get("status", OCRStatus.COMPLETED)
        job.extracted_text = result.get("extracted_text")
        job.extracted_fields = result.get("extracted_fields")
        job.confidence_score = result.get("confidence_score")
        job.tier_used = result.get("tier_used")
        job.page_count = result.get("page_count")
        job.processing_time_ms = result.get("processing_time_ms")
        job.tesseract_confidence = result.get("tesseract_confidence")
        job.ai_confidence = result.get("ai_confidence")
        job.warnings = result.get("warnings")
        job.error_message = result.get("error_message")

        # Force review if requested
        if require_review and job.status == OCRStatus.COMPLETED:
            job.status = OCRStatus.AWAITING_REVIEW

        db.commit()

        # Cache successful results
        if job.status == OCRStatus.COMPLETED and job.extracted_text:
            cache_entry = OCRCache(
                document_hash=job.document_hash,
                extracted_text=job.extracted_text,
                extracted_fields=job.extracted_fields or {},
                confidence_score=job.confidence_score,
                tier_used=job.tier_used,
                document_type=job.document_type,
                page_count=job.page_count or 1,
                processing_time_ms=job.processing_time_ms or 0,
            )
            db.merge(cache_entry)  # Use merge to handle duplicates
            db.commit()

        logger.info(
            f"Job {job_id} completed with status {job.status}, "
            f"confidence {job.confidence_score:.1f}%, tier {job.tier_used}"
        )

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
        job = db.query(OCRJob).filter(OCRJob.id == job_id).first()
        if job:
            job.status = OCRStatus.FAILED
            job.error_message = str(e)
            db.commit()

    finally:
        db.close()


@app.get("/jobs/{job_id}", response_model=OCRJobResponse, tags=["ocr"])
async def get_job(job_id: str, db: Session = Depends(get_db_session)) -> OCRJobResponse:
    """
    Get OCR job status and results

    Use this endpoint to poll for job completion after submitting via POST /extract
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    job = db.query(OCRJob).filter(OCRJob.id == job_uuid).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return OCRJobResponse.model_validate(job)


@app.put("/jobs/{job_id}/review", response_model=OCRJobResponse, tags=["ocr"])
async def submit_review(
    job_id: str, review: OCRReviewRequest, db: Session = Depends(get_db_session)
) -> OCRJobResponse:
    """
    Submit human review corrections for an OCR job

    This endpoint allows reviewers to correct OCR results and mark them as verified.
    The job status will be updated to COMPLETED with 100% confidence.
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    job = db.query(OCRJob).filter(OCRJob.id == job_uuid).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != OCRStatus.AWAITING_REVIEW:
        raise HTTPException(
            status_code=400, detail=f"Job is not awaiting review (current status: {job.status})"
        )

    # Create review record
    review_record = OCRReview(
        id=uuid.uuid4(),
        job_id=job.id,
        reviewer_id=review.reviewer_id,
        corrected_text=review.corrected_text,
        corrected_fields=review.corrected_fields,
        review_notes=review.review_notes,
        review_time_seconds=review.review_time_seconds,
        confidence_after_review=100.0,
    )
    db.add(review_record)

    # Update job with corrected data
    if review.corrected_text:
        job.extracted_text = review.corrected_text
    if review.corrected_fields:
        job.extracted_fields = review.corrected_fields

    job.status = OCRStatus.COMPLETED
    job.tier_used = OCRTier.HUMAN_REVIEW
    job.confidence_score = 100.0

    db.commit()
    db.refresh(job)

    logger.info(f"Job {job_id} reviewed by {review.reviewer_id}")

    return OCRJobResponse.model_validate(job)


# ============================================================================
# Cache Management Endpoints
# ============================================================================


@app.get("/cache/{document_hash}", response_model=OCRCacheResponse, tags=["cache"])
async def get_cache(document_hash: str, db: Session = Depends(get_db_session)) -> OCRCacheResponse:
    """
    Check if a document hash exists in cache

    Use this to avoid reprocessing documents you've already submitted.
    """
    cache_entry = db.query(OCRCache).filter(OCRCache.document_hash == document_hash).first()

    if cache_entry:
        return OCRCacheResponse(
            cache_hit=True,
            document_hash=document_hash,
            extracted_text=cache_entry.extracted_text,
            extracted_fields=cache_entry.extracted_fields,
            confidence_score=cache_entry.confidence_score,
            tier_used=cache_entry.tier_used,
            page_count=cache_entry.page_count,
            processing_time_ms=cache_entry.processing_time_ms,
            cached_at=cache_entry.created_at,
            last_accessed_at=cache_entry.last_accessed_at,
            hit_count=cache_entry.hit_count,
        )
    else:
        return OCRCacheResponse(cache_hit=False, document_hash=document_hash)


# ============================================================================
# Statistics Endpoints
# ============================================================================


@app.get("/stats", response_model=OCRStatsResponse, tags=["stats"])
async def get_stats(
    tenant_id: Optional[str] = None, db: Session = Depends(get_db_session)
) -> OCRStatsResponse:
    """
    Get OCR service statistics

    Optionally filter by tenant_id to get tenant-specific stats.
    """
    query = db.query(OCRJob)
    if tenant_id:
        query = query.filter(OCRJob.tenant_id == tenant_id)

    # Total jobs
    total_jobs = query.count()

    # Jobs by status
    status_counts = {}
    for status in OCRStatus:
        count = query.filter(OCRJob.status == status).count()
        if count > 0:
            status_counts[status.value] = count

    # Jobs by tier
    tier_counts = {}
    for tier in OCRTier:
        count = query.filter(OCRJob.tier_used == tier).count()
        if count > 0:
            tier_counts[tier.value] = count

    # Average confidence
    avg_confidence = db.query(func.avg(OCRJob.confidence_score)).filter(
        OCRJob.confidence_score.isnot(None)
    )
    if tenant_id:
        avg_confidence = avg_confidence.filter(OCRJob.tenant_id == tenant_id)
    avg_confidence = avg_confidence.scalar() or 0.0

    # Average processing time
    avg_time = db.query(func.avg(OCRJob.processing_time_ms)).filter(
        OCRJob.processing_time_ms.isnot(None)
    )
    if tenant_id:
        avg_time = avg_time.filter(OCRJob.tenant_id == tenant_id)
    avg_time = avg_time.scalar() or 0.0

    # Cache hit rate
    total_cache_entries = db.query(OCRCache).count()
    total_cache_hits = db.query(func.sum(OCRCache.hit_count)).scalar() or 0
    cache_hit_rate = (
        (total_cache_hits / (total_jobs + total_cache_hits) * 100)
        if (total_jobs + total_cache_hits) > 0
        else 0.0
    )

    return OCRStatsResponse(
        total_jobs=total_jobs,
        jobs_by_status=status_counts,
        jobs_by_tier=tier_counts,
        average_confidence=float(avg_confidence),
        average_processing_time_ms=float(avg_time),
        cache_hit_rate=cache_hit_rate,
    )


# ============================================================================
# Root Endpoint
# ============================================================================


@app.get("/", tags=["meta"])
async def root() -> JSONResponse:
    """
    Service information
    """
    return JSONResponse(
        {
            "service": "AI-Enhanced OCR Service",
            "version": __version__,
            "description": "Multi-tier OCR with Tesseract, Claude Vision, and human review",
            "tiers": [
                {
                    "name": "tesseract",
                    "description": "Fast OCR for modern, clear documents",
                    "cost": "low",
                },
                {
                    "name": "ai_vision",
                    "description": "Claude 3.5 Sonnet for historical/handwritten documents",
                    "cost": "medium",
                },
                {
                    "name": "human_review",
                    "description": "100% accuracy guarantee via manual review",
                    "cost": "high",
                },
            ],
            "endpoints": {
                "health": "/health",
                "extract": "POST /extract",
                "get_job": "GET /jobs/{job_id}",
                "submit_review": "PUT /jobs/{job_id}/review",
                "cache_lookup": "GET /cache/{document_hash}",
                "stats": "GET /stats",
            },
        }
    )
