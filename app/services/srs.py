from typing import List
import io
import logging

import pdfplumber

from app.utils.utils import parse_requirements_from_text

logger = logging.getLogger(__name__)


def extract_text_from_pdf_bytes(data: bytes) -> str:
    """Extract text from a PDF file given its bytes."""
    text_parts: List[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            try:
                text = page.extract_text() or ""
            except Exception:
                logger.exception("Failed to extract text from a PDF page")
                text = ""
            if text:
                text_parts.append(text)
    return "\n".join(text_parts)


def parse_requirements_from_pdf_bytes(data: bytes) -> List[str]:
    """Extract text from PDF bytes and parse into requirement items."""
    text = extract_text_from_pdf_bytes(data)
    return parse_requirements_from_text(text)
