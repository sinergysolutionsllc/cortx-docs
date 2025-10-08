"""
Document chunking service.

Implements semantic chunking that preserves context while maintaining
reasonable chunk sizes for embedding and retrieval.
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Token estimation (rough approximation: 1 token ≈ 4 characters)
CHARS_PER_TOKEN = 4

# Default chunking parameters
DEFAULT_CHUNK_SIZE = 512  # tokens
DEFAULT_CHUNK_OVERLAP = 50  # tokens
MIN_CHUNK_SIZE = 100  # tokens


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk."""

    ord: int
    content: str
    heading: Optional[str] = None
    page_number: Optional[int] = None
    token_count: Optional[int] = None
    start_char: int = 0
    end_char: int = 0


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Uses rough approximation: 1 token ≈ 4 characters
    More accurate than word count, less expensive than actual tokenization.
    """
    return len(text) // CHARS_PER_TOKEN


def extract_headings(text: str) -> List[Tuple[str, int]]:
    """
    Extract markdown-style headings from text.

    Returns:
        List of (heading_text, position) tuples
    """
    headings = []

    # Match markdown headings (# Header, ## Header, etc.)
    for match in re.finditer(r"^(#{1,6})\s+(.+)$", text, re.MULTILINE):
        level = len(match.group(1))
        heading = match.group(2).strip()
        position = match.start()
        headings.append((heading, position))

    return headings


def find_nearest_heading(position: int, headings: List[Tuple[str, int]]) -> Optional[str]:
    """
    Find the nearest heading before a given position.

    Args:
        position: Character position in document
        headings: List of (heading, position) tuples

    Returns:
        Heading text, or None if no heading found
    """
    # Find headings before this position
    before = [h for h in headings if h[1] <= position]

    if not before:
        return None

    # Return the closest one
    return before[-1][0]


def split_by_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs.

    Paragraphs are separated by double newlines or more.
    """
    # Split on double newlines
    paragraphs = re.split(r"\n\s*\n", text)

    # Filter out empty paragraphs
    return [p.strip() for p in paragraphs if p.strip()]


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    preserve_headings: bool = True,
) -> List[ChunkMetadata]:
    """
    Chunk text into semantically meaningful segments.

    Strategy:
    1. Split by paragraphs (preserve natural boundaries)
    2. Combine small paragraphs until reaching chunk_size
    3. Apply overlap to maintain context across chunks
    4. Preserve heading context for each chunk

    Args:
        text: Document text to chunk
        chunk_size: Target chunk size in tokens
        chunk_overlap: Overlap between chunks in tokens
        preserve_headings: Whether to track headings for context

    Returns:
        List of ChunkMetadata objects
    """
    if not text or not text.strip():
        return []

    # Extract headings if requested
    headings = extract_headings(text) if preserve_headings else []

    # Split into paragraphs
    paragraphs = split_by_paragraphs(text)

    if not paragraphs:
        return []

    chunks = []
    current_chunk = []
    current_tokens = 0
    current_start = 0
    chunk_ord = 0

    for para in paragraphs:
        para_tokens = estimate_tokens(para)

        # If single paragraph exceeds chunk_size, split it further
        if para_tokens > chunk_size * 1.5:
            # Save current chunk if it has content
            if current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(
                    ChunkMetadata(
                        ord=chunk_ord,
                        content=chunk_text,
                        heading=(
                            find_nearest_heading(current_start, headings)
                            if preserve_headings
                            else None
                        ),
                        token_count=estimate_tokens(chunk_text),
                        start_char=current_start,
                        end_char=current_start + len(chunk_text),
                    )
                )
                chunk_ord += 1
                current_chunk = []
                current_tokens = 0

            # Split large paragraph by sentences
            sentences = re.split(r"(?<=[.!?])\s+", para)
            temp_chunk = []
            temp_tokens = 0

            for sentence in sentences:
                sent_tokens = estimate_tokens(sentence)

                if temp_tokens + sent_tokens > chunk_size:
                    # Emit current temp chunk
                    if temp_chunk:
                        chunk_text = " ".join(temp_chunk)
                        chunks.append(
                            ChunkMetadata(
                                ord=chunk_ord,
                                content=chunk_text,
                                heading=(
                                    find_nearest_heading(current_start, headings)
                                    if preserve_headings
                                    else None
                                ),
                                token_count=estimate_tokens(chunk_text),
                                start_char=current_start,
                                end_char=current_start + len(chunk_text),
                            )
                        )
                        chunk_ord += 1

                        # Apply overlap (keep last few sentences)
                        if chunk_overlap > 0 and len(temp_chunk) > 1:
                            overlap_sentences = []
                            overlap_tokens = 0
                            for s in reversed(temp_chunk):
                                s_tokens = estimate_tokens(s)
                                if overlap_tokens + s_tokens <= chunk_overlap:
                                    overlap_sentences.insert(0, s)
                                    overlap_tokens += s_tokens
                                else:
                                    break
                            temp_chunk = overlap_sentences
                            temp_tokens = overlap_tokens
                        else:
                            temp_chunk = []
                            temp_tokens = 0

                temp_chunk.append(sentence)
                temp_tokens += sent_tokens

            # Emit remaining sentences
            if temp_chunk:
                chunk_text = " ".join(temp_chunk)
                chunks.append(
                    ChunkMetadata(
                        ord=chunk_ord,
                        content=chunk_text,
                        heading=(
                            find_nearest_heading(current_start, headings)
                            if preserve_headings
                            else None
                        ),
                        token_count=estimate_tokens(chunk_text),
                        start_char=current_start,
                        end_char=current_start + len(chunk_text),
                    )
                )
                chunk_ord += 1

            current_start += len(para)
            continue

        # If adding this paragraph would exceed chunk_size, emit current chunk
        if current_tokens + para_tokens > chunk_size and current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(
                ChunkMetadata(
                    ord=chunk_ord,
                    content=chunk_text,
                    heading=(
                        find_nearest_heading(current_start, headings) if preserve_headings else None
                    ),
                    token_count=estimate_tokens(chunk_text),
                    start_char=current_start,
                    end_char=current_start + len(chunk_text),
                )
            )
            chunk_ord += 1

            # Apply overlap
            if chunk_overlap > 0 and current_chunk:
                overlap_paras = []
                overlap_tokens = 0
                for p in reversed(current_chunk):
                    p_tokens = estimate_tokens(p)
                    if overlap_tokens + p_tokens <= chunk_overlap:
                        overlap_paras.insert(0, p)
                        overlap_tokens += p_tokens
                    else:
                        break
                current_chunk = overlap_paras
                current_tokens = overlap_tokens
            else:
                current_chunk = []
                current_tokens = 0

        # Add paragraph to current chunk
        current_chunk.append(para)
        current_tokens += para_tokens

    # Emit final chunk
    if current_chunk:
        chunk_text = "\n\n".join(current_chunk)
        chunks.append(
            ChunkMetadata(
                ord=chunk_ord,
                content=chunk_text,
                heading=(
                    find_nearest_heading(current_start, headings) if preserve_headings else None
                ),
                token_count=estimate_tokens(chunk_text),
                start_char=current_start,
                end_char=current_start + len(chunk_text),
            )
        )

    # Filter out chunks that are too small
    chunks = [c for c in chunks if c.token_count and c.token_count >= MIN_CHUNK_SIZE]

    logger.info(
        f"Chunked document into {len(chunks)} chunks (avg tokens: {sum(c.token_count or 0 for c in chunks) / len(chunks) if chunks else 0:.0f})"
    )

    return chunks


def chunk_markdown(
    markdown_text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[ChunkMetadata]:
    """
    Chunk markdown document, preserving section structure.

    Similar to chunk_text but optimized for markdown with headings.
    """
    return chunk_text(
        markdown_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap, preserve_headings=True
    )
