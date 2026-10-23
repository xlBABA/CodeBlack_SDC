"""Milestone 11B/11E: orchestrates POST /api/v1/cv/parse.

Pipeline: PDF validation/extraction (cv_pdf.py, local, no network) ->
RunPod GLM-5.3 (glm_client.py) -> Pydantic validation of GLM's untrusted
output (app.schemas.cv.GlmCvExtraction) -> per-skill evidence validation
against the locally-extracted CV text (_evidence_is_supported) -> skill
mapping (Hussain's SkillNormalizer, deterministic, never invents an ID)
-> CvDraftProfile. A skill with missing/unverifiable evidence never
reaches mapping at all — see _validate_and_map_skills.

Every GLM/parsing failure mode degrades to a "manual_review" CvParseData
rather than raising past this module (requirement 6: never fabricate a
result). A PDF with no extractable text short-circuits before ever
calling GLM at all.
"""
from __future__ import annotations

import logging
import re

from app.core.config import Settings
from app.schemas.cv import (
    CvDraftProfile,
    CvMappedSkill,
    CvParseData,
    CvSkillNeedsReview,
    CvUnmappedSkill,
    GlmCvExtraction,
    GlmSkillEntry,
)
from app.schemas.profile import SkillRef, StudentProfile
from app.services.cv_pdf import PdfExtractionResult
from app.services.glm_client import GlmExtractionError, extract_cv_fields
from app.services.hussain_matching.normalizer import SkillNormalizer
from app.services.role_catalog_cached import _load_json

logger = logging.getLogger(__name__)

NO_TEXT_WARNING = (
    "No selectable text was found in this PDF (it may be a scanned "
    "image). Please fill in your profile manually — automatic text "
    "recognition (OCR) is not performed."
)
MANUAL_REVIEW_WARNING = (
    "Automatic extraction was unavailable, so this is an empty draft for "
    "manual entry. Nothing was fabricated in its place."
)
MISSING_EVIDENCE_REASON = (
    "No supporting quote was provided for this skill, so it was not "
    "added automatically. Add it yourself if it's accurate."
)
UNVERIFIED_EVIDENCE_REASON = (
    "The supporting quote for this skill could not be found in your CV "
    "text, so it was not added automatically. Add it yourself if it's "
    "accurate."
)
# Guards against a trivially short "evidence" string (e.g. a single
# letter) that would make the substring check meaningless.
MIN_EVIDENCE_CHARS = 2


def _load_skill_catalogue() -> list[dict]:
    return _load_json("skills.json")["skills"]


def _normalize_whitespace(text: str) -> str:
    """Collapse all whitespace runs (spaces, tabs, newlines — including
    the kind PDF text extraction commonly introduces between words/
    lines) to single spaces, for a tolerant-but-not-loose comparison."""
    return re.sub(r"\s+", " ", text).strip()


def _evidence_is_supported(evidence: str | None, cv_text: str) -> bool:
    """True only if `evidence` is a real, non-trivial, word-for-word
    (modulo whitespace) substring of the locally-extracted CV text.
    Never a fuzzy/semantic match — an unrelated or hallucinated quote
    must fail this check (requirement 4)."""
    if not evidence:
        return False
    normalized_evidence = _normalize_whitespace(evidence).lower()
    if len(normalized_evidence) < MIN_EVIDENCE_CHARS:
        return False
    normalized_text = _normalize_whitespace(cv_text).lower()
    return normalized_evidence in normalized_text


def _validate_and_map_skills(
    skill_entries: list[GlmSkillEntry], cv_text: str
) -> tuple[list[CvMappedSkill], list[CvUnmappedSkill], list[CvSkillNeedsReview]]:
    """Evidence validation (requirement 4) runs before catalogue mapping:
    a skill whose evidence is missing or not actually found in the CV
    text is excluded from the automatically-suggested profile entirely
    and reported in `skills_requiring_review`, regardless of whether it
    would otherwise match the catalogue. Catalogue mapping itself stays
    deterministic exact/alias matching only (SkillNormalizer) — never a
    guess, never an invented skill_id (requirement 3/4)."""
    normalizer = SkillNormalizer(_load_skill_catalogue())
    mapped: list[CvMappedSkill] = []
    unmapped: list[CvUnmappedSkill] = []
    needs_review: list[CvSkillNeedsReview] = []
    seen_ids: set[str] = set()
    for entry in skill_entries:
        name = entry.name.strip()
        if not name:
            continue
        if not _evidence_is_supported(entry.evidence, cv_text):
            reason = MISSING_EVIDENCE_REASON if not entry.evidence else UNVERIFIED_EVIDENCE_REASON
            needs_review.append(CvSkillNeedsReview(name=name, reason=reason))
            continue
        evidence = entry.evidence.strip()  # non-empty/non-None, guaranteed by the check above
        result = normalizer.normalize(name)
        if result.skill_id and result.skill_id not in seen_ids:
            mapped.append(
                CvMappedSkill(skill_id=result.skill_id, name=result.name, raw_text=name, evidence=evidence)
            )
            seen_ids.add(result.skill_id)
        elif not result.skill_id:
            unmapped.append(CvUnmappedSkill(raw_text=name, evidence=evidence))
    return mapped, unmapped, needs_review


def _build_suggested_profile(
    extraction: GlmCvExtraction, mapped_skills: list[CvMappedSkill]
) -> StudentProfile:
    """A sensible pre-filled default for the review UI, never an
    authoritative result — the user confirms/edits before it is ever
    submitted to POST /profile/analyze (requirement 5)."""
    projects = [
        (f"{p.title}: {p.description}" if p.description else p.title)[:500]
        for p in extraction.projects
    ]

    experience_parts = [extraction.summary] if extraction.summary else []
    for e in extraction.experience:
        piece = " ".join(
            part for part in (e.role, f"at {e.organization}" if e.organization else None, e.description) if part
        )
        if piece.strip():
            experience_parts.append(piece.strip())
    experience_summary = " | ".join(experience_parts)[:2000] or None

    # degree/education_level: a CV's "Bachelor of Science in X" does not
    # cleanly split into our two fields without inference. degree holds
    # whichever literal text GLM actually extracted (field of study,
    # falling back to the raw degree title); education_level is left
    # for the user to set — classifying "undergraduate vs graduate"
    # from a title is a judgment call this draft does not make for them
    # (requirement 3: do not hallucinate).
    degree = None
    if extraction.education:
        first = extraction.education[0]
        degree = first.field_of_study or first.degree

    return StudentProfile(
        education_level=None,
        degree=degree,
        interests=[],  # never invented — a CV rarely states explicit career interests
        skills=[SkillRef(skill_id=m.skill_id, name=m.name) for m in mapped_skills],
        projects=projects,
        experience_summary=experience_summary,
    )


def _empty_draft() -> CvDraftProfile:
    """An honestly-empty draft for the manual_review/no_extractable_text
    states. Takes no warning text — CvDraftProfile has no warnings field
    of its own; the caller already returns the matching warning
    (NO_TEXT_WARNING/MANUAL_REVIEW_WARNING) separately in CvParseData's
    sibling warnings list."""
    return CvDraftProfile(
        suggested_profile=StudentProfile(interests=[], skills=[], projects=[]),
    )


def run_cv_extraction(pdf_result: PdfExtractionResult, settings: Settings) -> tuple[CvParseData, list[str]]:
    """Returns (CvParseData, warnings). Never raises — every failure path
    is represented as a status + warning, per requirement 6."""
    if not pdf_result.has_extractable_text:
        return (
            CvParseData(
                status="no_extractable_text",
                draft=_empty_draft(),
                page_count=pdf_result.page_count,
                extracted_text_preview=None,
            ),
            [NO_TEXT_WARNING],
        )

    api_key = settings.RUNPOD_API_KEY.get_secret_value() if settings.RUNPOD_API_KEY else ""
    try:
        result = extract_cv_fields(
            pdf_result.text,
            api_key=api_key,
            base_url=settings.RUNPOD_GLM_BASE_URL,
            model=settings.RUNPOD_GLM_MODEL,
        )
    except GlmExtractionError as exc:
        logger.warning("CV extraction fell back to manual review (%s)", exc.reason)
        return (
            CvParseData(
                status="manual_review",
                draft=_empty_draft(),
                page_count=pdf_result.page_count,
                # A short, bounded preview only in this fallback path
                # (requirement 6) — never the full document, and never
                # returned at all in the successful "ok" path below.
                extracted_text_preview=pdf_result.text[:500],
            ),
            [MANUAL_REVIEW_WARNING, f"Extraction service issue: {exc.reason}"],
        )

    try:
        extraction = GlmCvExtraction.model_validate(result.raw_json)
    except Exception:
        logger.warning("GLM output failed schema validation; falling back to manual review")
        return (
            CvParseData(
                status="manual_review",
                draft=_empty_draft(),
                page_count=pdf_result.page_count,
                extracted_text_preview=pdf_result.text[:500],
            ),
            [MANUAL_REVIEW_WARNING, "The extraction service's output did not match the expected format."],
        )

    mapped_skills, unmapped_skills, skills_requiring_review = _validate_and_map_skills(
        extraction.skills, pdf_result.text
    )
    draft = CvDraftProfile(
        name=extraction.name,
        summary=extraction.summary,
        education=extraction.education,
        mapped_skills=mapped_skills,
        unmapped_skills=unmapped_skills,
        skills_requiring_review=skills_requiring_review,
        projects=extraction.projects,
        experience=extraction.experience,
        certifications=extraction.certifications,
        suggested_profile=_build_suggested_profile(extraction, mapped_skills),
    )
    warnings = [
        "Extracted automatically; please review every field before confirming — nothing here is final."
    ]
    if unmapped_skills:
        warnings.append(
            f"{len(unmapped_skills)} skill(s) were not recognized against the current catalogue "
            "and were not added to your profile automatically; review them below."
        )
    if skills_requiring_review:
        warnings.append(
            f"{len(skills_requiring_review)} skill(s) could not be automatically verified against "
            "your CV text and were not added to your profile automatically; add them yourself if "
            "they're accurate."
        )
    return CvParseData(status="ok", draft=draft, page_count=pdf_result.page_count, extracted_text_preview=None), warnings
