"""Extract raw text from uploaded homework files (PDF or image).

Text-based PDF pages are read directly with pdfplumber. Pages that come back
mostly empty (i.e. the homework was scanned as an image) are rendered to an
image with PyMuPDF and passed through OCR. Bare image uploads go straight to
OCR. Tesseract may not be installed in every environment, so OCR failures
degrade to an empty string rather than crashing the request.
"""
from __future__ import annotations

import pdfplumber
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

MIN_CHARS_PER_PAGE = 20


def _ocr_image(image: Image.Image) -> str:
    try:
        return pytesseract.image_to_string(image)
    except Exception:
        # Covers TesseractNotFoundError and any other OCR backend failure.
        return ""


def extract_text_from_pdf(path: str) -> str:
    pages: list[str] = []
    doc = None
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages):
            text = (page.extract_text() or "").strip()
            if len(text) < MIN_CHARS_PER_PAGE:
                if doc is None:
                    doc = fitz.open(path)
                pix = doc[page_number].get_pixmap(dpi=300)
                image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                ocr_text = _ocr_image(image).strip()
                if len(ocr_text) > len(text):
                    text = ocr_text
            pages.append(text)
    if doc is not None:
        doc.close()
    return "\n".join(pages).strip()


def extract_text_from_image(path: str) -> str:
    with Image.open(path) as image:
        return _ocr_image(image).strip()


def extract_text(path: str, filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(path)
    if lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")):
        return extract_text_from_image(path)
    raise ValueError(f"Unsupported file type: {filename}")
