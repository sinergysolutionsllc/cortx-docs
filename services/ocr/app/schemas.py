"""
Pydantic schemas for OCR service API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .models import OCRStatus, OCRTier


class OCRRequest(BaseModel):
    """Request to extract text from a document"""

    document_hash: str = Field(..., description="SHA-256 hash of the document")
    document_data: str = Field(..., description="Base64-encoded document data")
    document_type: Optional[str] = Field(
        None, description="MIME type or file extension (e.g., 'image/png', 'application/pdf')"
    )
    tenant_id: str = Field(..., description="Tenant identifier")
    user_id: Optional[str] = Field(None, description="User identifier for audit trail")
    force_tier: Optional[OCRTier] = Field(
        None, description="Force specific OCR tier (bypass auto-selection)"
    )
    require_review: bool = Field(
        False, description="Whether human review is required regardless of confidence"
    )
    confidence_threshold: Optional[float] = Field(
        None, description="Custom confidence threshold (0-100)"
    )
    extract_fields: Optional[List[str]] = Field(
        None, description="Specific fields to extract (e.g., ['name', 'date', 'amount'])"
    )
    correlation_id: Optional[str] = Field(None, description="Correlation ID for request tracing")

    class Config:
        json_schema_extra = {
            "example": {
                "document_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "document_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "document_type": "image/png",
                "tenant_id": "tenant-123",
                "user_id": "user-456",
                "require_review": False,
                "correlation_id": "req-789",
            }
        }


class OCRJobResponse(BaseModel):
    """Response containing OCR job details"""

    job_id: str = Field(..., description="Unique job identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    status: OCRStatus = Field(..., description="Current processing status")
    document_hash: str = Field(..., description="Document hash")

    # Processing details
    tier_used: Optional[OCRTier] = Field(None, description="OCR tier used for processing")
    confidence_score: Optional[float] = Field(None, description="Overall confidence score (0-100)")

    # Results
    extracted_text: Optional[str] = Field(None, description="Extracted text content")
    extracted_fields: Optional[Dict[str, Any]] = Field(
        None, description="Extracted structured fields"
    )

    # Metadata
    document_type: Optional[str] = Field(None, description="Document type")
    page_count: Optional[int] = Field(None, description="Number of pages processed")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")

    # Quality metrics
    tesseract_confidence: Optional[float] = Field(None, description="Tesseract confidence score")
    ai_confidence: Optional[float] = Field(None, description="AI vision confidence score")
    warnings: Optional[Dict[str, Any]] = Field(None, description="Processing warnings")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    # Audit
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    user_id: Optional[str] = Field(None, description="User who submitted the job")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "tenant_id": "tenant-123",
                "status": "completed",
                "document_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "tier_used": "tesseract",
                "confidence_score": 95.5,
                "extracted_text": "Sample document text",
                "page_count": 1,
                "processing_time_ms": 250,
                "created_at": "2025-10-07T12:00:00Z",
                "updated_at": "2025-10-07T12:00:01Z",
            }
        }


class OCRReviewRequest(BaseModel):
    """Request to submit human review corrections"""

    reviewer_id: str = Field(..., description="ID of the reviewer")
    corrected_text: Optional[str] = Field(
        None, description="Corrected text (if different from extracted)"
    )
    corrected_fields: Optional[Dict[str, Any]] = Field(
        None, description="Corrected structured fields"
    )
    review_notes: Optional[str] = Field(None, description="Notes about the review")
    review_time_seconds: Optional[int] = Field(None, description="Time spent on review in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "reviewer_id": "reviewer-789",
                "corrected_text": "Corrected document text",
                "corrected_fields": {"name": "John Doe", "date": "2025-10-07"},
                "review_notes": "Fixed OCR errors in name field",
                "review_time_seconds": 120,
            }
        }


class OCRCacheResponse(BaseModel):
    """Response from cache lookup"""

    cache_hit: bool = Field(..., description="Whether cache entry was found")
    document_hash: str = Field(..., description="Document hash")

    # Cached data (only if cache_hit=True)
    extracted_text: Optional[str] = Field(None, description="Cached extracted text")
    extracted_fields: Optional[Dict[str, Any]] = Field(None, description="Cached structured fields")
    confidence_score: Optional[float] = Field(None, description="Cached confidence score")
    tier_used: Optional[OCRTier] = Field(None, description="Tier used for cached result")
    page_count: Optional[int] = Field(None, description="Number of pages")
    processing_time_ms: Optional[int] = Field(None, description="Original processing time")

    # Cache metadata
    cached_at: Optional[datetime] = Field(None, description="When result was cached")
    last_accessed_at: Optional[datetime] = Field(None, description="Last access time")
    hit_count: Optional[int] = Field(None, description="Number of cache hits")

    class Config:
        json_schema_extra = {
            "example": {
                "cache_hit": True,
                "document_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "extracted_text": "Cached document text",
                "confidence_score": 95.5,
                "tier_used": "tesseract",
                "cached_at": "2025-10-07T10:00:00Z",
                "hit_count": 5,
            }
        }


class OCRStatsResponse(BaseModel):
    """OCR service statistics"""

    total_jobs: int = Field(..., description="Total number of jobs processed")
    jobs_by_status: Dict[str, int] = Field(..., description="Job counts by status")
    jobs_by_tier: Dict[str, int] = Field(..., description="Job counts by tier")
    average_confidence: float = Field(..., description="Average confidence score")
    average_processing_time_ms: float = Field(..., description="Average processing time")
    cache_hit_rate: float = Field(..., description="Cache hit rate (0-100)")

    class Config:
        json_schema_extra = {
            "example": {
                "total_jobs": 1000,
                "jobs_by_status": {"completed": 950, "failed": 20, "awaiting_review": 30},
                "jobs_by_tier": {"tesseract": 800, "ai_vision": 150, "human_review": 50},
                "average_confidence": 92.5,
                "average_processing_time_ms": 350,
                "cache_hit_rate": 15.5,
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    tesseract_available: bool = Field(..., description="Whether Tesseract is available")
    anthropic_api_available: bool = Field(..., description="Whether Anthropic API is configured")
    database_connected: bool = Field(..., description="Whether database is connected")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "tesseract_available": True,
                "anthropic_api_available": True,
                "database_connected": True,
            }
        }
