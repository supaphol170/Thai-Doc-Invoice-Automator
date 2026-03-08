"""
loader.py
─────────
Handles reading PDF files and images into structured page data.
- PDF  → uses pdfplumber (text + tables + image preview, no Poppler needed)
- Image → uses EasyOCR (Thai + English)
"""

import io
import numpy as np
import pdfplumber
import easyocr
import streamlit as st
from PIL import Image

from extractor import extract_invoice_fields


# ── OCR reader (cached so model loads only once) ─────────────────────────────

@st.cache_resource
def get_ocr_reader() -> easyocr.Reader:
    """Load EasyOCR model once and reuse across Streamlit reruns."""
    return easyocr.Reader(['th', 'en'])


def run_ocr(img: Image.Image) -> list:
    """Run EasyOCR on a PIL Image and return list of text strings."""
    reader = get_ocr_reader()
    return reader.readtext(np.array(img), detail=0)


# ── PDF loader ───────────────────────────────────────────────────────────────

def load_pdf(filename: str, file_bytes: bytes) -> list:
    """
    Extract all pages from a PDF.

    Returns
    -------
    List of dicts: {meta, image, lines}
    """
    entries = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            # Text + tables
            text   = page.extract_text() or ""
            lines  = [l.strip() for l in text.split("\n") if l.strip()]
            tables = page.extract_tables() or []

            # Structured fields
            fields         = extract_invoice_fields(lines, tables)
            fields["File"] = filename
            fields["Page"] = page_num

            # Page preview image
            img = _render_pdf_page(page)

            entries.append({"meta": fields, "image": img, "lines": lines})
    return entries


def _render_pdf_page(page) -> Image.Image | None:
    """Render a pdfplumber page to a PIL Image for preview."""
    try:
        return page.to_image(resolution=150).original
    except Exception:
        return None


# ── Image loader ─────────────────────────────────────────────────────────────

def load_image(filename: str, file_bytes: bytes) -> dict:
    """
    Run OCR on an image file.

    Returns
    -------
    Single dict: {meta, image, lines}
    """
    img        = Image.open(io.BytesIO(file_bytes))
    text_lines = run_ocr(img)
    fields     = extract_invoice_fields(text_lines)
    fields["File"] = filename
    fields["Page"] = 1
    return {"meta": fields, "image": img, "lines": text_lines}


# ── Unified entry point ───────────────────────────────────────────────────────

def process_uploaded_file(uploaded_file) -> list:
    """
    Dispatch to PDF or image loader based on MIME type.

    Parameters
    ----------
    uploaded_file : Streamlit UploadedFile

    Returns
    -------
    List of page entry dicts: [{meta, image, lines}, ...]
    """
    file_bytes = uploaded_file.read()

    if uploaded_file.type == "application/pdf":
        return load_pdf(uploaded_file.name, file_bytes)
    else:
        return [load_image(uploaded_file.name, file_bytes)]
