"""POST /api/v1/cv/parse — Milestone 11B: CV PDF upload -> local text
extraction -> RunPod GLM-5.3 -> validated draft for user confirmation.

Returns a draft only; never writes to the stored profile (see
app.services.cv_extraction_service's module docstring for why). The
user reviews/edits the draft's suggested_profile client-side, then
submits it to the EXISTING, unchanged POST /profile/analyze to actually
create or update a profile and proceed to matching — this route adds
nothing new to that handoff (requirement 5).

Privacy: the uploaded file is read into memory only for the duration of
this request, validated/extracted, then discarded — never written to
disk, never logged, and the response never echoes the raw CV text in
the successful ("ok") path (only a short, bounded preview in the
fallback/manual-review paths — see cv_extraction_service.py).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.time import utc_now_iso
from app.schemas.cv import CvParseResponse
from app.services.cv_extraction_service import run_cv_extraction
from app.services.cv_pdf import MAX_PDF_BYTES, CvPdfError, validate_and_extract

router = APIRouter()

# Read in chunks, stopping as soon as the cap is exceeded, so an
# oversized upload is rejected without first buffering the whole thing
# into memory (requirement 1's 5 MB cap, enforced defensively).
_READ_CHUNK_BYTES = 256 * 1024

# A declared Content-Type is advisory, not authoritative — the real
# security boundary is the %PDF- magic-byte check and the pypdf parse
# inside validate_and_extract(), which run regardless of what's declared
# here. This is a cheap, early rejection of *obviously* wrong uploads
# (an image, a zip, plain text) before spending any time reading/
# parsing them; a missing or generic type is never rejected on this
# basis alone, since many legitimate clients omit or generalize it.
_ACCEPTED_CONTENT_TYPES = {"application/pdf", "application/x-pdf", "application/octet-stream", ""}


async def _read_bounded(file: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_READ_CHUNK_BYTES)
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            raise AppError(
                code="FILE_TOO_LARGE",
                message=f"The uploaded file exceeds the {max_bytes // (1024 * 1024)} MB limit.",
                status_code=413,
            )
    return b"".join(chunks)


@router.post("/cv/parse", response_model=CvParseResponse)
async def parse_cv(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> CvParseResponse:
    declared_type = (file.content_type or "").lower()
    if declared_type and declared_type not in _ACCEPTED_CONTENT_TYPES:
        raise AppError(
            code="INVALID_CV_FILE",
            message="Only PDF files are accepted.",
            status_code=422,
        )

    file_bytes = await _read_bounded(file, MAX_PDF_BYTES)

    try:
        pdf_result = validate_and_extract(file_bytes)
    except CvPdfError as exc:
        raise AppError(code="INVALID_CV_FILE", message=exc.message, status_code=422) from exc
    finally:
        del file_bytes  # the raw upload is never needed again after this point

    data, warnings = run_cv_extraction(pdf_result, settings)

    return CvParseResponse(data=data, generated_at=utc_now_iso(), warnings=warnings)
