"""
Pytest configuration and shared fixtures for OCR service tests
"""

import base64
import uuid
from io import BytesIO
from typing import Generator

import pytest
from app.database import get_db_session
from app.main import app
from app.models import Base, OCRCache, OCRJob, OCRReview, OCRStatus, OCRTier
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine"""
    # Use in-memory SQLite for tests
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, echo=False
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create test database session"""
    TestSessionLocal = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session):
    """Create test client with database override"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_image() -> Image.Image:
    """Create a simple test image with text"""
    img = Image.new("RGB", (800, 600), color="white")
    draw = ImageDraw.Draw(img)

    # Draw some text (using default font)
    text = "Sample Invoice\nInvoice #12345\nDate: 2025-10-07\nAmount: $1,234.56"
    draw.text((50, 50), text, fill="black")

    # Draw some shapes to simulate document structure
    draw.rectangle([40, 40, 760, 150], outline="black", width=2)
    draw.line([40, 90, 760, 90], fill="black", width=1)

    return img


@pytest.fixture
def sample_image_base64(sample_image) -> str:
    """Convert sample image to base64"""
    buffer = BytesIO()
    sample_image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


@pytest.fixture
def sample_degraded_image() -> Image.Image:
    """Create a degraded/low quality test image"""
    img = Image.new("RGB", (400, 300), color="gray")
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "Low Quality Text", fill="darkgray")
    return img


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Create a simple PDF for testing (mock)"""
    # For testing, we'll use a minimal PDF-like structure
    # In real tests, you'd use reportlab or similar to create actual PDFs
    return b"%PDF-1.4\n%Mock PDF for testing\n%%EOF"


@pytest.fixture
def sample_document_hash() -> str:
    """Generate a sample SHA-256 hash"""
    return "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


# ============================================================================
# OCR Result Fixtures
# ============================================================================


@pytest.fixture
def sample_extracted_text() -> str:
    """Sample extracted text from OCR"""
    return """Sample Invoice
Invoice #12345
Date: 2025-10-07
Amount: $1,234.56

Items:
- Product A: $500.00
- Product B: $734.56

Total: $1,234.56"""


@pytest.fixture
def sample_extracted_fields() -> dict:
    """Sample extracted structured fields"""
    return {
        "invoice_number": "12345",
        "date": "2025-10-07",
        "amount": 1234.56,
        "currency": "USD",
        "items": [{"name": "Product A", "price": 500.00}, {"name": "Product B", "price": 734.56}],
    }


@pytest.fixture
def sample_tesseract_data() -> dict:
    """Sample Tesseract output data"""
    return {
        "text": ["Sample", "Invoice", "#12345", "Date:", "2025-10-07", "", "Amount:", "$1,234.56"],
        "conf": [95, 92, 88, 94, 90, -1, 93, 85],
        "line_num": [1, 1, 2, 3, 3, 4, 5, 5],
        "block_num": [1, 1, 1, 1, 1, 2, 2, 2],
    }


@pytest.fixture
def sample_low_confidence_tesseract_data() -> dict:
    """Sample Tesseract output with low confidence"""
    return {
        "text": ["Unclear", "Handwritten", "Text"],
        "conf": [45, 38, 52],
        "line_num": [1, 1, 2],
        "block_num": [1, 1, 1],
    }


# ============================================================================
# Database Model Fixtures
# ============================================================================


@pytest.fixture
def sample_ocr_job(db_session) -> OCRJob:
    """Create a sample OCR job in database"""
    job = OCRJob(
        id=uuid.uuid4(),
        tenant_id="test-tenant",
        document_hash="sample-hash-123",
        status=OCRStatus.PENDING,
        document_type="image/png",
        user_id="test-user",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture
def completed_ocr_job(db_session, sample_extracted_text) -> OCRJob:
    """Create a completed OCR job in database"""
    job = OCRJob(
        id=uuid.uuid4(),
        tenant_id="test-tenant",
        document_hash="completed-hash-456",
        status=OCRStatus.COMPLETED,
        tier_used=OCRTier.TESSERACT,
        confidence_score=95.0,
        extracted_text=sample_extracted_text,
        document_type="image/png",
        page_count=1,
        processing_time_ms=250,
        tesseract_confidence=95.0,
        user_id="test-user",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture
def review_pending_job(db_session) -> OCRJob:
    """Create a job awaiting human review"""
    job = OCRJob(
        id=uuid.uuid4(),
        tenant_id="test-tenant",
        document_hash="review-hash-789",
        status=OCRStatus.AWAITING_REVIEW,
        tier_used=OCRTier.AI_VISION,
        confidence_score=72.0,
        extracted_text="Low confidence text",
        document_type="image/png",
        page_count=1,
        processing_time_ms=1500,
        ai_confidence=72.0,
        user_id="test-user",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture
def sample_cache_entry(db_session, sample_extracted_text) -> OCRCache:
    """Create a sample cache entry"""
    cache = OCRCache(
        document_hash="cached-hash-111",
        extracted_text=sample_extracted_text,
        extracted_fields={"invoice_number": "12345"},
        confidence_score=95.0,
        tier_used=OCRTier.TESSERACT,
        document_type="image/png",
        page_count=1,
        processing_time_ms=200,
        hit_count=0,
    )
    db_session.add(cache)
    db_session.commit()
    db_session.refresh(cache)
    return cache


@pytest.fixture
def sample_review(db_session, review_pending_job) -> OCRReview:
    """Create a sample review record"""
    review = OCRReview(
        id=uuid.uuid4(),
        job_id=review_pending_job.id,
        reviewer_id="reviewer-123",
        corrected_text="Corrected text after review",
        corrected_fields={"field1": "value1"},
        review_notes="Fixed OCR errors",
        review_time_seconds=120,
        confidence_after_review=100.0,
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)
    return review


# ============================================================================
# API Request Fixtures
# ============================================================================


@pytest.fixture
def sample_ocr_request(sample_document_hash, sample_image_base64) -> dict:
    """Sample OCR request payload"""
    return {
        "document_hash": sample_document_hash,
        "document_data": sample_image_base64,
        "document_type": "image/png",
        "tenant_id": "test-tenant",
        "user_id": "test-user",
        "require_review": False,
        "correlation_id": "test-correlation-123",
    }


@pytest.fixture
def sample_review_request() -> dict:
    """Sample review submission payload"""
    return {
        "reviewer_id": "reviewer-456",
        "corrected_text": "Corrected OCR text",
        "corrected_fields": {"name": "John Doe", "amount": 1500.00},
        "review_notes": "Fixed multiple OCR errors",
        "review_time_seconds": 180,
    }


# ============================================================================
# Environment Fixtures
# ============================================================================


@pytest.fixture
def mock_tesseract_available(monkeypatch):
    """Mock Tesseract availability"""

    def mock_version():
        return "5.3.0"

    monkeypatch.setattr("pytesseract.get_tesseract_version", mock_version)


@pytest.fixture
def mock_anthropic_key(monkeypatch):
    """Mock Anthropic API key in environment"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key-12345")


@pytest.fixture
def mock_no_anthropic_key(monkeypatch):
    """Remove Anthropic API key from environment"""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


# ============================================================================
# Utility Fixtures
# ============================================================================


@pytest.fixture
def freeze_time():
    """Fixture to freeze time for consistent testing"""
    from freezegun import freeze_time

    with freeze_time("2025-10-07 12:00:00"):
        yield


@pytest.fixture
def mock_uuid():
    """Fixture to generate predictable UUIDs"""
    test_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
    return test_uuid
