"""Milestone 11B: local, no-OCR PDF validation and text extraction for CV
uploads. Runs entirely offline — no network call, no RunPod, no GLM.

Privacy: this module itself never logs or persists file bytes or
extracted text; it only returns them to its caller, which is responsible
for the same discipline (see cv_extraction_service.py / cv.py). pypdf is
pure-Python (no compiled extension), keeping this Python 3.11-compatible
with no platform-specific wheels.
"""
from __future__ import annotations

import io
from dataclasses import dataclass

from pypdf import PdfReader

MAX_PDF_BYTES = 5 * 1024 * 1024  # 5 MB — requirement 1's explicit cap
# Below this many extracted characters, treat the PDF as having no
# meaningful selectable text (a scanned/image-only PDF, or a near-empty
# one) rather than attempting OCR, per requirement 1's explicit scope.
MIN_EXTRACTABLE_CHARS = 20
_HEADER_SEARCH_WINDOW = 1024  # PDF spec permits some bytes before %PDF-


class CvPdfError(Exception):
    """A PDF could not be validated or safely parsed.

    `message` is always safe to show the user directly (never includes
    file content, stack traces, or library internals).
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


@dataclass
class PdfExtractionResult:
    text: str
    page_count: int
    has_extractable_text: bool


def validate_and_extract(file_bytes: bytes) -> PdfExtractionResult:
    """Validate size/format/encryption, then extract selectable text.

    Raises CvPdfError for anything the caller should surface as a clean
    4xx: empty upload, oversize, not-a-PDF, encrypted, or unparseable.
    A PDF with no (or near-no) extractable text is NOT an error here —
    that's the scanned/image-only case, returned with
    has_extractable_text=False for the caller to handle gracefully
    (requirement 1: "without requiring OCR").
    """
    if not file_bytes:
        raise CvPdfError("The uploaded file is empty.")
    if len(file_bytes) > MAX_PDF_BYTES:
        raise CvPdfError(
            f"The uploaded file exceeds the {MAX_PDF_BYTES // (1024 * 1024)} MB limit."
        )
    if b"%PDF-" not in file_bytes[:_HEADER_SEARCH_WINDOW]:
        raise CvPdfError("The uploaded file is not a valid PDF.")

    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception as exc:  # pypdf raises several distinct error types for malformed input
        raise CvPdfError("The uploaded file could not be read as a PDF.") from exc

    if reader.is_encrypted:
        raise CvPdfError(
            "This PDF is password-protected. Please upload an unprotected PDF."
        )

    try:
        page_count = len(reader.pages)
        page_texts = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise CvPdfError("The uploaded PDF could not be processed.") from exc

    if page_count == 0:
        raise CvPdfError("The uploaded PDF has no pages.")

    text = "\n".join(page_texts).strip()
    return PdfExtractionResult(
        text=text,
        page_count=page_count,
        has_extractable_text=len(text) >= MIN_EXTRACTABLE_CHARS,
    )
