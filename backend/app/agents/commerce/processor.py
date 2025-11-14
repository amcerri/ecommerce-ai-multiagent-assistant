"""
Commerce processor (multi-format document processing with OCR).

Overview
  Processes documents in multiple formats (PDF, DOCX, TXT, images) with
  intelligent OCR fallback. Evaluates text quality and uses OCR only when
  necessary. Supports preprocessing for better OCR results.

Design
  - **Multi-Format**: Supports PDF, DOCX, TXT, and images (PNG, JPG, etc.).
  - **Intelligent OCR**: Evaluates text quality before deciding on OCR.
  - **Image Preprocessing**: Preprocesses images for better OCR results.
  - **Quality Evaluation**: Heuristics to assess text extraction quality.

Integration
  - Consumes: LocalStorage, pdfplumber, python-docx, pytesseract, PIL.
  - Returns: Extracted text with metadata and OCR flags.
  - Used by: CommerceAgent for document processing.
  - Observability: Logs processing operations and OCR usage.

Usage
  >>> from app.agents.commerce.processor import CommerceProcessor
  >>> processor = CommerceProcessor(storage)
  >>> result = await processor.process_file("path/to/file.pdf", "pdf")
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from app.config.exceptions import StorageException, ValidationException
from app.infrastructure.storage.local_storage import LocalStorage

logger = logging.getLogger(__name__)

# Try to import required libraries (optional dependencies)
try:
    import pdfplumber

    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    pdfplumber = None  # type: ignore

try:
    from docx import Document as DocxDocument

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    DocxDocument = None  # type: ignore

try:
    from PIL import Image
    import pytesseract

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    Image = None  # type: ignore
    pytesseract = None  # type: ignore


class CommerceProcessor:
    """Document processor for commerce documents.

    Processes documents in multiple formats with intelligent OCR fallback.
    Evaluates text quality and uses OCR only when necessary.
    """

    def __init__(self, storage: LocalStorage) -> None:
        """Initialize commerce processor.

        Args:
            storage: Local storage for file access.
        """
        self._storage = storage

    async def process_file(
        self,
        file_path: str,
        file_type: str,
    ) -> Dict[str, Any]:
        """Process file and extract text.

        Processes file based on type, extracts text, evaluates quality,
        and uses OCR if necessary.

        Args:
            file_path: File path in storage.
            file_type: File type ("pdf", "docx", "txt", "png", "jpg", etc.).

        Returns:
            Dictionary with text, metadata, needs_ocr, ocr_used.

        Raises:
            StorageException: If file cannot be read.
            ValidationException: If file type is unsupported.
        """
        try:
            # Get file content from storage
            file_content = await self._storage.get(file_path)

            # Create temporary file for processing
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp_file:
                tmp_path = Path(tmp_file.name)
                tmp_path.write_bytes(file_content)

            try:
                # Process based on file type
                if file_type.lower() == "pdf":
                    text = await self._extract_text_pdf(tmp_path)
                    needs_ocr = False
                elif file_type.lower() == "docx":
                    text = await self._extract_text_docx(tmp_path)
                    needs_ocr = False
                elif file_type.lower() == "txt":
                    text = await self._extract_text_txt(tmp_path)
                    needs_ocr = False
                elif file_type.lower() in ["png", "jpg", "jpeg", "tiff", "bmp"]:
                    text = ""
                    needs_ocr = True
                else:
                    raise ValidationException(
                        message=f"Unsupported file type: {file_type}",
                        details={"file_path": file_path, "file_type": file_type},
                    )

                # Evaluate text quality
                quality_score = self._evaluate_text_quality(text)

                # Use OCR if quality is low or if it's an image
                ocr_used = False
                if needs_ocr or quality_score < 0.5:
                    if OCR_AVAILABLE:
                        try:
                            ocr_text = await self._perform_ocr(tmp_path)
                            if ocr_text and len(ocr_text.strip()) > len(text.strip()):
                                text = ocr_text
                                ocr_used = True
                        except Exception as e:
                            logger.warning(f"OCR failed: {e}")
                            # Continue with original text if OCR fails
                    else:
                        logger.warning("OCR requested but pytesseract not available")

                return {
                    "text": text,
                    "metadata": {
                        "file_type": file_type,
                        "quality_score": quality_score,
                        "needs_ocr": needs_ocr,
                        "ocr_used": ocr_used,
                    },
                    "needs_ocr": needs_ocr,
                    "ocr_used": ocr_used,
                }
            finally:
                # Clean up temporary file
                tmp_path.unlink(missing_ok=True)

        except Exception as e:
            if isinstance(e, (StorageException, ValidationException)):
                raise
            raise StorageException(
                message=f"Failed to process file: {str(e)}",
                details={"file_path": file_path, "file_type": file_type, "error": str(e)},
            ) from e

    async def _extract_text_pdf(self, file_path: Path) -> str:
        """Extract text from PDF.

        Uses pdfplumber to extract text from all pages.

        Args:
            file_path: Path to PDF file.

        Returns:
            Extracted text from all pages.
        """
        if not PDFPLUMBER_AVAILABLE:
            raise ValidationException(
                message="pdfplumber is required for PDF processing",
                details={"file_path": str(file_path)},
            )

        try:
            text_parts: list[str] = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

            return "\n\n".join(text_parts)
        except Exception as e:
            raise ValidationException(
                message=f"Failed to extract text from PDF: {str(e)}",
                details={"file_path": str(file_path), "error": str(e)},
            ) from e

    async def _extract_text_docx(self, file_path: Path) -> str:
        """Extract text from DOCX.

        Uses python-docx to extract text preserving structure.

        Args:
            file_path: Path to DOCX file.

        Returns:
            Extracted text with preserved structure.
        """
        if not DOCX_AVAILABLE:
            raise ValidationException(
                message="python-docx is required for DOCX processing",
                details={"file_path": str(file_path)},
            )

        try:
            doc = DocxDocument(file_path)
            text_parts: list[str] = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)

            return "\n".join(text_parts)
        except Exception as e:
            raise ValidationException(
                message=f"Failed to extract text from DOCX: {str(e)}",
                details={"file_path": str(file_path), "error": str(e)},
            ) from e

    async def _extract_text_txt(self, file_path: Path) -> str:
        """Extract text from TXT file.

        Reads text file directly.

        Args:
            file_path: Path to TXT file.

        Returns:
            File content as text.
        """
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            return text
        except Exception as e:
            raise ValidationException(
                message=f"Failed to read text file: {str(e)}",
                details={"file_path": str(file_path), "error": str(e)},
            ) from e

    def _evaluate_text_quality(self, text: str) -> float:
        """Evaluate text extraction quality.

        Uses heuristics to assess text quality (0.0-1.0).

        Args:
            text: Extracted text to evaluate.

        Returns:
            Quality score (0.0-1.0, higher is better).
        """
        if not text or len(text.strip()) < 10:
            return 0.0

        # Heuristic 1: Average word length (very short words = OCR issues)
        words = text.split()
        if not words:
            return 0.0

        avg_word_length = sum(len(word) for word in words) / len(words)
        word_length_score = min(avg_word_length / 5.0, 1.0)  # Normalize to 0-1

        # Heuristic 2: Ratio of alphanumeric to special characters
        alnum_count = sum(1 for c in text if c.isalnum())
        total_chars = len(text.replace(" ", ""))
        if total_chars > 0:
            alnum_ratio = alnum_count / total_chars
        else:
            alnum_ratio = 0.0

        # Heuristic 3: Presence of paragraphs (structure)
        has_paragraphs = "\n\n" in text or text.count("\n") > 5
        structure_score = 1.0 if has_paragraphs else 0.5

        # Heuristic 4: Text length (very short = likely incomplete)
        length_score = min(len(text) / 500.0, 1.0)  # Normalize to 0-1

        # Combined score (weighted)
        quality = (
            word_length_score * 0.3
            + alnum_ratio * 0.3
            + structure_score * 0.2
            + length_score * 0.2
        )

        return min(max(quality, 0.0), 1.0)

    async def _perform_ocr(self, file_path: Path) -> str:
        """Perform OCR on image file.

        Preprocesses image and uses Tesseract OCR to extract text.

        Args:
            file_path: Path to image file.

        Returns:
            Extracted text from OCR.
        """
        if not OCR_AVAILABLE:
            raise ValidationException(
                message="pytesseract and PIL are required for OCR",
                details={"file_path": str(file_path)},
            )

        try:
            # Load image
            image = Image.open(file_path)

            # Preprocess image (improve contrast, binarization)
            processed_image = self._preprocess_image(image)

            # Perform OCR
            text = await asyncio.to_thread(
                pytesseract.image_to_string,
                processed_image,
                lang="por+eng",  # Portuguese and English
            )

            # Post-process text (clean up)
            text = self._postprocess_ocr_text(text)

            return text
        except Exception as e:
            raise ValidationException(
                message=f"OCR failed: {str(e)}",
                details={"file_path": str(file_path), "error": str(e)},
            ) from e

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results.

        Improves contrast, converts to grayscale, and applies binarization.

        Args:
            image: PIL Image to preprocess.

        Returns:
            Preprocessed PIL Image.
        """
        # Convert to grayscale if needed
        if image.mode != "L":
            image = image.convert("L")

        # Enhance contrast (optional - can use PIL.ImageEnhance)
        # For now, just return grayscale image
        # In production, you might want to apply additional preprocessing

        return image

    def _postprocess_ocr_text(self, text: str) -> str:
        """Post-process OCR text.

        Cleans up OCR text by removing common artifacts and normalizing.

        Args:
            text: Raw OCR text.

        Returns:
            Cleaned OCR text.
        """
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)

