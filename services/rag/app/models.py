"""
Database models for RAG service.

Implements 4-level hierarchical knowledge base:
- Platform: Universal knowledge (NIST, FedRAMP, HIPAA, etc.)
- Suite: Domain-specific (FedSuite, CorpSuite, MedSuite)
- Module: Module-specific (DataFlow, PropVerify, FedReconcile)
- Entity: Tenant-specific (agency policies, custom mappings)
"""

import hashlib
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Document(Base):
    """
    Documents in the RAG knowledge base.

    Supports 4-level hierarchy: platform, suite, module, entity.
    Each document can have multiple chunks with embeddings.
    """

    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("level IN ('platform', 'suite', 'module', 'entity')", name="valid_level"),
        CheckConstraint("status IN ('active', 'archived', 'deleted')", name="valid_status"),
        CheckConstraint(
            "access_level IN ('public', 'internal', 'confidential', 'restricted')",
            name="valid_access_level",
        ),
        Index("idx_documents_tenant", "tenant_id"),
        Index("idx_documents_level", "level"),
        Index("idx_documents_suite", "suite_id"),
        Index("idx_documents_module", "module_id"),
        Index("idx_documents_status", "status"),
        Index("idx_documents_created", "created_at"),
        {"schema": "rag"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Hierarchical organization
    level = Column(String(50), nullable=False)  # platform, suite, module, entity
    suite_id = Column(String(255), nullable=True)  # e.g., 'fedsuite', 'corpsuite', 'medsuite'
    module_id = Column(String(255), nullable=True)  # e.g., 'dataflow', 'propverify'

    # Document metadata
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(String(100), nullable=False)  # pdf, markdown, url, api_spec, policy
    file_path = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    content_type = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)

    # Access control
    access_level = Column(String(50), default="internal")
    status = Column(String(50), default="active")

    # Additional metadata as JSONB
    doc_metadata = Column("metadata", JSONB, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_accessed = Column(DateTime, nullable=True)

    # Relationships
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}', level='{self.level}')>"


class Chunk(Base):
    """
    Text chunks from documents with vector embeddings.

    Each chunk represents a semantic unit (paragraph, section) with:
    - Embedding vector for similarity search
    - Full-text search via PostgreSQL FTS
    - Context metadata (heading, page number)
    """

    __tablename__ = "chunks"
    __table_args__ = (
        Index("idx_chunks_document", "document_id"),
        Index(
            "idx_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index(
            "idx_chunks_content_fts",
            "content",
            postgresql_using="gin",
            postgresql_ops={"content": "gin_trgm_ops"},
        ),
        Index("idx_chunks_hash", "content_hash"),
        {"schema": "rag"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("rag.documents.id", ondelete="CASCADE"), nullable=False
    )

    # Chunk order and content
    ord = Column(Integer, nullable=False)  # Order within document
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)  # SHA256 for deduplication

    # Context metadata
    heading = Column(Text, nullable=True)  # Nearest heading/section title
    page_number = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)

    # Vector embedding (384 dimensions for all-MiniLM-L6-v2)
    embedding = Column(Vector(384), nullable=False)

    # Additional metadata
    chunk_metadata = Column("metadata", JSONB, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<Chunk(id={self.id}, document_id={self.document_id}, ord={self.ord})>"

    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute SHA256 hash of content for deduplication."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


class Conversation(Base):
    """
    User conversation history for learning and context.

    Tracks multi-turn conversations with ThinkTank for:
    - Understanding common user questions
    - Identifying knowledge gaps
    - Personalizing responses per user
    - Training fine-tuned models (future)
    """

    __tablename__ = "conversations"
    __table_args__ = (
        Index("idx_conversations_user", "user_id"),
        Index("idx_conversations_tenant", "tenant_id"),
        Index("idx_conversations_started", "started_at"),
        {"schema": "rag"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)

    # Context at conversation start
    suite_id = Column(String(255), nullable=True)
    module_id = Column(String(255), nullable=True)
    route = Column(String(500), nullable=True)  # URL path where conversation started

    # Conversation metadata
    title = Column(Text, nullable=True)  # Auto-generated from first message
    message_count = Column(Integer, default=0)

    # User feedback
    feedback_score = Column(Integer, nullable=True)  # 1-5 rating
    feedback_comment = Column(Text, nullable=True)

    # Additional context
    extra_metadata = Column("metadata", JSONB, default={})

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    last_message_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<Conversation(id={self.id}, user_id='{self.user_id}', messages={self.message_count})>"
        )


class Message(Base):
    """
    Individual messages within a conversation.

    Tracks user queries and assistant responses with:
    - Full message content
    - Sources used (document chunks)
    - Model and token usage
    - User feedback on response quality
    """

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="valid_role"),
        Index("idx_messages_conversation", "conversation_id"),
        Index("idx_messages_created", "created_at"),
        {"schema": "rag"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True), ForeignKey("rag.conversations.id", ondelete="CASCADE"), nullable=False
    )

    # Message content
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # Query metadata (for user messages)
    query_embedding = Column(Vector(384), nullable=True)

    # Response metadata (for assistant messages)
    model = Column(String(100), nullable=True)  # e.g., 'gemini-1.5-flash'
    tokens_used = Column(Integer, nullable=True)
    chunks_retrieved = Column(Integer, nullable=True)
    document_ids = Column(JSONB, nullable=True)  # List of document IDs used
    chunk_ids = Column(JSONB, nullable=True)  # List of chunk IDs used

    # User feedback on this specific message
    feedback_score = Column(Integer, nullable=True)  # 1-5 rating
    feedback_type = Column(String(100), nullable=True)  # helpful, incorrect, missing_context, other
    feedback_comment = Column(Text, nullable=True)

    # Additional metadata
    chunk_metadata = Column("metadata", JSONB, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return (
            f"<Message(id={self.id}, role='{self.role}', conversation_id={self.conversation_id})>"
        )


class KnowledgeBaseStats(Base):
    """
    Statistics and metrics for knowledge base health.

    Tracks per-document metrics:
    - Retrieval frequency
    - Citation rate
    - User feedback
    - Last access timestamp

    Used for identifying outdated documents and knowledge gaps.
    """

    __tablename__ = "kb_stats"
    __table_args__ = (
        Index("idx_kb_stats_document", "document_id", unique=True),
        Index("idx_kb_stats_updated", "updated_at"),
        {"schema": "rag"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rag.documents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Usage metrics
    retrieval_count = Column(Integer, default=0)  # How often chunks are retrieved
    citation_count = Column(Integer, default=0)  # How often used in responses
    view_count = Column(Integer, default=0)  # Direct document views

    # Quality metrics
    avg_feedback_score = Column(Float, nullable=True)  # Average user feedback
    positive_feedback_count = Column(Integer, default=0)
    negative_feedback_count = Column(Integer, default=0)

    # Recency
    last_retrieved_at = Column(DateTime, nullable=True)
    last_cited_at = Column(DateTime, nullable=True)
    last_viewed_at = Column(DateTime, nullable=True)

    # Additional metrics
    extra_metadata = Column("metadata", JSONB, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<KnowledgeBaseStats(document_id={self.document_id}, retrievals={self.retrieval_count})>"


class QueryCache(Base):
    """
    Semantic cache for frequent queries.

    Caches responses for similar queries to improve performance and reduce costs.
    Uses embedding similarity to match queries.
    """

    __tablename__ = "query_cache"
    __table_args__ = (
        Index(
            "idx_query_cache_embedding",
            "query_embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"query_embedding": "vector_cosine_ops"},
        ),
        Index("idx_query_cache_accessed", "last_accessed_at"),
        {"schema": "rag"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Query
    query_text = Column(Text, nullable=False)
    query_hash = Column(String(64), nullable=False, index=True)  # SHA256 of normalized query
    query_embedding = Column(Vector(384), nullable=False)

    # Context
    suite_id = Column(String(255), nullable=True)
    module_id = Column(String(255), nullable=True)
    tenant_id = Column(String(255), nullable=False)

    # Cached response
    response_text = Column(Text, nullable=False)
    document_ids = Column(JSONB, nullable=True)
    chunk_ids = Column(JSONB, nullable=True)
    model = Column(String(100), nullable=True)

    # Cache statistics
    hit_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # TTL for cache expiration

    def __repr__(self):
        return f"<QueryCache(id={self.id}, hits={self.hit_count})>"

    @staticmethod
    def compute_query_hash(query: str) -> str:
        """Compute hash of normalized query."""
        normalized = query.lower().strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
