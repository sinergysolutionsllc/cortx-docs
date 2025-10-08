"""
Hierarchical RAG retrieval service.

Implements cascading retrieval strategy with context-aware boosting:
- Entity-level (tenant-specific): +0.15 boost
- Module-level (current module): +0.10 boost
- Suite-level (current suite): +0.05 boost
- Platform-level (universal): 0.0 boost
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.embeddings import generate_embedding
from app.models import KnowledgeBaseStats
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class RetrievalContext:
    """Context for retrieval queries."""

    tenant_id: str
    user_id: str
    suite_id: Optional[str] = None
    module_id: Optional[str] = None
    entity_id: Optional[str] = None
    route: Optional[str] = None
    user_role: Optional[str] = "viewer"


@dataclass
class RetrievedChunk:
    """Retrieved chunk with metadata and score."""

    chunk_id: str
    document_id: str
    content: str
    heading: Optional[str]
    page_number: Optional[int]

    # Document metadata
    document_title: str
    document_level: str
    suite_id: Optional[str]
    module_id: Optional[str]

    # Scoring
    similarity: float
    context_boost: float
    final_score: float


def cascading_retrieval(
    query: str,
    context: RetrievalContext,
    db: Session,
    top_k: int = 5,
    similarity_threshold: float = 0.5,
    access_levels: List[str] = None,
) -> List[RetrievedChunk]:
    """
    Retrieve relevant chunks with cascading context priority.

    Priority order:
    1. Entity-level (tenant-specific): +0.15 boost
    2. Module-level (current module): +0.10 boost
    3. Suite-level (current suite): +0.05 boost
    4. Platform-level (universal): 0.0 boost

    Args:
        query: User's question
        context: Retrieval context (suite, module, tenant, etc.)
        db: Database session
        top_k: Number of chunks to retrieve
        similarity_threshold: Minimum similarity score (0-1)
        access_levels: Allowed access levels (default: ['public', 'internal'])

    Returns:
        List of RetrievedChunk objects sorted by final_score
    """
    # Default access levels
    if access_levels is None:
        access_levels = ["public", "internal"]

    # Generate query embedding
    try:
        query_embedding = generate_embedding(query)
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        return []

    # Build SQL query with cascading context boost
    sql = text(
        """
        SELECT
            c.id::text AS chunk_id,
            c.document_id::text,
            c.content,
            c.heading,
            c.page_number,
            d.title AS document_title,
            d.level AS document_level,
            d.suite_id,
            d.module_id,
            -- Similarity score (cosine distance -> similarity)
            1 - (c.embedding <=> CAST(:query_embedding AS vector)) AS similarity,
            -- Context boost based on hierarchy level
            CASE
                WHEN d.level = 'entity' AND d.tenant_id = :tenant_id THEN 0.15
                WHEN d.level = 'module' AND d.module_id = :module_id THEN 0.10
                WHEN d.level = 'suite' AND d.suite_id = :suite_id THEN 0.05
                ELSE 0.0
            END AS context_boost,
            -- Combined final score
            (1 - (c.embedding <=> CAST(:query_embedding AS vector))) +
            CASE
                WHEN d.level = 'entity' AND d.tenant_id = :tenant_id THEN 0.15
                WHEN d.level = 'module' AND d.module_id = :module_id THEN 0.10
                WHEN d.level = 'suite' AND d.suite_id = :suite_id THEN 0.05
                ELSE 0.0
            END AS final_score
        FROM rag.chunks c
        JOIN rag.documents d ON c.document_id = d.id
        WHERE d.status = 'active'
          AND d.access_level = ANY(:access_levels)
          AND (1 - (c.embedding <=> CAST(:query_embedding AS vector))) >= :similarity_threshold
        ORDER BY final_score DESC
        LIMIT :top_k
    """
    )

    try:
        result = db.execute(
            sql,
            {
                "query_embedding": query_embedding,
                "tenant_id": context.tenant_id,
                "module_id": context.module_id or "",
                "suite_id": context.suite_id or "",
                "access_levels": access_levels,
                "similarity_threshold": similarity_threshold,
                "top_k": top_k,
            },
        )

        rows = result.fetchall()

        chunks = [
            RetrievedChunk(
                chunk_id=row.chunk_id,
                document_id=row.document_id,
                content=row.content,
                heading=row.heading,
                page_number=row.page_number,
                document_title=row.document_title,
                document_level=row.document_level,
                suite_id=row.suite_id,
                module_id=row.module_id,
                similarity=float(row.similarity),
                context_boost=float(row.context_boost),
                final_score=float(row.final_score),
            )
            for row in rows
        ]

        # Update knowledge base stats
        if chunks:
            document_ids = list(set(c.document_id for c in chunks))
            update_retrieval_stats(db, document_ids)

        logger.info(
            f"Retrieved {len(chunks)} chunks for query (avg score: {sum(c.final_score for c in chunks)/len(chunks):.3f})"
        )

        return chunks

    except Exception as e:
        logger.error(f"Cascading retrieval failed: {e}")
        return []


def hybrid_retrieval(
    query: str,
    context: RetrievalContext,
    db: Session,
    top_k: int = 5,
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3,
    access_levels: List[str] = None,
) -> List[RetrievedChunk]:
    """
    Hybrid retrieval combining vector similarity and keyword search.

    Combines:
    1. Vector similarity (semantic search)
    2. Full-text keyword search (PostgreSQL FTS)

    Args:
        query: User's question
        context: Retrieval context
        db: Database session
        top_k: Number of chunks to retrieve
        vector_weight: Weight for vector similarity (default: 0.7)
        keyword_weight: Weight for keyword search (default: 0.3)
        access_levels: Allowed access levels

    Returns:
        List of RetrievedChunk objects sorted by hybrid score
    """
    # Default access levels
    if access_levels is None:
        access_levels = ["public", "internal"]

    # Generate query embedding
    try:
        query_embedding = generate_embedding(query)
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        return []

    # Prepare query for full-text search
    fts_query = " & ".join(query.split())

    # Hybrid SQL query
    sql = text(
        """
        SELECT
            c.id::text AS chunk_id,
            c.document_id::text,
            c.content,
            c.heading,
            c.page_number,
            d.title AS document_title,
            d.level AS document_level,
            d.suite_id,
            d.module_id,
            -- Vector similarity
            1 - (c.embedding <=> CAST(:query_embedding AS vector)) AS similarity,
            -- Keyword relevance (0-1 normalized)
            ts_rank(to_tsvector('english', c.content), to_tsquery('english', :fts_query)) AS keyword_score,
            -- Context boost
            CASE
                WHEN d.level = 'entity' AND d.tenant_id = :tenant_id THEN 0.15
                WHEN d.level = 'module' AND d.module_id = :module_id THEN 0.10
                WHEN d.level = 'suite' AND d.suite_id = :suite_id THEN 0.05
                ELSE 0.0
            END AS context_boost,
            -- Hybrid score
            (
                :vector_weight * (1 - (c.embedding <=> CAST(:query_embedding AS vector))) +
                :keyword_weight * ts_rank(to_tsvector('english', c.content), to_tsquery('english', :fts_query))
            ) +
            CASE
                WHEN d.level = 'entity' AND d.tenant_id = :tenant_id THEN 0.15
                WHEN d.level = 'module' AND d.module_id = :module_id THEN 0.10
                WHEN d.level = 'suite' AND d.suite_id = :suite_id THEN 0.05
                ELSE 0.0
            END AS final_score
        FROM rag.chunks c
        JOIN rag.documents d ON c.document_id = d.id
        WHERE d.status = 'active'
          AND d.access_level = ANY(:access_levels)
          AND (
            to_tsvector('english', c.content) @@ to_tsquery('english', :fts_query)
            OR (1 - (c.embedding <=> CAST(:query_embedding AS vector))) >= 0.5
          )
        ORDER BY final_score DESC
        LIMIT :top_k
    """
    )

    try:
        result = db.execute(
            sql,
            {
                "query_embedding": query_embedding,
                "fts_query": fts_query,
                "tenant_id": context.tenant_id,
                "module_id": context.module_id or "",
                "suite_id": context.suite_id or "",
                "access_levels": access_levels,
                "vector_weight": vector_weight,
                "keyword_weight": keyword_weight,
                "top_k": top_k,
            },
        )

        rows = result.fetchall()

        chunks = [
            RetrievedChunk(
                chunk_id=row.chunk_id,
                document_id=row.document_id,
                content=row.content,
                heading=row.heading,
                page_number=row.page_number,
                document_title=row.document_title,
                document_level=row.document_level,
                suite_id=row.suite_id,
                module_id=row.module_id,
                similarity=float(row.similarity),
                context_boost=float(row.context_boost),
                final_score=float(row.final_score),
            )
            for row in rows
        ]

        # Update stats
        if chunks:
            document_ids = list(set(c.document_id for c in chunks))
            update_retrieval_stats(db, document_ids)

        logger.info(
            f"Hybrid retrieval: {len(chunks)} chunks (avg score: {sum(c.final_score for c in chunks)/len(chunks):.3f})"
        )

        return chunks

    except Exception as e:
        logger.error(f"Hybrid retrieval failed: {e}")
        return []


def update_retrieval_stats(db: Session, document_ids: List[str]) -> None:
    """
    Update knowledge base statistics after retrieval.

    Increments retrieval_count and updates last_retrieved_at.
    """
    try:
        from datetime import datetime

        for doc_id in document_ids:
            # Check if stats exist
            stats = (
                db.query(KnowledgeBaseStats)
                .filter(KnowledgeBaseStats.document_id == doc_id)
                .first()
            )

            if stats:
                stats.retrieval_count += 1
                stats.last_retrieved_at = datetime.utcnow()
            else:
                # Create new stats entry
                stats = KnowledgeBaseStats(
                    document_id=doc_id, retrieval_count=1, last_retrieved_at=datetime.utcnow()
                )
                db.add(stats)

        db.commit()

    except Exception as e:
        logger.error(f"Failed to update retrieval stats: {e}")
        db.rollback()


def get_similar_documents(
    document_id: str, db: Session, top_k: int = 5, min_similarity: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Find documents similar to a given document.

    Uses average chunk embedding to represent document.
    """
    sql = text(
        """
        WITH target_doc_embedding AS (
            SELECT AVG(embedding) AS avg_embedding
            FROM rag.chunks
            WHERE document_id = :document_id
        )
        SELECT
            d.id::text,
            d.title,
            d.level,
            d.suite_id,
            d.module_id,
            1 - (AVG(c.embedding) <=> (SELECT avg_embedding FROM target_doc_embedding)) AS similarity
        FROM rag.documents d
        JOIN rag.chunks c ON c.document_id = d.id
        WHERE d.id != :document_id
          AND d.status = 'active'
        GROUP BY d.id, d.title, d.level, d.suite_id, d.module_id
        HAVING 1 - (AVG(c.embedding) <=> (SELECT avg_embedding FROM target_doc_embedding)) >= :min_similarity
        ORDER BY similarity DESC
        LIMIT :top_k
    """
    )

    try:
        result = db.execute(
            sql, {"document_id": document_id, "min_similarity": min_similarity, "top_k": top_k}
        )

        return [
            {
                "id": row.id,
                "title": row.title,
                "level": row.level,
                "suite_id": row.suite_id,
                "module_id": row.module_id,
                "similarity": float(row.similarity),
            }
            for row in result.fetchall()
        ]

    except Exception as e:
        logger.error(f"Failed to find similar documents: {e}")
        return []
