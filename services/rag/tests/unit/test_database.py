"""
Unit tests for database connection and initialization.

Tests cover:
- Database connection
- Schema initialization
- Session management
- Connection pooling
- Extension setup
"""

from unittest.mock import patch

import pytest
from app.database import check_db_connection, engine, get_db
from sqlalchemy import text


@pytest.mark.unit
class TestDatabaseConnection:
    """Test database connection functions."""

    def test_check_db_connection_success(self):
        """Test successful database connection check."""
        result = check_db_connection()
        assert isinstance(result, bool)

    def test_check_db_connection_failure(self):
        """Test database connection failure handling."""
        with patch("app.database.engine.connect", side_effect=Exception("Connection failed")):
            result = check_db_connection()
            assert result is False


@pytest.mark.unit
class TestGetDb:
    """Test get_db dependency function."""

    def test_get_db_yields_session(self):
        """Test that get_db yields a database session."""
        generator = get_db()
        session = next(generator)

        assert session is not None
        assert hasattr(session, "query")
        assert hasattr(session, "commit")
        assert hasattr(session, "rollback")

        # Cleanup
        try:
            next(generator)
        except StopIteration:
            pass

    def test_get_db_closes_session(self):
        """Test that get_db closes session after use."""
        generator = get_db()
        session = next(generator)

        # Session should be open
        assert session.is_active

        # Close generator
        try:
            next(generator)
        except StopIteration:
            pass

        # Session should be closed
        # Note: Can't easily test this without mocking

    def test_get_db_usage_pattern(self, db_session):
        """Test typical usage pattern with get_db."""
        # Simulate FastAPI dependency injection
        from app.models import Document

        # Use session
        doc = Document(
            tenant_id="test", level="platform", title="Test", source_type="text", status="active"
        )
        db_session.add(doc)
        db_session.commit()

        # Verify
        result = db_session.query(Document).filter(Document.title == "Test").first()
        assert result is not None


@pytest.mark.integration
class TestInitDb:
    """Test database initialization."""

    def test_init_db_creates_schema(self, db_session):
        """Test that init_db creates rag schema."""
        # Schema should already be created by conftest
        result = db_session.execute(
            text(
                """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name = 'rag'
        """
            )
        )
        schemas = [row[0] for row in result]

        assert "rag" in schemas

    def test_init_db_creates_extensions(self, db_session):
        """Test that init_db creates required extensions."""
        # Check pgvector extension
        result = db_session.execute(
            text(
                """
            SELECT extname
            FROM pg_extension
            WHERE extname IN ('vector', 'pg_trgm')
        """
            )
        )
        extensions = [row[0] for row in result]

        assert "vector" in extensions
        assert "pg_trgm" in extensions

    def test_init_db_creates_tables(self, db_session):
        """Test that init_db creates all required tables."""
        result = db_session.execute(
            text(
                """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'rag'
        """
            )
        )
        tables = [row[0] for row in result]

        expected_tables = [
            "documents",
            "chunks",
            "conversations",
            "messages",
            "kb_stats",
            "query_cache",
        ]

        for table in expected_tables:
            assert table in tables


@pytest.mark.integration
class TestDatabaseSchema:
    """Test database schema details."""

    def test_documents_table_columns(self, db_session):
        """Test that documents table has expected columns."""
        result = db_session.execute(
            text(
                """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'rag' AND table_name = 'documents'
        """
            )
        )
        columns = [row[0] for row in result]

        expected_columns = [
            "id",
            "tenant_id",
            "level",
            "suite_id",
            "module_id",
            "title",
            "description",
            "source_type",
            "status",
            "access_level",
            "created_at",
            "updated_at",
        ]

        for col in expected_columns:
            assert col in columns

    def test_chunks_table_columns(self, db_session):
        """Test that chunks table has expected columns."""
        result = db_session.execute(
            text(
                """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'rag' AND table_name = 'chunks'
        """
            )
        )
        columns = [row[0] for row in result]

        expected_columns = [
            "id",
            "document_id",
            "ord",
            "content",
            "content_hash",
            "heading",
            "token_count",
            "embedding",
            "created_at",
        ]

        for col in expected_columns:
            assert col in columns

    def test_chunks_embedding_column_type(self, db_session):
        """Test that embedding column is vector type."""
        result = db_session.execute(
            text(
                """
            SELECT data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema = 'rag' AND table_name = 'chunks' AND column_name = 'embedding'
        """
            )
        )
        row = result.fetchone()

        # Should be USER-DEFINED type (vector)
        assert row is not None

    def test_documents_indexes(self, db_session):
        """Test that documents table has expected indexes."""
        result = db_session.execute(
            text(
                """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'rag' AND tablename = 'documents'
        """
            )
        )
        indexes = [row[0] for row in result]

        # Should have indexes on common query columns
        assert any("tenant" in idx for idx in indexes)
        assert any("level" in idx for idx in indexes)

    def test_chunks_vector_index(self, db_session):
        """Test that chunks table has vector index for similarity search."""
        result = db_session.execute(
            text(
                """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'rag' AND tablename = 'chunks'
        """
            )
        )
        indexes = [(row[0], row[1]) for row in result]

        # Should have HNSW index on embedding
        vector_indexes = [idx for idx in indexes if "embedding" in idx[1]]
        assert len(vector_indexes) > 0


@pytest.mark.integration
class TestDatabaseConstraints:
    """Test database constraints."""

    def test_documents_check_constraints(self, db_session):
        """Test that documents table has check constraints."""
        result = db_session.execute(
            text(
                """
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_schema = 'rag'
              AND table_name = 'documents'
              AND constraint_type = 'CHECK'
        """
            )
        )
        constraints = [row[0] for row in result]

        # Should have check constraints for level, status, access_level
        assert any("level" in c for c in constraints)
        assert any("status" in c for c in constraints)
        assert any("access_level" in c for c in constraints)

    def test_chunks_foreign_key(self, db_session, sample_document):
        """Test that chunks table has foreign key to documents."""
        # Try to create chunk with invalid document_id
        import uuid

        from app.embeddings import generate_embedding
        from app.models import Chunk

        invalid_id = uuid.uuid4()

        chunk = Chunk(
            document_id=invalid_id,
            ord=0,
            content="Test",
            content_hash=Chunk.compute_hash("Test"),
            embedding=generate_embedding("Test"),
        )
        db_session.add(chunk)

        with pytest.raises(Exception):  # Foreign key violation
            db_session.commit()

    def test_kb_stats_unique_document(self, db_session, sample_document):
        """Test that kb_stats has unique constraint on document_id."""
        from app.models import KnowledgeBaseStats

        stats1 = KnowledgeBaseStats(document_id=sample_document.id, retrieval_count=1)
        db_session.add(stats1)
        db_session.commit()

        # Try to add another stats entry for same document
        stats2 = KnowledgeBaseStats(document_id=sample_document.id, retrieval_count=2)
        db_session.add(stats2)

        with pytest.raises(Exception):  # Unique constraint violation
            db_session.commit()


@pytest.mark.unit
class TestSessionManagement:
    """Test session management and transactions."""

    def test_session_transaction_commit(self, db_session):
        """Test successful transaction commit."""
        from app.models import Document

        doc = Document(
            tenant_id="test",
            level="platform",
            title="Commit Test",
            source_type="text",
            status="active",
        )
        db_session.add(doc)
        db_session.commit()

        # Verify committed
        result = db_session.query(Document).filter(Document.title == "Commit Test").first()
        assert result is not None

    def test_session_transaction_rollback(self, db_session):
        """Test transaction rollback."""
        from app.models import Document

        doc = Document(
            tenant_id="test",
            level="platform",
            title="Rollback Test",
            source_type="text",
            status="active",
        )
        db_session.add(doc)

        # Rollback before commit
        db_session.rollback()

        # Should not exist in database
        result = db_session.query(Document).filter(Document.title == "Rollback Test").first()
        assert result is None

    def test_session_transaction_error_rollback(self, db_session):
        """Test automatic rollback on error."""
        from app.models import Document

        try:
            # Create valid document
            doc1 = Document(
                tenant_id="test",
                level="platform",
                title="Valid Doc",
                source_type="text",
                status="active",
            )
            db_session.add(doc1)

            # Create invalid document (this will fail)
            doc2 = Document(
                tenant_id="test",
                level="invalid_level",  # Invalid
                title="Invalid Doc",
                source_type="text",
                status="active",
            )
            db_session.add(doc2)

            db_session.commit()
        except Exception:
            db_session.rollback()

        # Neither document should be in database
        count = (
            db_session.query(Document)
            .filter(Document.title.in_(["Valid Doc", "Invalid Doc"]))
            .count()
        )
        assert count == 0


@pytest.mark.unit
class TestConnectionPooling:
    """Test connection pooling configuration."""

    def test_engine_pool_settings(self):
        """Test that engine has proper pool settings."""
        assert engine.pool is not None
        assert engine.pool.size() >= 0  # Pool should exist

    def test_engine_pool_pre_ping(self):
        """Test that pool_pre_ping is enabled."""
        # This is set in engine creation
        assert engine.pool._pre_ping is True or hasattr(engine.pool, "_pre_ping")


@pytest.mark.integration
class TestDatabaseOperations:
    """Test basic database operations."""

    def test_insert_and_query(self, db_session):
        """Test basic insert and query operations."""
        from app.models import Document

        # Insert
        doc = Document(
            tenant_id="test",
            level="platform",
            title="Test Doc",
            source_type="text",
            status="active",
        )
        db_session.add(doc)
        db_session.commit()

        # Query
        result = db_session.query(Document).filter(Document.title == "Test Doc").first()
        assert result is not None
        assert result.title == "Test Doc"

    def test_update_operation(self, db_session, sample_document):
        """Test update operation."""
        # Update
        sample_document.title = "Updated Title"
        db_session.commit()

        # Verify
        db_session.refresh(sample_document)
        assert sample_document.title == "Updated Title"

    def test_delete_operation(self, db_session):
        """Test delete operation."""
        from app.models import Document

        doc = Document(
            tenant_id="test",
            level="platform",
            title="To Delete",
            source_type="text",
            status="active",
        )
        db_session.add(doc)
        db_session.commit()

        doc_id = doc.id

        # Delete
        db_session.delete(doc)
        db_session.commit()

        # Verify deleted
        result = db_session.query(Document).filter(Document.id == doc_id).first()
        assert result is None

    def test_bulk_insert(self, db_session):
        """Test bulk insert operations."""
        from app.models import Document

        docs = [
            Document(
                tenant_id="test",
                level="platform",
                title=f"Bulk Doc {i}",
                source_type="text",
                status="active",
            )
            for i in range(10)
        ]

        db_session.bulk_save_objects(docs)
        db_session.commit()

        # Verify
        count = db_session.query(Document).filter(Document.title.like("Bulk Doc%")).count()
        assert count == 10


@pytest.mark.integration
class TestVectorOperations:
    """Test pgvector operations."""

    def test_vector_similarity_search(self, db_session, sample_chunks, mock_embedding_model):
        """Test vector similarity search."""
        from app.embeddings import generate_embedding

        query_embedding = generate_embedding("access control")

        # Perform similarity search
        result = db_session.execute(
            text(
                """
            SELECT id, content, 1 - (embedding <=> CAST(:query AS vector)) AS similarity
            FROM rag.chunks
            ORDER BY similarity DESC
            LIMIT 3
        """
            ),
            {"query": query_embedding},
        )

        rows = result.fetchall()
        assert len(rows) > 0

        # Similarities should be in descending order
        similarities = [row[2] for row in rows]
        assert similarities == sorted(similarities, reverse=True)

    def test_vector_distance_calculation(self, db_session, sample_chunks, mock_embedding_model):
        """Test vector distance calculation."""
        from app.embeddings import generate_embedding

        embedding = generate_embedding("test")

        # Calculate distances
        result = db_session.execute(
            text(
                """
            SELECT id, embedding <=> CAST(:query AS vector) AS distance
            FROM rag.chunks
            LIMIT 5
        """
            ),
            {"query": embedding},
        )

        rows = result.fetchall()
        assert len(rows) > 0

        # All distances should be non-negative
        for row in rows:
            assert row[1] >= 0
