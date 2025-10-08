"""
Unit tests for OCR processor module
"""

import base64
from unittest.mock import MagicMock, Mock, patch

import pytest
from app.models import OCRStatus, OCRTier
from app.processor import ClaudeVisionOCR, DocumentPreprocessor, OCRProcessor, TesseractOCR
from PIL import Image

# ============================================================================
# DocumentPreprocessor Tests
# ============================================================================


class TestDocumentPreprocessor:
    """Tests for DocumentPreprocessor class"""

    def test_preprocess_image_success(self, sample_image):
        """Test successful image preprocessing"""
        preprocessor = DocumentPreprocessor()
        result = preprocessor.preprocess_image(sample_image)

        assert isinstance(result, Image.Image)
        assert result.size == sample_image.size

    def test_preprocess_image_handles_grayscale(self):
        """Test preprocessing of grayscale images"""
        # Create grayscale image
        gray_img = Image.new("L", (100, 100), color=128)
        preprocessor = DocumentPreprocessor()

        result = preprocessor.preprocess_image(gray_img)

        assert isinstance(result, Image.Image)

    def test_preprocess_image_handles_small_image(self):
        """Test preprocessing of very small images"""
        small_img = Image.new("RGB", (10, 10), color="white")
        preprocessor = DocumentPreprocessor()

        result = preprocessor.preprocess_image(small_img)

        assert isinstance(result, Image.Image)

    def test_preprocess_image_error_handling(self):
        """Test preprocessing handles errors gracefully"""
        preprocessor = DocumentPreprocessor()

        # Create a mock image that raises an error during conversion
        mock_img = Mock(spec=Image.Image)
        mock_img.convert.side_effect = Exception("Conversion error")

        result = preprocessor.preprocess_image(mock_img)

        # Should return original image on error
        assert result == mock_img

    @patch("app.processor.convert_from_bytes")
    def test_split_pdf_pages_success(self, mock_convert):
        """Test successful PDF page splitting"""
        # Mock PDF conversion
        mock_images = [
            Image.new("RGB", (800, 600), color="white"),
            Image.new("RGB", (800, 600), color="white"),
        ]
        mock_convert.return_value = mock_images

        preprocessor = DocumentPreprocessor()
        pdf_bytes = b"%PDF-1.4\n%Test PDF\n%%EOF"

        result = preprocessor.split_pdf_pages(pdf_bytes)

        assert len(result) == 2
        assert all(isinstance(img, Image.Image) for img in result)
        mock_convert.assert_called_once_with(pdf_bytes, dpi=300)

    @patch("app.processor.convert_from_bytes")
    def test_split_pdf_pages_error(self, mock_convert):
        """Test PDF splitting error handling"""
        mock_convert.side_effect = Exception("PDF conversion failed")

        preprocessor = DocumentPreprocessor()
        pdf_bytes = b"%PDF-invalid"

        with pytest.raises(ValueError, match="Failed to convert PDF"):
            preprocessor.split_pdf_pages(pdf_bytes)


# ============================================================================
# TesseractOCR Tests
# ============================================================================


class TestTesseractOCR:
    """Tests for TesseractOCR class"""

    @patch("app.processor.pytesseract.image_to_string")
    @patch("app.processor.pytesseract.image_to_data")
    def test_extract_text_success(
        self, mock_image_to_data, mock_image_to_string, sample_image, sample_tesseract_data
    ):
        """Test successful text extraction with Tesseract"""
        mock_image_to_string.return_value = "Sample Invoice\nInvoice #12345"
        mock_image_to_data.return_value = sample_tesseract_data

        ocr = TesseractOCR()
        text, confidence, metadata = ocr.extract_text(sample_image)

        assert isinstance(text, str)
        assert len(text) > 0
        assert isinstance(confidence, float)
        assert confidence > 0
        assert isinstance(metadata, dict)
        assert "word_count" in metadata
        assert "line_count" in metadata

    @patch("app.processor.pytesseract.image_to_string")
    @patch("app.processor.pytesseract.image_to_data")
    def test_extract_text_with_preprocessing(
        self, mock_image_to_data, mock_image_to_string, sample_image, sample_tesseract_data
    ):
        """Test text extraction with image preprocessing"""
        mock_image_to_string.return_value = "Preprocessed text"
        mock_image_to_data.return_value = sample_tesseract_data

        ocr = TesseractOCR()
        text, confidence, metadata = ocr.extract_text(sample_image, preprocess=True)

        assert text == "Preprocessed text"
        mock_image_to_string.assert_called_once()

    @patch("app.processor.pytesseract.image_to_string")
    @patch("app.processor.pytesseract.image_to_data")
    def test_extract_text_without_preprocessing(
        self, mock_image_to_data, mock_image_to_string, sample_image, sample_tesseract_data
    ):
        """Test text extraction without preprocessing"""
        mock_image_to_string.return_value = "Raw text"
        mock_image_to_data.return_value = sample_tesseract_data

        ocr = TesseractOCR()
        text, confidence, metadata = ocr.extract_text(sample_image, preprocess=False)

        assert text == "Raw text"

    @patch("app.processor.pytesseract.image_to_string")
    @patch("app.processor.pytesseract.image_to_data")
    def test_extract_text_low_confidence(
        self,
        mock_image_to_data,
        mock_image_to_string,
        sample_image,
        sample_low_confidence_tesseract_data,
    ):
        """Test extraction with low confidence scores"""
        mock_image_to_string.return_value = "Unclear text"
        mock_image_to_data.return_value = sample_low_confidence_tesseract_data

        ocr = TesseractOCR()
        text, confidence, metadata = ocr.extract_text(sample_image)

        assert confidence < 60
        assert metadata["low_confidence_words"] > 0

    @patch("app.processor.pytesseract.image_to_string")
    @patch("app.processor.pytesseract.image_to_data")
    def test_extract_text_high_confidence(
        self, mock_image_to_data, mock_image_to_string, sample_image, sample_tesseract_data
    ):
        """Test extraction with high confidence scores"""
        mock_image_to_string.return_value = "Clear text"
        mock_image_to_data.return_value = sample_tesseract_data

        ocr = TesseractOCR()
        text, confidence, metadata = ocr.extract_text(sample_image)

        assert confidence > 80
        assert metadata["word_count"] > 0

    @patch("app.processor.pytesseract.image_to_string")
    def test_extract_text_error(self, mock_image_to_string, sample_image):
        """Test error handling during extraction"""
        mock_image_to_string.side_effect = Exception("Tesseract failed")

        ocr = TesseractOCR()

        with pytest.raises(RuntimeError, match="Tesseract OCR failed"):
            ocr.extract_text(sample_image)

    @patch("app.processor.pytesseract.image_to_string")
    @patch("app.processor.pytesseract.image_to_data")
    def test_extract_text_empty_result(
        self, mock_image_to_data, mock_image_to_string, sample_image
    ):
        """Test extraction with empty result"""
        mock_image_to_string.return_value = "   \n  "
        mock_image_to_data.return_value = {
            "text": [""],
            "conf": [-1],
            "line_num": [1],
            "block_num": [1],
        }

        ocr = TesseractOCR()
        text, confidence, metadata = ocr.extract_text(sample_image)

        assert text == ""
        assert confidence == 0.0


# ============================================================================
# ClaudeVisionOCR Tests
# ============================================================================


class TestClaudeVisionOCR:
    """Tests for ClaudeVisionOCR class"""

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    def test_initialization_with_api_key(self):
        """Test initialization with API key present"""
        ocr = ClaudeVisionOCR()
        assert ocr.client is not None

    @patch.dict("os.environ", {}, clear=True)
    def test_initialization_without_api_key(self):
        """Test initialization without API key"""
        ocr = ClaudeVisionOCR()
        assert ocr.client is None

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    @patch("app.processor.Anthropic")
    def test_extract_text_success(self, mock_anthropic_class, sample_image):
        """Test successful text extraction with Claude Vision"""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Extracted text from Claude")]
        mock_message.stop_reason = "end_turn"
        mock_message.model = "claude-3-5-sonnet-20241022"
        mock_message.usage = MagicMock(input_tokens=100, output_tokens=50)

        mock_client.messages.create.return_value = mock_message

        ocr = ClaudeVisionOCR()
        text, confidence, metadata = ocr.extract_text(sample_image)

        assert text == "Extracted text from Claude"
        assert confidence == 95.0  # Complete response
        assert metadata["model"] == "claude-3-5-sonnet-20241022"
        assert metadata["stop_reason"] == "end_turn"
        assert metadata["input_tokens"] == 100
        assert metadata["output_tokens"] == 50

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    @patch("app.processor.Anthropic")
    def test_extract_text_with_fields(self, mock_anthropic_class, sample_image):
        """Test extraction with specific fields requested"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Invoice data")]
        mock_message.stop_reason = "end_turn"
        mock_message.model = "claude-3-5-sonnet-20241022"
        mock_message.usage = MagicMock(input_tokens=100, output_tokens=50)

        mock_client.messages.create.return_value = mock_message

        ocr = ClaudeVisionOCR()
        extract_fields = ["invoice_number", "date", "amount"]
        text, confidence, metadata = ocr.extract_text(sample_image, extract_fields)

        assert text == "Invoice data"
        # Verify the prompt included field extraction request
        call_args = mock_client.messages.create.call_args
        messages = call_args.kwargs["messages"]
        prompt_text = messages[0]["content"][1]["text"]
        assert "invoice_number" in prompt_text
        assert "date" in prompt_text
        assert "amount" in prompt_text

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    @patch("app.processor.Anthropic")
    def test_extract_text_short_response(self, mock_anthropic_class, sample_image):
        """Test extraction with very short response (low confidence)"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="No")]
        mock_message.stop_reason = "max_tokens"
        mock_message.model = "claude-3-5-sonnet-20241022"
        mock_message.usage = MagicMock(input_tokens=100, output_tokens=1)

        mock_client.messages.create.return_value = mock_message

        ocr = ClaudeVisionOCR()
        text, confidence, metadata = ocr.extract_text(sample_image)

        assert text == "No"
        assert confidence == 70.0  # Low confidence for short response

    @patch.dict("os.environ", {}, clear=True)
    def test_extract_text_no_api_key(self, sample_image):
        """Test extraction fails without API key"""
        ocr = ClaudeVisionOCR()

        with pytest.raises(RuntimeError, match="Anthropic API not configured"):
            ocr.extract_text(sample_image)

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    @patch("app.processor.Anthropic")
    def test_extract_text_api_error(self, mock_anthropic_class, sample_image):
        """Test API error handling"""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")

        ocr = ClaudeVisionOCR()

        with pytest.raises(RuntimeError, match="AI OCR failed"):
            ocr.extract_text(sample_image)


# ============================================================================
# OCRProcessor Tests
# ============================================================================


class TestOCRProcessor:
    """Tests for OCRProcessor class"""

    def test_initialization(self):
        """Test OCR processor initialization"""
        processor = OCRProcessor()
        assert processor.tesseract is not None
        assert processor.claude_vision is not None

    @patch("app.processor.TesseractOCR.extract_text")
    def test_process_document_simple_image(self, mock_tesseract, sample_image_base64):
        """Test processing a simple image document"""
        mock_tesseract.return_value = (
            "Extracted text",
            90.0,
            {"word_count": 10, "line_count": 3, "block_count": 1, "low_confidence_words": 0},
        )

        processor = OCRProcessor()
        result = processor.process_document(
            document_data=sample_image_base64, document_type="image/png"
        )

        assert result["status"] == OCRStatus.COMPLETED
        assert result["extracted_text"] == "Extracted text"
        assert result["confidence_score"] == 90.0
        assert result["tier_used"] == OCRTier.TESSERACT
        assert result["page_count"] == 1
        assert "processing_time_ms" in result

    @patch("app.processor.TesseractOCR.extract_text")
    def test_process_document_high_confidence(self, mock_tesseract, sample_image_base64):
        """Test processing with high confidence (Tesseract only)"""
        mock_tesseract.return_value = (
            "Clear text",
            95.0,
            {"word_count": 20, "line_count": 5, "block_count": 2, "low_confidence_words": 0},
        )

        processor = OCRProcessor()
        result = processor.process_document(
            document_data=sample_image_base64, confidence_threshold=80.0
        )

        assert result["tier_used"] == OCRTier.TESSERACT
        assert result["confidence_score"] == 95.0
        assert result["status"] == OCRStatus.COMPLETED

    @patch("app.processor.ClaudeVisionOCR.extract_text")
    @patch("app.processor.TesseractOCR.extract_text")
    def test_process_document_escalation_to_ai(
        self, mock_tesseract, mock_claude, sample_image_base64
    ):
        """Test escalation from Tesseract to AI when confidence is low"""
        # Tesseract returns low confidence
        mock_tesseract.return_value = (
            "Unclear text",
            65.0,
            {"word_count": 5, "line_count": 2, "block_count": 1, "low_confidence_words": 3},
        )

        # Claude returns high confidence
        mock_claude.return_value = (
            "Clear AI-extracted text",
            92.0,
            {
                "model": "claude-3-5-sonnet-20241022",
                "stop_reason": "end_turn",
                "input_tokens": 100,
                "output_tokens": 50,
            },
        )

        processor = OCRProcessor()
        result = processor.process_document(
            document_data=sample_image_base64, confidence_threshold=80.0
        )

        assert result["tier_used"] == OCRTier.AI_VISION
        assert result["confidence_score"] == 92.0
        assert result["extracted_text"] == "Clear AI-extracted text"
        assert result["tesseract_confidence"] == 65.0
        assert result["ai_confidence"] == 92.0

    @patch("app.processor.TesseractOCR.extract_text")
    def test_process_document_force_tesseract(self, mock_tesseract, sample_image_base64):
        """Test forcing Tesseract tier"""
        mock_tesseract.return_value = (
            "Forced Tesseract text",
            75.0,
            {"word_count": 15, "line_count": 4, "block_count": 1, "low_confidence_words": 2},
        )

        processor = OCRProcessor()
        result = processor.process_document(
            document_data=sample_image_base64, force_tier=OCRTier.TESSERACT
        )

        assert result["tier_used"] == OCRTier.TESSERACT
        assert result["extracted_text"] == "Forced Tesseract text"

    @patch("app.processor.ClaudeVisionOCR.extract_text")
    def test_process_document_force_ai(self, mock_claude, sample_image_base64):
        """Test forcing AI Vision tier"""
        mock_claude.return_value = (
            "Forced AI text",
            93.0,
            {
                "model": "claude-3-5-sonnet-20241022",
                "stop_reason": "end_turn",
                "input_tokens": 100,
                "output_tokens": 50,
            },
        )

        processor = OCRProcessor()
        result = processor.process_document(
            document_data=sample_image_base64, force_tier=OCRTier.AI_VISION
        )

        assert result["tier_used"] == OCRTier.AI_VISION
        assert result["extracted_text"] == "Forced AI text"

    @patch("app.processor.ClaudeVisionOCR.extract_text")
    @patch("app.processor.TesseractOCR.extract_text")
    def test_process_document_with_extract_fields(
        self, mock_tesseract, mock_claude, sample_image_base64
    ):
        """Test document processing with field extraction"""
        mock_tesseract.return_value = (
            "Document text",
            85.0,
            {"word_count": 10, "line_count": 3, "block_count": 1, "low_confidence_words": 0},
        )

        processor = OCRProcessor()
        extract_fields = ["invoice_number", "date", "amount"]
        result = processor.process_document(
            document_data=sample_image_base64, extract_fields=extract_fields
        )

        assert result["status"] == OCRStatus.COMPLETED

    @patch("app.processor.ClaudeVisionOCR.extract_text")
    @patch("app.processor.TesseractOCR.extract_text")
    def test_process_document_awaiting_review(
        self, mock_tesseract, mock_claude, sample_image_base64
    ):
        """Test document requiring human review due to low confidence"""
        # Both tiers return low confidence
        mock_tesseract.return_value = (
            "Low confidence text",
            60.0,
            {"word_count": 8, "line_count": 2, "block_count": 1, "low_confidence_words": 5},
        )

        mock_claude.return_value = (
            "Still uncertain text",
            70.0,
            {
                "model": "claude-3-5-sonnet-20241022",
                "stop_reason": "end_turn",
                "input_tokens": 100,
                "output_tokens": 50,
            },
        )

        processor = OCRProcessor()
        result = processor.process_document(
            document_data=sample_image_base64, confidence_threshold=80.0
        )

        assert result["status"] == OCRStatus.AWAITING_REVIEW
        assert "low_confidence" in result["warnings"]

    @patch("app.processor.DocumentPreprocessor.split_pdf_pages")
    @patch("app.processor.TesseractOCR.extract_text")
    def test_process_document_pdf_multipage(
        self, mock_tesseract, mock_split_pdf, sample_image_base64
    ):
        """Test processing multi-page PDF"""
        # Mock PDF splitting to return 3 pages
        mock_pages = [
            Image.new("RGB", (800, 600), color="white"),
            Image.new("RGB", (800, 600), color="white"),
            Image.new("RGB", (800, 600), color="white"),
        ]
        mock_split_pdf.return_value = mock_pages

        # Mock Tesseract for each page
        mock_tesseract.side_effect = [
            (
                "Page 1 text",
                90.0,
                {"word_count": 10, "line_count": 3, "block_count": 1, "low_confidence_words": 0},
            ),
            (
                "Page 2 text",
                92.0,
                {"word_count": 12, "line_count": 4, "block_count": 1, "low_confidence_words": 0},
            ),
            (
                "Page 3 text",
                88.0,
                {"word_count": 9, "line_count": 3, "block_count": 1, "low_confidence_words": 0},
            ),
        ]

        processor = OCRProcessor()
        result = processor.process_document(
            document_data=sample_image_base64, document_type="application/pdf"
        )

        assert result["page_count"] == 3
        assert "Page 1 text" in result["extracted_text"]
        assert "Page 2 text" in result["extracted_text"]
        assert "Page 3 text" in result["extracted_text"]
        assert "--- Page Break ---" in result["extracted_text"]
        assert result["confidence_score"] == 92.0  # Max confidence

    def test_process_document_invalid_base64(self):
        """Test processing with invalid base64 data"""
        processor = OCRProcessor()
        result = processor.process_document(
            document_data="not-valid-base64!!!", document_type="image/png"
        )

        assert result["status"] == OCRStatus.FAILED
        assert "error_message" in result

    def test_process_document_invalid_image(self):
        """Test processing with invalid image data"""
        processor = OCRProcessor()
        # Valid base64 but not an image
        invalid_data = base64.b64encode(b"not an image").decode("utf-8")
        result = processor.process_document(document_data=invalid_data, document_type="image/png")

        assert result["status"] == OCRStatus.FAILED
        assert "error_message" in result

    @patch("app.processor.TesseractOCR.extract_text")
    def test_process_document_with_warnings(self, mock_tesseract, sample_image_base64):
        """Test document processing generates warnings for quality issues"""
        mock_tesseract.return_value = (
            "Text with issues",
            85.0,
            {"word_count": 20, "line_count": 5, "block_count": 2, "low_confidence_words": 10},
        )

        processor = OCRProcessor()
        result = processor.process_document(document_data=sample_image_base64)

        assert result["warnings"] is not None
        assert "page_1" in result["warnings"]
