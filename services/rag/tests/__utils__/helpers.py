"""
Test helper utilities for RAG service.

Provides helper functions for:
- Creating test embeddings
- Generating test documents
- Mock setup
- Assertions
"""

from typing import Any, Dict, List

import numpy as np
from app.models import Chunk, Document
from sqlalchemy.orm import Session


def create_test_embedding(text: str, dim: int = 384) -> List[float]:
    """
    Create a deterministic test embedding for given text.

    Uses hash of text to generate reproducible embeddings for testing.
    """
    # Use text hash to seed random generator
    seed = hash(text) % (2**32)
    np.random.seed(seed)

    # Generate random vector
    vec = np.random.randn(dim)

    # Normalize to unit length
    vec = vec / np.linalg.norm(vec)

    return vec.tolist()


def create_test_document_with_chunks(
    db: Session,
    title: str,
    chunks_content: List[str],
    level: str = "platform",
    tenant_id: str = "test_tenant",
    **kwargs,
) -> Document:
    """
    Create a test document with chunks in one call.

    Args:
        db: Database session
        title: Document title
        chunks_content: List of chunk content strings
        level: Document hierarchy level
        tenant_id: Tenant ID
        **kwargs: Additional document fields

    Returns:
        Created Document instance with chunks
    """
    from tests.__utils__.factories import ChunkFactory, DocumentFactory

    # Create document
    doc = DocumentFactory.create(tenant_id=tenant_id, level=level, title=title, **kwargs)
    db.add(doc)
    db.flush()

    # Create chunks
    for i, content in enumerate(chunks_content):
        chunk = ChunkFactory.create(
            document_id=doc.id, ord=i, content=content, embedding=create_test_embedding(content)
        )
        db.add(chunk)

    db.commit()
    db.refresh(doc)

    return doc


def assert_similar_embeddings(emb1: List[float], emb2: List[float], threshold: float = 0.9):
    """
    Assert that two embeddings are similar.

    Args:
        emb1: First embedding
        emb2: Second embedding
        threshold: Minimum cosine similarity (default: 0.9)
    """
    from app.embeddings import cosine_similarity

    similarity = cosine_similarity(emb1, emb2)
    assert similarity >= threshold, f"Embeddings not similar enough: {similarity} < {threshold}"


def assert_chunks_sorted_by_score(chunks: List[Dict[str, Any]]):
    """
    Assert that chunks are sorted by final_score in descending order.

    Args:
        chunks: List of chunk dictionaries with 'final_score' field
    """
    scores = [chunk.get("final_score", 0) for chunk in chunks]

    for i in range(len(scores) - 1):
        assert (
            scores[i] >= scores[i + 1]
        ), f"Chunks not sorted: score at {i} ({scores[i]}) < score at {i+1} ({scores[i+1]})"


def count_tokens_approximate(text: str) -> int:
    """
    Approximate token count for text.

    Uses simple word-based estimation for testing.
    """
    return len(text.split())


def create_markdown_document(headings_and_content: List[tuple]) -> str:
    """
    Create a markdown document from headings and content.

    Args:
        headings_and_content: List of (heading, content) tuples

    Returns:
        Formatted markdown string
    """
    sections = []

    for i, (heading, content) in enumerate(headings_and_content):
        level = "#" * (i % 3 + 1)  # Vary heading levels
        sections.append(f"{level} {heading}\n\n{content}\n")

    return "\n".join(sections)


def verify_document_structure(doc: Document):
    """
    Verify that a document has required fields and valid structure.

    Args:
        doc: Document instance to verify
    """
    assert doc.id is not None
    assert doc.tenant_id is not None
    assert doc.level in ["platform", "suite", "module", "entity"]
    assert doc.title is not None
    assert doc.status in ["active", "archived", "deleted"]
    assert doc.access_level in ["public", "internal", "confidential", "restricted"]
    assert doc.created_at is not None
    assert doc.updated_at is not None


def verify_chunk_structure(chunk: Chunk):
    """
    Verify that a chunk has required fields and valid structure.

    Args:
        chunk: Chunk instance to verify
    """
    assert chunk.id is not None
    assert chunk.document_id is not None
    assert chunk.ord >= 0
    assert chunk.content is not None
    assert len(chunk.content) > 0
    assert chunk.content_hash is not None
    assert len(chunk.content_hash) == 64  # SHA256 hash
    assert chunk.embedding is not None
    assert len(chunk.embedding) == 384  # Embedding dimension


def mock_httpx_post(response_data: Dict[str, Any], status_code: int = 200):
    """
    Create a mock for httpx.AsyncClient.post.

    Args:
        response_data: JSON response data
        status_code: HTTP status code

    Returns:
        Mock coroutine function
    """
    from unittest.mock import Mock

    async def mock_post(*args, **kwargs):
        response = Mock()
        response.status_code = status_code
        response.json.return_value = response_data
        response.raise_for_status = Mock()
        return response

    return mock_post


def create_test_query_payload(
    query: str,
    suite_id: str = None,
    module_id: str = None,
    top_k: int = 5,
    use_cache: bool = True,
    use_hybrid: bool = False,
) -> Dict[str, Any]:
    """
    Create a test query payload for /query endpoint.

    Args:
        query: Query text
        suite_id: Optional suite context
        module_id: Optional module context
        top_k: Number of chunks to retrieve
        use_cache: Whether to use cache
        use_hybrid: Whether to use hybrid retrieval

    Returns:
        Query payload dictionary
    """
    payload = {"query": query, "top_k": top_k, "use_cache": use_cache, "use_hybrid": use_hybrid}

    if suite_id:
        payload["suite_id"] = suite_id

    if module_id:
        payload["module_id"] = module_id

    return payload


def extract_document_ids(chunks: List[Dict[str, Any]]) -> List[str]:
    """
    Extract unique document IDs from list of chunks.

    Args:
        chunks: List of chunk dictionaries

    Returns:
        List of unique document IDs
    """
    return list(set(chunk.get("document_id") for chunk in chunks if "document_id" in chunk))


def calculate_embedding_similarity_matrix(embeddings: List[List[float]]) -> np.ndarray:
    """
    Calculate pairwise similarity matrix for list of embeddings.

    Args:
        embeddings: List of embedding vectors

    Returns:
        NxN similarity matrix
    """
    from app.embeddings import cosine_similarity

    n = len(embeddings)
    matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            matrix[i, j] = cosine_similarity(embeddings[i], embeddings[j])

    return matrix


def cleanup_test_data(db: Session, tenant_id: str = "test_tenant"):
    """
    Clean up test data for a tenant.

    Args:
        db: Database session
        tenant_id: Tenant ID to clean up
    """
    # Delete documents (chunks will cascade)
    db.query(Document).filter(Document.tenant_id == tenant_id).delete()
    db.commit()


# Convenience exports
__all__ = [
    "create_test_embedding",
    "create_test_document_with_chunks",
    "assert_similar_embeddings",
    "assert_chunks_sorted_by_score",
    "count_tokens_approximate",
    "create_markdown_document",
    "verify_document_structure",
    "verify_chunk_structure",
    "mock_httpx_post",
    "create_test_query_payload",
    "extract_document_ids",
    "calculate_embedding_similarity_matrix",
    "cleanup_test_data",
]
