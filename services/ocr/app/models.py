"""
Database models for OCR job tracking and results
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import TIMESTAMP, Enum, Float, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class OCRStatus(str, PyEnum):
    """OCR processing status"""

    PENDING = "pending"
    PROCESSING_TESSERACT = "processing_tesseract"
    PROCESSING_AI = "processing_ai"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"
    FAILED = "failed"


class OCRTier(str, PyEnum):
    """OCR processing tier used"""

    TESSERACT = "tesseract"
    AI_VISION = "ai_vision"
    HUMAN_REVIEW = "human_review"


class OCRJob(Base):
    """Tracks OCR extraction jobs"""

    __tablename__ = "ocr_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    document_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # SHA-256
    status: Mapped[OCRStatus] = mapped_column(
        Enum(OCRStatus), nullable=False, default=OCRStatus.PENDING, index=True
    )

    # Processing details
    tier_used: Mapped[Optional[OCRTier]] = mapped_column(Enum(OCRTier), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Document metadata
    document_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Extraction results
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_fields: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Processing metadata
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tesseract_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    warnings: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audit trail
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Index for efficient queries
    __table_args__ = (
        Index("idx_tenant_status", "tenant_id", "status"),
        Index("idx_tenant_created", "tenant_id", "created_at"),
    )


class OCRReview(Base):
    """Human review corrections for OCR results"""

    __tablename__ = "ocr_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)

    # Review details
    reviewer_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    reviewed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    # Corrections
    corrected_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrected_fields: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Review metadata
    review_time_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence_after_review: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)

    __table_args__ = (Index("idx_job_reviewer", "job_id", "reviewer_id"),)


class OCRCache(Base):
    """Cache for OCR results to avoid reprocessing"""

    __tablename__ = "ocr_cache"

    document_hash: Mapped[str] = mapped_column(String(64), primary_key=True)

    # Cached results
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    tier_used: Mapped[OCRTier] = mapped_column(Enum(OCRTier), nullable=False)

    # Metadata
    document_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    processing_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    # Cache management
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
