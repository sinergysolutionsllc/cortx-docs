"""
Test data factories for RAG service.

Provides factory functions for creating test data:
- Documents
- Chunks
- Embeddings
- Conversations
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from app.models import Chunk, Conversation, Document, KnowledgeBaseStats, Message, QueryCache
from faker import Faker

fake = Faker()


class DocumentFactory:
    """Factory for creating test documents."""

    @staticmethod
    def create(
        tenant_id: str = "test_tenant",
        level: str = "platform",
        suite_id: Optional[str] = None,
        module_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        source_type: str = "markdown",
        access_level: str = "public",
        status: str = "active",
        **kwargs,
    ) -> Document:
        """Create a document instance."""
        return Document(
            tenant_id=tenant_id,
            level=level,
            suite_id=suite_id,
            module_id=module_id,
            title=title or fake.sentence(),
            description=description or fake.paragraph(),
            source_type=source_type,
            access_level=access_level,
            status=status,
            doc_metadata=kwargs.get(
                "doc_metadata", {"uploaded_by": "test_user", "tags": ["test", "compliance"]}
            ),
        )

    @staticmethod
    def create_platform(tenant_id: str = "test_tenant", **kwargs) -> Document:
        """Create a platform-level document."""
        return DocumentFactory.create(
            tenant_id=tenant_id,
            level="platform",
            suite_id=None,
            module_id=None,
            title=kwargs.pop("title", "Platform Security Controls"),
            **kwargs,
        )

    @staticmethod
    def create_suite(
        tenant_id: str = "test_tenant", suite_id: str = "fedsuite", **kwargs
    ) -> Document:
        """Create a suite-level document."""
        return DocumentFactory.create(
            tenant_id=tenant_id,
            level="suite",
            suite_id=suite_id,
            module_id=None,
            title=kwargs.pop("title", f"{suite_id.title()} Compliance Guide"),
            **kwargs,
        )

    @staticmethod
    def create_module(
        tenant_id: str = "test_tenant",
        suite_id: str = "fedsuite",
        module_id: str = "dataflow",
        **kwargs,
    ) -> Document:
        """Create a module-level document."""
        return DocumentFactory.create(
            tenant_id=tenant_id,
            level="module",
            suite_id=suite_id,
            module_id=module_id,
            title=kwargs.pop("title", f"{module_id.title()} Module Documentation"),
            **kwargs,
        )

    @staticmethod
    def create_entity(
        tenant_id: str = "test_tenant",
        suite_id: str = "fedsuite",
        module_id: str = "dataflow",
        **kwargs,
    ) -> Document:
        """Create an entity-level document."""
        return DocumentFactory.create(
            tenant_id=tenant_id,
            level="entity",
            suite_id=suite_id,
            module_id=module_id,
            title=kwargs.pop("title", "Entity-Specific Policy"),
            **kwargs,
        )


class ChunkFactory:
    """Factory for creating test chunks."""

    @staticmethod
    def create(
        document_id: uuid.UUID,
        ord: int = 0,
        content: Optional[str] = None,
        heading: Optional[str] = None,
        token_count: Optional[int] = None,
        embedding: Optional[List[float]] = None,
        **kwargs,
    ) -> Chunk:
        """Create a chunk instance."""
        content_text = content or fake.paragraph(nb_sentences=5)

        return Chunk(
            document_id=document_id,
            ord=ord,
            content=content_text,
            content_hash=Chunk.compute_hash(content_text),
            heading=heading or fake.sentence(nb_words=3),
            token_count=token_count or len(content_text.split()),
            embedding=embedding or _generate_fake_embedding(),
            chunk_metadata=kwargs.get("chunk_metadata", {}),
        )

    @staticmethod
    def create_batch(document_id: uuid.UUID, count: int = 5, **kwargs) -> List[Chunk]:
        """Create multiple chunks for a document."""
        return [ChunkFactory.create(document_id=document_id, ord=i, **kwargs) for i in range(count)]


class ConversationFactory:
    """Factory for creating test conversations."""

    @staticmethod
    def create(
        user_id: str = "test_user",
        tenant_id: str = "test_tenant",
        suite_id: Optional[str] = None,
        module_id: Optional[str] = None,
        title: Optional[str] = None,
        **kwargs,
    ) -> Conversation:
        """Create a conversation instance."""
        return Conversation(
            user_id=user_id,
            tenant_id=tenant_id,
            suite_id=suite_id,
            module_id=module_id,
            title=title or fake.sentence(),
            message_count=kwargs.get("message_count", 0),
            feedback_score=kwargs.get("feedback_score"),
            feedback_comment=kwargs.get("feedback_comment"),
        )


class MessageFactory:
    """Factory for creating test messages."""

    @staticmethod
    def create(
        conversation_id: uuid.UUID, role: str = "user", content: Optional[str] = None, **kwargs
    ) -> Message:
        """Create a message instance."""
        return Message(
            conversation_id=conversation_id,
            role=role,
            content=content or fake.paragraph(),
            model=kwargs.get("model"),
            tokens_used=kwargs.get("tokens_used"),
            chunks_retrieved=kwargs.get("chunks_retrieved"),
            document_ids=kwargs.get("document_ids"),
            chunk_ids=kwargs.get("chunk_ids"),
            query_embedding=kwargs.get("query_embedding"),
        )

    @staticmethod
    def create_user_message(
        conversation_id: uuid.UUID, content: Optional[str] = None, **kwargs
    ) -> Message:
        """Create a user message."""
        return MessageFactory.create(
            conversation_id=conversation_id,
            role="user",
            content=content or fake.sentence() + "?",
            **kwargs,
        )

    @staticmethod
    def create_assistant_message(
        conversation_id: uuid.UUID, content: Optional[str] = None, **kwargs
    ) -> Message:
        """Create an assistant message."""
        return MessageFactory.create(
            conversation_id=conversation_id,
            role="assistant",
            content=content or fake.paragraph(),
            model="gemini-1.5-flash",
            tokens_used=kwargs.get("tokens_used", 150),
            chunks_retrieved=kwargs.get("chunks_retrieved", 3),
            **kwargs,
        )


class QueryCacheFactory:
    """Factory for creating test query cache entries."""

    @staticmethod
    def create(
        query_text: Optional[str] = None,
        tenant_id: str = "test_tenant",
        suite_id: Optional[str] = None,
        module_id: Optional[str] = None,
        response_text: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        expires_at: Optional[datetime] = None,
        **kwargs,
    ) -> QueryCache:
        """Create a query cache instance."""
        query = query_text or fake.sentence() + "?"

        return QueryCache(
            query_text=query,
            query_hash=QueryCache.compute_query_hash(query),
            query_embedding=embedding or _generate_fake_embedding(),
            suite_id=suite_id,
            module_id=module_id,
            tenant_id=tenant_id,
            response_text=response_text or fake.paragraph(),
            document_ids=kwargs.get("document_ids", []),
            chunk_ids=kwargs.get("chunk_ids", []),
            model=kwargs.get("model", "gemini-1.5-flash"),
            hit_count=kwargs.get("hit_count", 0),
            expires_at=expires_at or (datetime.utcnow() + timedelta(hours=1)),
        )


class KnowledgeBaseStatsFactory:
    """Factory for creating test KB stats entries."""

    @staticmethod
    def create(document_id: uuid.UUID, **kwargs) -> KnowledgeBaseStats:
        """Create a KB stats instance."""
        return KnowledgeBaseStats(
            document_id=document_id,
            retrieval_count=kwargs.get("retrieval_count", 0),
            citation_count=kwargs.get("citation_count", 0),
            view_count=kwargs.get("view_count", 0),
            avg_feedback_score=kwargs.get("avg_feedback_score"),
            positive_feedback_count=kwargs.get("positive_feedback_count", 0),
            negative_feedback_count=kwargs.get("negative_feedback_count", 0),
            last_retrieved_at=kwargs.get("last_retrieved_at"),
            last_cited_at=kwargs.get("last_cited_at"),
            last_viewed_at=kwargs.get("last_viewed_at"),
        )


def _generate_fake_embedding(dim: int = 384) -> List[float]:
    """Generate a fake normalized embedding vector."""
    import numpy as np

    # Generate random vector
    vec = np.random.randn(dim)

    # Normalize to unit length
    vec = vec / np.linalg.norm(vec)

    return vec.tolist()


# Convenience exports
__all__ = [
    "DocumentFactory",
    "ChunkFactory",
    "ConversationFactory",
    "MessageFactory",
    "QueryCacheFactory",
    "KnowledgeBaseStatsFactory",
]
