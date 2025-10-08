"""
Unit tests for database models.

Tests cover:
- Document model creation and validation
- Chunk model with hash computation
- Conversation and Message models
- KnowledgeBaseStats model
- QueryCache model
- Model relationships
"""

import uuid
from datetime import datetime, timedelta

import pytest
from app.models import Chunk, Conversation, Document, KnowledgeBaseStats, Message, QueryCache
from sqlalchemy.exc import IntegrityError


@pytest.mark.unit
class TestDocumentModel:
    """Test Document model."""

    def test_document_creation(self, db_session):
        """Test creating a basic document."""
        doc = Document(
            tenant_id="test_tenant",
            level="platform",
            title="Test Document",
            source_type="markdown",
            access_level="public",
            status="active",
        )
        db_session.add(doc)
        db_session.commit()

        assert doc.id is not None
        assert isinstance(doc.id, uuid.UUID)
        assert doc.created_at is not None
        assert doc.updated_at is not None

    def test_document_levels(self, db_session):
        """Test all hierarchy levels."""
        levels = ["platform", "suite", "module", "entity"]

        for level in levels:
            doc = Document(
                tenant_id="test",
                level=level,
                title=f"{level} doc",
                source_type="text",
                status="active",
            )
            db_session.add(doc)

        db_session.commit()

        # All should be created successfully
        docs = db_session.query(Document).all()
        assert len(docs) == len(levels)

    def test_document_status_values(self, db_session):
        """Test valid status values."""
        statuses = ["active", "archived", "deleted"]

        for status in statuses:
            doc = Document(
                tenant_id="test",
                level="platform",
                title=f"Doc {status}",
                source_type="text",
                status=status,
            )
            db_session.add(doc)

        db_session.commit()

        docs = db_session.query(Document).all()
        assert len(docs) == len(statuses)

    def test_document_access_levels(self, db_session):
        """Test valid access levels."""
        access_levels = ["public", "internal", "confidential", "restricted"]

        for access in access_levels:
            doc = Document(
                tenant_id="test",
                level="platform",
                title=f"Doc {access}",
                source_type="text",
                access_level=access,
                status="active",
            )
            db_session.add(doc)

        db_session.commit()

        docs = db_session.query(Document).all()
        assert len(docs) == len(access_levels)

    def test_document_with_hierarchy(self, db_session):
        """Test document with full hierarchy context."""
        doc = Document(
            tenant_id="tenant_1",
            level="module",
            suite_id="fedsuite",
            module_id="dataflow",
            title="DataFlow Documentation",
            description="Module-specific docs",
            source_type="markdown",
            access_level="internal",
            status="active",
        )
        db_session.add(doc)
        db_session.commit()

        assert doc.suite_id == "fedsuite"
        assert doc.module_id == "dataflow"
        assert doc.level == "module"

    def test_document_metadata(self, db_session):
        """Test document with JSONB metadata."""
        metadata = {
            "uploaded_by": "test_user",
            "tags": ["compliance", "security"],
            "version": "1.0.0",
        }

        doc = Document(
            tenant_id="test",
            level="platform",
            title="Test",
            source_type="text",
            doc_metadata=metadata,
            status="active",
        )
        db_session.add(doc)
        db_session.commit()

        # Refresh from database
        db_session.refresh(doc)

        assert doc.doc_metadata == metadata
        assert "uploaded_by" in doc.doc_metadata

    def test_document_repr(self, db_session):
        """Test document string representation."""
        doc = Document(
            tenant_id="test",
            level="platform",
            title="Test Document",
            source_type="text",
            status="active",
        )
        db_session.add(doc)
        db_session.commit()

        repr_str = repr(doc)
        assert "Document" in repr_str
        assert "Test Document" in repr_str
        assert "platform" in repr_str


@pytest.mark.unit
class TestChunkModel:
    """Test Chunk model."""

    def test_chunk_creation(self, db_session, sample_document, mock_embedding_model):
        """Test creating a chunk."""
        from app.embeddings import generate_embedding

        content = "Test chunk content."
        embedding = generate_embedding(content)

        chunk = Chunk(
            document_id=sample_document.id,
            ord=0,
            content=content,
            content_hash=Chunk.compute_hash(content),
            heading="Test Heading",
            token_count=4,
            embedding=embedding,
        )
        db_session.add(chunk)
        db_session.commit()

        assert chunk.id is not None
        assert chunk.document_id == sample_document.id
        assert chunk.ord == 0

    def test_chunk_hash_computation(self):
        """Test hash computation for content."""
        content1 = "This is test content."
        content2 = "This is test content."
        content3 = "Different content."

        hash1 = Chunk.compute_hash(content1)
        hash2 = Chunk.compute_hash(content2)
        hash3 = Chunk.compute_hash(content3)

        # Same content should produce same hash
        assert hash1 == hash2

        # Different content should produce different hash
        assert hash1 != hash3

        # Hash should be SHA256 (64 hex characters)
        assert len(hash1) == 64

    def test_chunk_with_vector_embedding(self, db_session, sample_document, mock_embedding_model):
        """Test chunk with pgvector embedding."""
        from app.embeddings import generate_embedding

        embedding = generate_embedding("Test content")

        chunk = Chunk(
            document_id=sample_document.id,
            ord=0,
            content="Test",
            content_hash=Chunk.compute_hash("Test"),
            embedding=embedding,
        )
        db_session.add(chunk)
        db_session.commit()

        # Refresh and check
        db_session.refresh(chunk)
        assert chunk.embedding is not None
        assert len(chunk.embedding) == 384  # Embedding dimension

    def test_chunk_relationship_to_document(self, db_session, sample_document, sample_chunks):
        """Test chunk-document relationship."""
        # Document should have chunks
        assert len(sample_document.chunks) > 0

        # Each chunk should reference document
        for chunk in sample_chunks:
            assert chunk.document_id == sample_document.id
            assert chunk.document == sample_document

    def test_chunk_cascade_delete(self, db_session, sample_document, sample_chunks):
        """Test that deleting document deletes chunks."""
        chunk_ids = [chunk.id for chunk in sample_chunks]

        # Delete document
        db_session.delete(sample_document)
        db_session.commit()

        # Chunks should be deleted
        remaining = db_session.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()
        assert len(remaining) == 0

    def test_chunk_metadata(self, db_session, sample_document, mock_embedding_model):
        """Test chunk with metadata."""
        from app.embeddings import generate_embedding

        metadata = {"source_page": 42, "extraction_method": "automated"}

        chunk = Chunk(
            document_id=sample_document.id,
            ord=0,
            content="Test",
            content_hash=Chunk.compute_hash("Test"),
            embedding=generate_embedding("Test"),
            chunk_metadata=metadata,
        )
        db_session.add(chunk)
        db_session.commit()

        db_session.refresh(chunk)
        assert chunk.chunk_metadata == metadata


@pytest.mark.unit
class TestConversationModel:
    """Test Conversation model."""

    def test_conversation_creation(self, db_session):
        """Test creating a conversation."""
        conv = Conversation(
            user_id="user_1",
            tenant_id="tenant_1",
            suite_id="fedsuite",
            module_id="dataflow",
            title="Test Conversation",
            message_count=0,
        )
        db_session.add(conv)
        db_session.commit()

        assert conv.id is not None
        assert conv.started_at is not None
        assert conv.last_message_at is not None

    def test_conversation_with_feedback(self, db_session):
        """Test conversation with user feedback."""
        conv = Conversation(
            user_id="user_1",
            tenant_id="tenant_1",
            feedback_score=5,
            feedback_comment="Very helpful!",
        )
        db_session.add(conv)
        db_session.commit()

        assert conv.feedback_score == 5
        assert conv.feedback_comment == "Very helpful!"

    def test_conversation_metadata(self, db_session):
        """Test conversation with extra metadata."""
        metadata = {"client_info": "web", "session_id": "abc123"}

        conv = Conversation(user_id="user_1", tenant_id="tenant_1", extra_metadata=metadata)
        db_session.add(conv)
        db_session.commit()

        db_session.refresh(conv)
        assert conv.extra_metadata == metadata


@pytest.mark.unit
class TestMessageModel:
    """Test Message model."""

    def test_message_creation(self, db_session):
        """Test creating a message."""
        conv = Conversation(user_id="user_1", tenant_id="tenant_1")
        db_session.add(conv)
        db_session.flush()

        msg = Message(conversation_id=conv.id, role="user", content="What is NIST 800-53?")
        db_session.add(msg)
        db_session.commit()

        assert msg.id is not None
        assert msg.role == "user"
        assert msg.conversation_id == conv.id

    def test_message_roles(self, db_session):
        """Test valid message roles."""
        conv = Conversation(user_id="user_1", tenant_id="tenant_1")
        db_session.add(conv)
        db_session.flush()

        roles = ["user", "assistant", "system"]

        for role in roles:
            msg = Message(conversation_id=conv.id, role=role, content=f"Message from {role}")
            db_session.add(msg)

        db_session.commit()

        messages = db_session.query(Message).filter(Message.conversation_id == conv.id).all()
        assert len(messages) == len(roles)

    def test_message_with_embedding(self, db_session, mock_embedding_model):
        """Test message with query embedding."""
        from app.embeddings import generate_embedding

        conv = Conversation(user_id="user_1", tenant_id="tenant_1")
        db_session.add(conv)
        db_session.flush()

        embedding = generate_embedding("Test query")

        msg = Message(
            conversation_id=conv.id, role="user", content="Test query", query_embedding=embedding
        )
        db_session.add(msg)
        db_session.commit()

        db_session.refresh(msg)
        assert msg.query_embedding is not None

    def test_message_with_response_metadata(self, db_session):
        """Test assistant message with response metadata."""
        conv = Conversation(user_id="user_1", tenant_id="tenant_1")
        db_session.add(conv)
        db_session.flush()

        msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content="Here's the answer...",
            model="gemini-1.5-flash",
            tokens_used=150,
            chunks_retrieved=5,
            document_ids=["doc1", "doc2"],
            chunk_ids=["chunk1", "chunk2", "chunk3"],
        )
        db_session.add(msg)
        db_session.commit()

        assert msg.model == "gemini-1.5-flash"
        assert msg.tokens_used == 150
        assert msg.chunks_retrieved == 5
        assert len(msg.document_ids) == 2

    def test_message_relationship_to_conversation(self, db_session):
        """Test message-conversation relationship."""
        conv = Conversation(user_id="user_1", tenant_id="tenant_1")
        db_session.add(conv)
        db_session.flush()

        msg1 = Message(conversation_id=conv.id, role="user", content="Question 1")
        msg2 = Message(conversation_id=conv.id, role="assistant", content="Answer 1")
        db_session.add_all([msg1, msg2])
        db_session.commit()

        # Conversation should have messages
        db_session.refresh(conv)
        assert len(conv.messages) == 2

    def test_message_cascade_delete(self, db_session):
        """Test that deleting conversation deletes messages."""
        conv = Conversation(user_id="user_1", tenant_id="tenant_1")
        db_session.add(conv)
        db_session.flush()

        msg = Message(conversation_id=conv.id, role="user", content="Test")
        db_session.add(msg)
        db_session.commit()

        msg_id = msg.id

        # Delete conversation
        db_session.delete(conv)
        db_session.commit()

        # Message should be deleted
        remaining = db_session.query(Message).filter(Message.id == msg_id).first()
        assert remaining is None


@pytest.mark.unit
class TestKnowledgeBaseStatsModel:
    """Test KnowledgeBaseStats model."""

    def test_kb_stats_creation(self, db_session, sample_document):
        """Test creating KB stats entry."""
        stats = KnowledgeBaseStats(
            document_id=sample_document.id, retrieval_count=10, citation_count=5, view_count=20
        )
        db_session.add(stats)
        db_session.commit()

        assert stats.id is not None
        assert stats.retrieval_count == 10

    def test_kb_stats_quality_metrics(self, db_session, sample_document):
        """Test quality metrics in KB stats."""
        stats = KnowledgeBaseStats(
            document_id=sample_document.id,
            avg_feedback_score=4.5,
            positive_feedback_count=10,
            negative_feedback_count=2,
        )
        db_session.add(stats)
        db_session.commit()

        assert stats.avg_feedback_score == 4.5
        assert stats.positive_feedback_count == 10

    def test_kb_stats_recency(self, db_session, sample_document):
        """Test recency timestamps in KB stats."""
        now = datetime.utcnow()

        stats = KnowledgeBaseStats(
            document_id=sample_document.id,
            last_retrieved_at=now,
            last_cited_at=now,
            last_viewed_at=now,
        )
        db_session.add(stats)
        db_session.commit()

        assert stats.last_retrieved_at is not None
        assert stats.updated_at is not None

    def test_kb_stats_unique_document(self, db_session, sample_document):
        """Test that each document can have only one stats entry."""
        stats1 = KnowledgeBaseStats(document_id=sample_document.id, retrieval_count=1)
        db_session.add(stats1)
        db_session.commit()

        # Try to add duplicate
        stats2 = KnowledgeBaseStats(document_id=sample_document.id, retrieval_count=2)
        db_session.add(stats2)

        with pytest.raises(IntegrityError):
            db_session.commit()


@pytest.mark.unit
class TestQueryCacheModel:
    """Test QueryCache model."""

    def test_query_cache_creation(self, db_session, mock_embedding_model):
        """Test creating query cache entry."""
        from app.embeddings import generate_embedding

        query = "What is NIST 800-53?"
        embedding = generate_embedding(query)

        cache = QueryCache(
            query_text=query,
            query_hash=QueryCache.compute_query_hash(query),
            query_embedding=embedding,
            tenant_id="tenant_1",
            response_text="NIST 800-53 is...",
            model="gemini-1.5-flash",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db_session.add(cache)
        db_session.commit()

        assert cache.id is not None
        assert cache.hit_count == 0

    def test_query_cache_hash_computation(self):
        """Test query hash computation."""
        query1 = "What is NIST 800-53?"
        query2 = "What is NIST 800-53?"  # Same
        query3 = "what is nist 800-53?"  # Different case

        hash1 = QueryCache.compute_query_hash(query1)
        hash2 = QueryCache.compute_query_hash(query2)
        hash3 = QueryCache.compute_query_hash(query3)

        # Same query should produce same hash
        assert hash1 == hash2

        # Different case should also produce same hash (normalized)
        assert hash1 == hash3

        # Hash should be SHA256
        assert len(hash1) == 64

    def test_query_cache_with_context(self, db_session, mock_embedding_model):
        """Test query cache with suite/module context."""
        from app.embeddings import generate_embedding

        cache = QueryCache(
            query_text="Test query",
            query_hash=QueryCache.compute_query_hash("Test query"),
            query_embedding=generate_embedding("Test query"),
            suite_id="fedsuite",
            module_id="dataflow",
            tenant_id="tenant_1",
            response_text="Response",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db_session.add(cache)
        db_session.commit()

        assert cache.suite_id == "fedsuite"
        assert cache.module_id == "dataflow"

    def test_query_cache_hit_tracking(self, db_session, mock_embedding_model):
        """Test cache hit tracking."""
        from app.embeddings import generate_embedding

        cache = QueryCache(
            query_text="Test",
            query_hash=QueryCache.compute_query_hash("Test"),
            query_embedding=generate_embedding("Test"),
            tenant_id="tenant_1",
            response_text="Response",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db_session.add(cache)
        db_session.commit()

        # Simulate cache hits
        cache.hit_count += 1
        cache.last_accessed_at = datetime.utcnow()
        db_session.commit()

        db_session.refresh(cache)
        assert cache.hit_count == 1

    def test_query_cache_expiration(self, db_session, mock_embedding_model):
        """Test query cache expiration."""
        from app.embeddings import generate_embedding

        # Expired cache entry
        expired_cache = QueryCache(
            query_text="Old query",
            query_hash=QueryCache.compute_query_hash("Old query"),
            query_embedding=generate_embedding("Old query"),
            tenant_id="tenant_1",
            response_text="Old response",
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Already expired
        )
        db_session.add(expired_cache)
        db_session.commit()

        # Query for non-expired entries
        valid_entries = (
            db_session.query(QueryCache).filter(QueryCache.expires_at > datetime.utcnow()).all()
        )

        # Expired entry should not be in results
        assert expired_cache not in valid_entries


@pytest.mark.unit
class TestModelConstraints:
    """Test model constraints and validations."""

    def test_document_invalid_level(self, db_session):
        """Test that invalid document level is rejected."""
        doc = Document(
            tenant_id="test",
            level="invalid_level",  # Invalid
            title="Test",
            source_type="text",
            status="active",
        )
        db_session.add(doc)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_document_invalid_status(self, db_session):
        """Test that invalid status is rejected."""
        doc = Document(
            tenant_id="test",
            level="platform",
            title="Test",
            source_type="text",
            status="invalid_status",  # Invalid
        )
        db_session.add(doc)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_message_invalid_role(self, db_session):
        """Test that invalid message role is rejected."""
        conv = Conversation(user_id="user_1", tenant_id="tenant_1")
        db_session.add(conv)
        db_session.flush()

        msg = Message(conversation_id=conv.id, role="invalid_role", content="Test")  # Invalid
        db_session.add(msg)

        with pytest.raises(IntegrityError):
            db_session.commit()
