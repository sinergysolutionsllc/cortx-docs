"""
OCR processing engine with multi-tier pipeline
"""

import base64
import io
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import pytesseract
from anthropic import Anthropic
from pdf2image import convert_from_bytes
from PIL import Image

from .models import OCRStatus, OCRTier

logger = logging.getLogger(__name__)

# Configuration
TESSERACT_CONFIDENCE_THRESHOLD = float(os.getenv("OCR_TESSERACT_THRESHOLD", "80.0"))
AI_CONFIDENCE_THRESHOLD = float(os.getenv("OCR_AI_THRESHOLD", "85.0"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")


class DocumentPreprocessor:
    """Preprocesses documents for better OCR accuracy"""

    @staticmethod
    def preprocess_image(image: Image.Image) -> Image.Image:
        """Apply preprocessing to improve OCR accuracy"""
        try:
            # Convert PIL Image to numpy array
            img_array = np.array(image.convert("RGB"))

            # Convert to grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Denoise
            denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)

            # Deskew if needed
            coords = np.column_stack(np.where(denoised > 0))
            if len(coords) > 0:
                angle = cv2.minAreaRect(coords)[-1]
                if angle < -45:
                    angle = -(90 + angle)
                else:
                    angle = -angle

                if abs(angle) > 0.5:  # Only deskew if needed
                    (h, w) = denoised.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, angle, 1.0)
                    denoised = cv2.warpAffine(
                        denoised, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
                    )

            # Convert back to PIL Image
            return Image.fromarray(denoised)

        except Exception as e:
            logger.warning(f"Preprocessing failed: {e}. Using original image.")
            return image

    @staticmethod
    def split_pdf_pages(pdf_bytes: bytes) -> List[Image.Image]:
        """Convert PDF to list of images"""
        try:
            images = convert_from_bytes(pdf_bytes, dpi=300)
            return images
        except Exception as e:
            logger.error(f"PDF conversion failed: {e}")
            raise ValueError(f"Failed to convert PDF: {e}")


class TesseractOCR:
    """Tesseract OCR engine for modern, clear documents"""

    @staticmethod
    def extract_text(
        image: Image.Image, preprocess: bool = True
    ) -> Tuple[str, float, Dict[str, Any]]:
        """
        Extract text using Tesseract OCR

        Returns:
            Tuple of (text, confidence_score, metadata)
        """
        try:
            # Preprocess image
            if preprocess:
                preprocessor = DocumentPreprocessor()
                image = preprocessor.preprocess_image(image)

            # Configure Tesseract
            custom_config = r"--oem 3 --psm 6"  # LSTM OCR Engine + Assume uniform block of text

            # Extract text and detailed data
            text = pytesseract.image_to_string(image, config=custom_config)
            data = pytesseract.image_to_data(
                image, config=custom_config, output_type=pytesseract.Output.DICT
            )

            # Calculate confidence
            confidences = [int(conf) for conf in data["conf"] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            # Generate metadata
            metadata = {
                "word_count": len([w for w in data["text"] if w.strip()]),
                "line_count": len(set(data["line_num"])),
                "block_count": len(set(data["block_num"])),
                "low_confidence_words": len([c for c in confidences if c < 60]),
            }

            return text.strip(), avg_confidence, metadata

        except Exception as e:
            logger.error(f"Tesseract extraction failed: {e}")
            raise RuntimeError(f"Tesseract OCR failed: {e}")


class ClaudeVisionOCR:
    """Claude 3.5 Sonnet Vision for complex/historical documents"""

    def __init__(self):
        self.client = None
        if ANTHROPIC_API_KEY:
            self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        else:
            logger.warning("Anthropic API key not configured. AI tier will be unavailable.")

    def extract_text(
        self, image: Image.Image, extract_fields: Optional[List[str]] = None
    ) -> Tuple[str, float, Dict[str, Any]]:
        """
        Extract text using Claude Vision API

        Returns:
            Tuple of (text, confidence_score, metadata)
        """
        if not self.client:
            raise RuntimeError("Anthropic API not configured")

        try:
            # Convert image to base64
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

            # Build prompt
            base_prompt = (
                "Extract all text from this document with high accuracy. "
                "Preserve the original formatting, line breaks, and structure. "
                "If the document is handwritten, historical, or degraded, use your best judgment to interpret it."
            )

            if extract_fields:
                field_list = ", ".join(extract_fields)
                base_prompt += f"\n\nAlso extract these specific fields if present: {field_list}"

            # Call Claude Vision
            message = self.client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_data,
                                },
                            },
                            {"type": "text", "text": base_prompt},
                        ],
                    }
                ],
            )

            # Extract response
            text = message.content[0].text if message.content else ""

            # Claude doesn't provide explicit confidence, estimate based on response quality
            # Use response length and stop_reason as heuristics
            confidence = 90.0  # Base confidence for AI
            if message.stop_reason == "end_turn":
                confidence = 95.0  # Complete response
            elif len(text) < 10:
                confidence = 70.0  # Very short response might indicate issues

            metadata = {
                "model": message.model,
                "stop_reason": message.stop_reason,
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
            }

            return text.strip(), confidence, metadata

        except Exception as e:
            logger.error(f"Claude Vision extraction failed: {e}")
            raise RuntimeError(f"AI OCR failed: {e}")


class OCRProcessor:
    """Main OCR processing pipeline with multi-tier fallback"""

    def __init__(self):
        self.tesseract = TesseractOCR()
        self.claude_vision = ClaudeVisionOCR()

    def process_document(
        self,
        document_data: str,
        document_type: Optional[str] = None,
        force_tier: Optional[OCRTier] = None,
        confidence_threshold: Optional[float] = None,
        extract_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Process document through multi-tier OCR pipeline

        Args:
            document_data: Base64-encoded document
            document_type: MIME type or file extension
            force_tier: Force specific OCR tier
            confidence_threshold: Custom confidence threshold
            extract_fields: Specific fields to extract

        Returns:
            Dictionary with processing results
        """
        start_time = time.time()
        threshold = confidence_threshold or TESSERACT_CONFIDENCE_THRESHOLD

        try:
            # Decode document
            doc_bytes = base64.b64decode(document_data)

            # Determine if PDF
            is_pdf = (document_type and "pdf" in document_type.lower()) or doc_bytes[:4] == b"%PDF"

            # Convert to images
            if is_pdf:
                preprocessor = DocumentPreprocessor()
                images = preprocessor.split_pdf_pages(doc_bytes)
            else:
                image = Image.open(io.BytesIO(doc_bytes))
                images = [image]

            page_count = len(images)
            all_text = []
            tier_used = None
            final_confidence = 0.0
            tesseract_confidence = None
            ai_confidence = None
            warnings = {}

            # Process each page
            for page_num, image in enumerate(images, 1):
                logger.info(f"Processing page {page_num}/{page_count}")

                # Force tier if specified
                if force_tier == OCRTier.AI_VISION:
                    text, confidence, metadata = self._process_ai_tier(image, extract_fields)
                    tier_used = OCRTier.AI_VISION
                    ai_confidence = confidence
                elif force_tier == OCRTier.TESSERACT:
                    text, confidence, metadata = self._process_tesseract_tier(image)
                    tier_used = OCRTier.TESSERACT
                    tesseract_confidence = confidence
                else:
                    # Auto-tiering logic
                    text, confidence, metadata, tier_used = self._auto_tier_process(
                        image, threshold, extract_fields
                    )
                    if tier_used == OCRTier.TESSERACT:
                        tesseract_confidence = confidence
                    elif tier_used == OCRTier.AI_VISION:
                        ai_confidence = confidence

                all_text.append(text)
                final_confidence = max(final_confidence, confidence)

                # Collect warnings
                if metadata.get("low_confidence_words", 0) > 5:
                    warnings[f"page_{page_num}"] = "High number of low-confidence words detected"

            # Combine results
            extracted_text = "\n\n--- Page Break ---\n\n".join(all_text)
            processing_time_ms = int((time.time() - start_time) * 1000)

            result = {
                "extracted_text": extracted_text,
                "confidence_score": final_confidence,
                "tier_used": tier_used,
                "page_count": page_count,
                "processing_time_ms": processing_time_ms,
                "tesseract_confidence": tesseract_confidence,
                "ai_confidence": ai_confidence,
                "warnings": warnings if warnings else None,
                "status": OCRStatus.COMPLETED,
            }

            # Check if human review needed
            if final_confidence < threshold:
                result["status"] = OCRStatus.AWAITING_REVIEW
                result["warnings"] = result.get("warnings", {})
                result["warnings"][
                    "low_confidence"
                ] = f"Confidence {final_confidence:.1f}% below threshold {threshold:.1f}%"

            return result

        except Exception as e:
            logger.error(f"OCR processing failed: {e}", exc_info=True)
            return {
                "status": OCRStatus.FAILED,
                "error_message": str(e),
                "processing_time_ms": int((time.time() - start_time) * 1000),
            }

    def _process_tesseract_tier(self, image: Image.Image) -> Tuple[str, float, Dict[str, Any]]:
        """Process with Tesseract tier"""
        logger.info("Processing with Tesseract tier")
        return self.tesseract.extract_text(image)

    def _process_ai_tier(
        self, image: Image.Image, extract_fields: Optional[List[str]] = None
    ) -> Tuple[str, float, Dict[str, Any]]:
        """Process with AI Vision tier"""
        logger.info("Processing with AI Vision tier")
        return self.claude_vision.extract_text(image, extract_fields)

    def _auto_tier_process(
        self, image: Image.Image, threshold: float, extract_fields: Optional[List[str]] = None
    ) -> Tuple[str, float, Dict[str, Any], OCRTier]:
        """
        Auto-select best tier based on confidence

        Returns:
            Tuple of (text, confidence, metadata, tier_used)
        """
        # Try Tesseract first (fast and cheap)
        try:
            text, confidence, metadata = self._process_tesseract_tier(image)

            if confidence >= threshold:
                logger.info(f"Tesseract tier succeeded with {confidence:.1f}% confidence")
                return text, confidence, metadata, OCRTier.TESSERACT

            logger.info(
                f"Tesseract confidence {confidence:.1f}% below threshold {threshold:.1f}%. "
                "Escalating to AI tier."
            )
        except Exception as e:
            logger.warning(f"Tesseract tier failed: {e}. Escalating to AI tier.")

        # Fallback to AI tier
        try:
            text, confidence, metadata = self._process_ai_tier(image, extract_fields)
            logger.info(f"AI tier completed with {confidence:.1f}% confidence")
            return text, confidence, metadata, OCRTier.AI_VISION
        except Exception as e:
            logger.error(f"AI tier also failed: {e}")
            # Return Tesseract result as fallback even if low confidence
            if "text" in locals():
                return text, confidence, metadata, OCRTier.TESSERACT
            raise
