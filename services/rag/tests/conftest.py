"""
pytest configuration and fixtures for RAG service tests.

Provides fixtures for:
- Database sessions with test schema
- FastAPI test client
- Mock embeddings and documents
- Authentication headers
"""

import os
import sys
from typing import Generator, List
from unittest.mock import Mock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import get_db
from app.main import app
from app.models import Base, Chunk, Document

# Test database configuration
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql://cortx:cortx_dev_password@127.0.0.1:5432/cortx_test"
)


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine for entire test session."""
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True, echo=False)

    # Create extensions and schema
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS rag"))

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS rag CASCADE"))

    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a new database session for each test."""
    Session = sessionmaker(bind=db_engine)
    session = Session()

    try:
        yield session
    finally:
        # Rollback any uncommitted changes
        session.rollback()

        # Clean up test data
        session.execute(
            text(
                "TRUNCATE rag.chunks, rag.documents, rag.conversations, rag.messages, rag.kb_stats, rag.query_cache RESTART IDENTITY CASCADE"
            )
        )
        session.commit()
        session.close()


@pytest.fixture
def client(db_session) -> TestClient:
    """Create FastAPI test client with test database."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Disable auth for tests by default
    os.environ["REQUIRE_AUTH"] = "false"

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict:
    """Generate auth headers for testing."""
    # Mock JWT token payload
    return {
        "Authorization": "Bearer test_token",
        "X-Tenant-ID": "test_tenant",
        "X-User-ID": "test_user",
    }


@pytest.fixture
def mock_embedding_model():
    """Mock sentence transformer model for tests."""
    with patch("app.embeddings.load_model") as mock_load:
        mock_model = Mock()

        def mock_encode(texts, **kwargs):
            """Generate deterministic fake embeddings."""
            if isinstance(texts, str):
                texts = [texts]

            # Generate deterministic embeddings based on text hash
            embeddings = []
            for text in texts:
                # Use hash to generate reproducible random vector
                np.random.seed(hash(text) % (2**32))
                embedding = np.random.randn(384)
                # Normalize
                embedding = embedding / np.linalg.norm(embedding)
                embeddings.append(embedding)

            if len(embeddings) == 1 and isinstance(texts, str):
                return embeddings[0]
            return np.array(embeddings)

        mock_model.encode = mock_encode
        mock_load.return_value = mock_model

        yield mock_model


@pytest.fixture
def sample_text() -> str:
    """Sample text for chunking and embedding tests."""
    return """# Introduction to NIST 800-53

The NIST Special Publication 800-53 provides a catalog of security and privacy controls for federal information systems and organizations.

## Access Control (AC)

Access control policies ensure that only authorized users can access system resources. Organizations must implement role-based access control (RBAC) to enforce least privilege principles.

### AC-1: Access Control Policy and Procedures

Organizations must develop, document, and disseminate access control policies that address purpose, scope, roles, responsibilities, and compliance.

## Audit and Accountability (AU)

Audit controls ensure that system activities are tracked and can be reviewed for security incidents.

### AU-1: Audit and Accountability Policy

Organizations must establish audit policies that define what events are logged and how logs are protected.

### AU-2: Event Logging

Systems must log security-relevant events including successful and failed authentication attempts, access to sensitive data, and administrative actions.

## Conclusion

Compliance with NIST 800-53 is essential for federal agencies and contractors handling sensitive information.
"""


@pytest.fixture
def sample_document(db_session: Session) -> Document:
    """Create a sample document in the database."""
    doc = Document(
        tenant_id="test_tenant",
        level="platform",
        suite_id=None,
        module_id=None,
        title="NIST 800-53 Security Controls",
        description="Federal security controls catalog",
        source_type="markdown",
        access_level="public",
        status="active",
        doc_metadata={"uploaded_by": "test_user", "tags": ["compliance", "nist", "security"]},
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


@pytest.fixture
def sample_chunks(
    db_session: Session, sample_document: Document, mock_embedding_model
) -> List[Chunk]:
    """Create sample chunks with embeddings."""
    from app.embeddings import generate_embeddings_batch

    chunk_contents = [
        "The NIST Special Publication 800-53 provides a catalog of security and privacy controls.",
        "Access control policies ensure that only authorized users can access system resources.",
        "Organizations must implement role-based access control (RBAC).",
        "Audit controls ensure that system activities are tracked and reviewed.",
        "Systems must log security-relevant events including authentication attempts.",
    ]

    embeddings = generate_embeddings_batch(chunk_contents)

    chunks = []
    for i, (content, embedding) in enumerate(zip(chunk_contents, embeddings)):
        chunk = Chunk(
            document_id=sample_document.id,
            ord=i,
            content=content,
            content_hash=Chunk.compute_hash(content),
            heading="Access Control" if i < 3 else "Audit and Accountability",
            token_count=len(content.split()),
            embedding=embedding,
        )
        db_session.add(chunk)
        chunks.append(chunk)

    db_session.commit()

    for chunk in chunks:
        db_session.refresh(chunk)

    return chunks


@pytest.fixture
def suite_document(db_session: Session) -> Document:
    """Create a suite-level document."""
    doc = Document(
        tenant_id="test_tenant",
        level="suite",
        suite_id="fedsuite",
        module_id=None,
        title="FedSuite Compliance Guide",
        description="Federal compliance guidelines",
        source_type="markdown",
        access_level="internal",
        status="active",
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


@pytest.fixture
def module_document(db_session: Session) -> Document:
    """Create a module-level document."""
    doc = Document(
        tenant_id="test_tenant",
        level="module",
        suite_id="fedsuite",
        module_id="dataflow",
        title="DataFlow Module Documentation",
        description="DataFlow module specific docs",
        source_type="markdown",
        access_level="internal",
        status="active",
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


@pytest.fixture
def mock_ai_broker(monkeypatch):
    """Mock AI Broker responses."""

    async def mock_post(*args, **kwargs):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "text": "This is a test response from the AI Broker.",
            "model": "gemini-1.5-flash",
            "tokens_used": 150,
        }
        response.raise_for_status = Mock()
        return response

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        yield


@pytest.fixture
def clean_env():
    """Clean environment variables for tests."""
    original_env = os.environ.copy()

    # Set test environment
    os.environ["REQUIRE_AUTH"] = "false"
    os.environ["CORTX_AI_BROKER_URL"] = "http://ai-broker-test:8085"

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
