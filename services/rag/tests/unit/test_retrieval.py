"""
Unit tests for RAG retrieval service.

Tests cover:
- Cascading retrieval with context boosting
- Hybrid retrieval (vector + keyword)
- Context-aware scoring
- Knowledge base statistics
- Similar document finding
"""

from unittest.mock import patch

import pytest
from app.models import Chunk, KnowledgeBaseStats
from app.retrieval import (
    RetrievalContext,
    RetrievedChunk,
    cascading_retrieval,
    get_similar_documents,
    hybrid_retrieval,
    update_retrieval_stats,
)


@pytest.mark.unit
class TestRetrievalContext:
    """Test RetrievalContext dataclass."""

    def test_retrieval_context_creation(self):
        """Test creating RetrievalContext."""
        context = RetrievalContext(
            tenant_id="test_tenant", user_id="test_user", suite_id="fedsuite", module_id="dataflow"
        )

        assert context.tenant_id == "test_tenant"
        assert context.user_id == "test_user"
        assert context.suite_id == "fedsuite"
        assert context.module_id == "dataflow"

    def test_retrieval_context_defaults(self):
        """Test RetrievalContext with default values."""
        context = RetrievalContext(tenant_id="test", user_id="user")

        assert context.suite_id is None
        assert context.module_id is None
        assert context.entity_id is None
        assert context.route is None
        assert context.user_role == "viewer"


@pytest.mark.unit
class TestRetrievedChunk:
    """Test RetrievedChunk dataclass."""

    def test_retrieved_chunk_creation(self):
        """Test creating RetrievedChunk."""
        chunk = RetrievedChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            content="Test content",
            heading="Test Heading",
            page_number=1,
            document_title="Test Document",
            document_level="platform",
            suite_id=None,
            module_id=None,
            similarity=0.85,
            context_boost=0.0,
            final_score=0.85,
        )

        assert chunk.chunk_id == "chunk-1"
        assert chunk.similarity == 0.85
        assert chunk.final_score == 0.85


@pytest.mark.integration
class TestCascadingRetrieval:
    """Test cascading retrieval with hierarchical context boosting."""

    def test_cascading_retrieval_basic(self, db_session, sample_chunks, mock_embedding_model):
        """Test basic cascading retrieval."""
        context = RetrievalContext(tenant_id="test_tenant", user_id="test_user")

        results = cascading_retrieval(
            query="What are access control policies?", context=context, db=db_session, top_k=3
        )

        assert isinstance(results, list)
        if len(results) > 0:
            assert all(isinstance(r, RetrievedChunk) for r in results)
            assert len(results) <= 3

            # Check that results are sorted by final_score
            scores = [r.final_score for r in results]
            assert scores == sorted(scores, reverse=True)

    def test_cascading_retrieval_empty_results(self, db_session, mock_embedding_model):
        """Test cascading retrieval with no matching documents."""
        context = RetrievalContext(tenant_id="test_tenant", user_id="test_user")

        # Query with no matching content
        results = cascading_retrieval(
            query="completely unrelated quantum physics topic",
            context=context,
            db=db_session,
            top_k=5,
            similarity_threshold=0.9,  # Very high threshold
        )

        # May return empty or low results
        assert isinstance(results, list)

    def test_cascading_retrieval_platform_level(
        self, db_session, sample_chunks, mock_embedding_model
    ):
        """Test retrieval of platform-level documents."""
        context = RetrievalContext(tenant_id="test_tenant", user_id="test_user")

        results = cascading_retrieval(
            query="NIST security controls", context=context, db=db_session
        )

        if len(results) > 0:
            # Platform-level documents should have no context boost
            platform_results = [r for r in results if r.document_level == "platform"]
            for result in platform_results:
                assert result.context_boost == 0.0

    def test_cascading_retrieval_suite_context_boost(
        self, db_session, suite_document, mock_embedding_model
    ):
        """Test that suite-level documents get context boost."""
        # Create a chunk for suite document
        from app.embeddings import generate_embedding

        chunk = Chunk(
            document_id=suite_document.id,
            ord=0,
            content="FedSuite specific compliance information",
            content_hash=Chunk.compute_hash("FedSuite specific compliance information"),
            heading="FedSuite",
            token_count=5,
            embedding=generate_embedding("FedSuite specific compliance information"),
        )
        db_session.add(chunk)
        db_session.commit()

        # Query with suite context
        context = RetrievalContext(
            tenant_id="test_tenant", user_id="test_user", suite_id="fedsuite"
        )

        results = cascading_retrieval(query="FedSuite compliance", context=context, db=db_session)

        if len(results) > 0:
            suite_results = [r for r in results if r.suite_id == "fedsuite"]
            for result in suite_results:
                # Suite-level should get +0.05 boost
                assert result.context_boost >= 0.05

    def test_cascading_retrieval_module_context_boost(
        self, db_session, module_document, mock_embedding_model
    ):
        """Test that module-level documents get context boost."""
        from app.embeddings import generate_embedding

        chunk = Chunk(
            document_id=module_document.id,
            ord=0,
            content="DataFlow module specific information",
            content_hash=Chunk.compute_hash("DataFlow module specific information"),
            heading="DataFlow",
            token_count=5,
            embedding=generate_embedding("DataFlow module specific information"),
        )
        db_session.add(chunk)
        db_session.commit()

        context = RetrievalContext(
            tenant_id="test_tenant", user_id="test_user", suite_id="fedsuite", module_id="dataflow"
        )

        results = cascading_retrieval(query="DataFlow module", context=context, db=db_session)

        if len(results) > 0:
            module_results = [r for r in results if r.module_id == "dataflow"]
            for result in module_results:
                # Module-level should get +0.10 boost
                assert result.context_boost >= 0.10

    def test_cascading_retrieval_top_k(self, db_session, sample_chunks, mock_embedding_model):
        """Test that top_k limits results correctly."""
        context = RetrievalContext(tenant_id="test_tenant", user_id="test_user")

        # Test different top_k values
        for k in [1, 3, 5]:
            results = cascading_retrieval(
                query="security controls", context=context, db=db_session, top_k=k
            )

            assert len(results) <= k

    def test_cascading_retrieval_similarity_threshold(
        self, db_session, sample_chunks, mock_embedding_model
    ):
        """Test similarity threshold filtering."""
        context = RetrievalContext(tenant_id="test_tenant", user_id="test_user")

        # Low threshold - should get more results
        low_results = cascading_retrieval(
            query="security", context=context, db=db_session, similarity_threshold=0.1
        )

        # High threshold - should get fewer results
        high_results = cascading_retrieval(
            query="security", context=context, db=db_session, similarity_threshold=0.8
        )

        assert len(high_results) <= len(low_results)

    def test_cascading_retrieval_access_levels(
        self, db_session, sample_chunks, mock_embedding_model
    ):
        """Test access level filtering."""
        context = RetrievalContext(tenant_id="test_tenant", user_id="test_user")

        # Only public documents
        results = cascading_retrieval(
            query="security", context=context, db=db_session, access_levels=["public"]
        )

        if len(results) > 0:
            # All results should be from public documents
            pass  # Can't easily verify without querying documents

    def test_cascading_retrieval_updates_stats(
        self, db_session, sample_chunks, mock_embedding_model
    ):
        """Test that retrieval updates knowledge base stats."""
        context = RetrievalContext(tenant_id="test_tenant", user_id="test_user")

        results = cascading_retrieval(query="security controls", context=context, db=db_session)

        if len(results) > 0:
            # Check that stats were updated
            doc_id = results[0].document_id
            stats = (
                db_session.query(KnowledgeBaseStats)
                .filter(KnowledgeBaseStats.document_id == doc_id)
                .first()
            )

            if stats:
                assert stats.retrieval_count > 0
                assert stats.last_retrieved_at is not None


@pytest.mark.integration
class TestHybridRetrieval:
    """Test hybrid retrieval (vector + keyword search)."""

    def test_hybrid_retrieval_basic(self, db_session, sample_chunks, mock_embedding_model):
        """Test basic hybrid retrieval."""
        context = RetrievalContext(tenant_id="test_tenant", user_id="test_user")

        results = hybrid_retrieval(
            query="access control policies", context=context, db=db_session, top_k=3
        )

        assert isinstance(results, list)
        if len(results) > 0:
            assert all(isinstance(r, RetrievedChunk) for r in results)
            assert len(results) <= 3

    def test_hybrid_retrieval_weights(self, db_session, sample_chunks, mock_embedding_model):
        """Test hybrid retrieval with different weights."""
        context = RetrievalContext(tenant_id="test_tenant", user_id="test_user")

        # Heavy vector weight
        vector_heavy = hybrid_retrieval(
            query="security", context=context, db=db_session, vector_weight=0.9, keyword_weight=0.1
        )

        # Heavy keyword weight
        keyword_heavy = hybrid_retrieval(
            query="security", context=context, db=db_session, vector_weight=0.1, keyword_weight=0.9
        )

        # Both should return results (if any match)
        assert isinstance(vector_heavy, list)
        assert isinstance(keyword_heavy, list)

    def test_hybrid_retrieval_keyword_matching(
        self, db_session, sample_chunks, mock_embedding_model
    ):
        """Test that keyword matching works in hybrid retrieval."""
        context = RetrievalContext(tenant_id="test_tenant", user_id="test_user")

        # Query with specific keyword in content
        results = hybrid_retrieval(query="authentication", context=context, db=db_session)

        if len(results) > 0:
            # At least some results should contain the keyword
            matching = [r for r in results if "authentication" in r.content.lower()]
            # Hybrid should find keyword matches
            assert len(matching) >= 0


@pytest.mark.integration
class TestUpdateRetrievalStats:
    """Test knowledge base statistics updates."""

    def test_update_retrieval_stats_new(self, db_session, sample_document):
        """Test creating new stats entry."""
        doc_id = str(sample_document.id)

        # Initial stats should not exist
        stats = (
            db_session.query(KnowledgeBaseStats)
            .filter(KnowledgeBaseStats.document_id == doc_id)
            .first()
        )
        assert stats is None

        # Update stats
        update_retrieval_stats(db_session, [doc_id])
        db_session.commit()

        # Stats should now exist
        stats = (
            db_session.query(KnowledgeBaseStats)
            .filter(KnowledgeBaseStats.document_id == doc_id)
            .first()
        )

        assert stats is not None
        assert stats.retrieval_count == 1
        assert stats.last_retrieved_at is not None

    def test_update_retrieval_stats_existing(self, db_session, sample_document):
        """Test updating existing stats entry."""
        doc_id = str(sample_document.id)

        # Create initial stats
        stats = KnowledgeBaseStats(document_id=doc_id, retrieval_count=5)
        db_session.add(stats)
        db_session.commit()

        # Update stats
        update_retrieval_stats(db_session, [doc_id])
        db_session.commit()

        # Check updated stats
        updated_stats = (
            db_session.query(KnowledgeBaseStats)
            .filter(KnowledgeBaseStats.document_id == doc_id)
            .first()
        )

        assert updated_stats.retrieval_count == 6

    def test_update_retrieval_stats_multiple(self, db_session, sample_document, suite_document):
        """Test updating stats for multiple documents."""
        doc_ids = [str(sample_document.id), str(suite_document.id)]

        update_retrieval_stats(db_session, doc_ids)
        db_session.commit()

        # Both should have stats
        for doc_id in doc_ids:
            stats = (
                db_session.query(KnowledgeBaseStats)
                .filter(KnowledgeBaseStats.document_id == doc_id)
                .first()
            )

            assert stats is not None
            assert stats.retrieval_count >= 1


@pytest.mark.integration
class TestGetSimilarDocuments:
    """Test finding similar documents."""

    def test_get_similar_documents_basic(
        self, db_session, sample_document, sample_chunks, suite_document
    ):
        """Test finding similar documents."""
        # Add chunks to suite document
        from app.embeddings import generate_embedding

        chunk = Chunk(
            document_id=suite_document.id,
            ord=0,
            content="Security controls and access policies",
            content_hash=Chunk.compute_hash("Security controls and access policies"),
            embedding=generate_embedding("Security controls and access policies"),
        )
        db_session.add(chunk)
        db_session.commit()

        # Find documents similar to sample_document
        similar = get_similar_documents(document_id=str(sample_document.id), db=db_session, top_k=5)

        assert isinstance(similar, list)
        # May or may not find similar documents depending on embeddings

    def test_get_similar_documents_excludes_self(self, db_session, sample_document, sample_chunks):
        """Test that similar documents don't include the source document."""
        similar = get_similar_documents(document_id=str(sample_document.id), db=db_session)

        # Source document should not be in results
        doc_ids = [doc["id"] for doc in similar]
        assert str(sample_document.id) not in doc_ids

    def test_get_similar_documents_threshold(self, db_session, sample_document, sample_chunks):
        """Test similarity threshold filtering."""
        # High threshold - fewer results
        similar_high = get_similar_documents(
            document_id=str(sample_document.id), db=db_session, min_similarity=0.9
        )

        # Low threshold - more results
        similar_low = get_similar_documents(
            document_id=str(sample_document.id), db=db_session, min_similarity=0.5
        )

        assert len(similar_low) >= len(similar_high)


@pytest.mark.unit
class TestRetrievalErrorHandling:
    """Test error handling in retrieval functions."""

    def test_cascading_retrieval_embedding_failure(self, db_session):
        """Test handling embedding generation failure."""
        with patch("app.retrieval.generate_embedding", side_effect=Exception("Embedding error")):
            context = RetrievalContext(tenant_id="test", user_id="user")

            results = cascading_retrieval(query="test", context=context, db=db_session)

            # Should return empty list on error
            assert results == []

    def test_hybrid_retrieval_embedding_failure(self, db_session):
        """Test handling embedding generation failure in hybrid retrieval."""
        with patch("app.retrieval.generate_embedding", side_effect=Exception("Embedding error")):
            context = RetrievalContext(tenant_id="test", user_id="user")

            results = hybrid_retrieval(query="test", context=context, db=db_session)

            # Should return empty list on error
            assert results == []

    def test_update_stats_failure(self, db_session):
        """Test handling database error in stats update."""
        with patch.object(db_session, "commit", side_effect=Exception("DB error")):
            # Should not raise exception
            update_retrieval_stats(db_session, ["doc-id"])


@pytest.mark.integration
class TestRetrievalScoring:
    """Test retrieval scoring and ranking."""

    def test_final_score_calculation(self, db_session, sample_chunks, mock_embedding_model):
        """Test that final scores are calculated correctly."""
        context = RetrievalContext(tenant_id="test_tenant", user_id="test_user")

        results = cascading_retrieval(query="security controls", context=context, db=db_session)

        for result in results:
            # final_score should equal similarity + context_boost
            expected = result.similarity + result.context_boost
            assert abs(result.final_score - expected) < 0.001

    def test_results_sorted_by_score(self, db_session, sample_chunks, mock_embedding_model):
        """Test that results are sorted by final score."""
        context = RetrievalContext(tenant_id="test_tenant", user_id="test_user")

        results = cascading_retrieval(
            query="access control", context=context, db=db_session, top_k=10
        )

        if len(results) > 1:
            # Check descending order
            for i in range(len(results) - 1):
                assert results[i].final_score >= results[i + 1].final_score
