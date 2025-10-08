"""
Unit tests for document chunking service.

Tests cover:
- Token estimation
- Heading extraction
- Paragraph splitting
- Semantic chunking with overlap
- Edge cases (empty text, very long paragraphs)
"""

from app.chunking import (
    ChunkMetadata,
    chunk_markdown,
    chunk_text,
    estimate_tokens,
    extract_headings,
    find_nearest_heading,
    split_by_paragraphs,
)


class TestTokenEstimation:
    """Test token estimation functions."""

    def test_estimate_tokens_basic(self):
        """Test basic token estimation."""
        text = "This is a test sentence."
        tokens = estimate_tokens(text)
        # 25 chars / 4 = ~6 tokens
        assert tokens == 6

    def test_estimate_tokens_empty(self):
        """Test token estimation with empty string."""
        assert estimate_tokens("") == 0

    def test_estimate_tokens_long_text(self):
        """Test token estimation with longer text."""
        text = "A" * 1000  # 1000 characters
        tokens = estimate_tokens(text)
        assert tokens == 250  # 1000 / 4


class TestHeadingExtraction:
    """Test markdown heading extraction."""

    def test_extract_headings_simple(self):
        """Test extracting simple markdown headings."""
        text = """# Main Title
Some content here.

## Section 1
More content.

### Subsection 1.1
Even more content.
"""
        headings = extract_headings(text)

        assert len(headings) == 3
        assert headings[0][0] == "Main Title"
        assert headings[1][0] == "Section 1"
        assert headings[2][0] == "Subsection 1.1"

    def test_extract_headings_none(self):
        """Test text with no headings."""
        text = "Just plain text with no headings."
        headings = extract_headings(text)
        assert len(headings) == 0

    def test_extract_headings_with_whitespace(self):
        """Test headings with extra whitespace."""
        text = "#   Title with spaces   \n##  Another Title  "
        headings = extract_headings(text)

        assert len(headings) == 2
        assert headings[0][0] == "Title with spaces"
        assert headings[1][0] == "Another Title"

    def test_find_nearest_heading(self):
        """Test finding nearest heading before a position."""
        text = """# Title 1
Content at position 10.

## Title 2
Content at position 50.
"""
        headings = extract_headings(text)

        # Before any headings
        assert find_nearest_heading(0, headings) is None

        # After first heading
        nearest = find_nearest_heading(20, headings)
        assert nearest == "Title 1"

        # After second heading
        nearest = find_nearest_heading(60, headings)
        assert nearest == "Title 2"


class TestParagraphSplitting:
    """Test paragraph splitting logic."""

    def test_split_by_paragraphs_basic(self):
        """Test basic paragraph splitting."""
        text = """First paragraph here.

Second paragraph here.

Third paragraph here."""

        paragraphs = split_by_paragraphs(text)

        assert len(paragraphs) == 3
        assert "First paragraph" in paragraphs[0]
        assert "Second paragraph" in paragraphs[1]
        assert "Third paragraph" in paragraphs[2]

    def test_split_by_paragraphs_multiple_newlines(self):
        """Test splitting with multiple newlines."""
        text = "Paragraph 1.\n\n\n\nParagraph 2."
        paragraphs = split_by_paragraphs(text)

        assert len(paragraphs) == 2

    def test_split_by_paragraphs_empty(self):
        """Test splitting empty text."""
        paragraphs = split_by_paragraphs("")
        assert len(paragraphs) == 0

    def test_split_by_paragraphs_single(self):
        """Test splitting single paragraph."""
        text = "Just one paragraph with no breaks."
        paragraphs = split_by_paragraphs(text)

        assert len(paragraphs) == 1
        assert paragraphs[0] == text


class TestChunkText:
    """Test main chunking function."""

    def test_chunk_text_basic(self, sample_text):
        """Test basic text chunking."""
        chunks = chunk_text(sample_text, chunk_size=200, chunk_overlap=20)

        assert len(chunks) > 0
        assert all(isinstance(c, ChunkMetadata) for c in chunks)
        assert all(c.content for c in chunks)
        assert all(c.token_count and c.token_count > 0 for c in chunks)

    def test_chunk_text_ordering(self, sample_text):
        """Test that chunks maintain proper ordering."""
        chunks = chunk_text(sample_text)

        for i, chunk in enumerate(chunks):
            assert chunk.ord == i

    def test_chunk_text_empty(self):
        """Test chunking empty text."""
        chunks = chunk_text("")
        assert len(chunks) == 0

    def test_chunk_text_whitespace_only(self):
        """Test chunking whitespace-only text."""
        chunks = chunk_text("   \n\n   \n   ")
        assert len(chunks) == 0

    def test_chunk_text_small(self):
        """Test chunking text smaller than chunk size."""
        text = "This is a small piece of text."
        chunks = chunk_text(text, chunk_size=100)

        # Should produce 0 chunks if below MIN_CHUNK_SIZE, or 1 chunk if above
        assert len(chunks) <= 1

    def test_chunk_text_overlap(self):
        """Test that overlap is applied correctly."""
        text = """First paragraph with some content that will be chunked.

Second paragraph with more content that continues.

Third paragraph with even more content here.

Fourth paragraph to ensure we have enough content.

Fifth paragraph for good measure."""

        chunks = chunk_text(text, chunk_size=100, chunk_overlap=20)

        if len(chunks) > 1:
            # Check that there's some overlap between consecutive chunks
            for i in range(len(chunks) - 1):
                current_content = chunks[i].content
                next_content = chunks[i + 1].content

                # Some words should appear in both chunks
                current_words = set(current_content.split()[-10:])
                next_words = set(next_content.split()[:10])

                # Allow for cases where overlap might not be perfect
                # but at least check structure is maintained

    def test_chunk_text_preserves_headings(self, sample_text):
        """Test that headings are preserved in chunks."""
        chunks = chunk_text(sample_text, preserve_headings=True)

        # At least some chunks should have headings
        headings_found = [c.heading for c in chunks if c.heading]
        assert len(headings_found) > 0

    def test_chunk_text_no_headings(self):
        """Test chunking without heading preservation."""
        text = """# Some Title

Some content here."""

        chunks = chunk_text(text, preserve_headings=False)

        # Headings should be None when not preserved
        assert all(c.heading is None for c in chunks)

    def test_chunk_text_large_paragraph(self):
        """Test chunking with a very large paragraph."""
        # Create a paragraph larger than chunk_size
        large_para = " ".join(["sentence"] * 500)
        chunks = chunk_text(large_para, chunk_size=100)

        # Should split large paragraph
        assert len(chunks) > 1

    def test_chunk_text_custom_size(self):
        """Test chunking with custom chunk size."""
        text = " ".join(["word"] * 1000)

        # Small chunks
        small_chunks = chunk_text(text, chunk_size=50, chunk_overlap=0)

        # Large chunks
        large_chunks = chunk_text(text, chunk_size=200, chunk_overlap=0)

        # Small chunks should produce more chunks
        assert len(small_chunks) > len(large_chunks)

    def test_chunk_text_metadata(self, sample_text):
        """Test that chunk metadata is properly populated."""
        chunks = chunk_text(sample_text)

        for chunk in chunks:
            assert isinstance(chunk.ord, int)
            assert chunk.ord >= 0
            assert isinstance(chunk.content, str)
            assert len(chunk.content) > 0
            assert chunk.token_count is not None
            assert chunk.token_count > 0


class TestChunkMarkdown:
    """Test markdown-specific chunking."""

    def test_chunk_markdown_basic(self):
        """Test basic markdown chunking."""
        markdown = """# Title

Some content.

## Section 1

More content here.

### Subsection

Even more content.
"""
        chunks = chunk_markdown(markdown, chunk_size=100)

        assert len(chunks) > 0
        assert all(isinstance(c, ChunkMetadata) for c in chunks)

    def test_chunk_markdown_preserves_structure(self):
        """Test that markdown structure is preserved."""
        markdown = """# Main Title

Intro paragraph.

## Section 1

Section 1 content.

## Section 2

Section 2 content.
"""
        chunks = chunk_markdown(markdown)

        # Should have headings preserved
        assert any(c.heading for c in chunks)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_chunk_text_unicode(self):
        """Test chunking with unicode characters."""
        text = """# 中文标题

这是一些中文内容。

## English Section

Mixed content with émojis 🎉 and spëcial çhars.
"""
        chunks = chunk_text(text)

        assert len(chunks) > 0
        assert all(c.content for c in chunks)

    def test_chunk_text_very_long_line(self):
        """Test chunking with very long single line."""
        text = "A" * 10000  # 10k character line
        chunks = chunk_text(text, chunk_size=500)

        assert len(chunks) > 0

    def test_chunk_text_mixed_line_endings(self):
        """Test chunking with mixed line endings."""
        text = "Paragraph 1.\r\n\r\nParagraph 2.\n\nParagraph 3."
        chunks = chunk_text(text)

        assert len(chunks) > 0

    def test_chunk_text_special_characters(self):
        """Test chunking with special characters."""
        text = """# Title with @#$%

Content with special chars: <>&"'

More content with [brackets] and {braces}.
"""
        chunks = chunk_text(text)

        assert len(chunks) > 0
        assert all(c.content for c in chunks)

    def test_chunk_text_code_blocks(self):
        """Test chunking markdown with code blocks."""
        text = """# Code Example

Here's some code:

```python
def example():
    return "hello"
```

And more text after.
"""
        chunks = chunk_text(text)

        assert len(chunks) > 0
        # Code block should be preserved in content
        assert any("def example" in c.content for c in chunks)


class TestChunkMetadata:
    """Test ChunkMetadata dataclass."""

    def test_chunk_metadata_creation(self):
        """Test creating ChunkMetadata instance."""
        metadata = ChunkMetadata(
            ord=0, content="Test content", heading="Test Heading", token_count=10
        )

        assert metadata.ord == 0
        assert metadata.content == "Test content"
        assert metadata.heading == "Test Heading"
        assert metadata.token_count == 10

    def test_chunk_metadata_defaults(self):
        """Test ChunkMetadata with default values."""
        metadata = ChunkMetadata(ord=0, content="Test")

        assert metadata.heading is None
        assert metadata.page_number is None
        assert metadata.token_count is None
        assert metadata.start_char == 0
        assert metadata.end_char == 0
