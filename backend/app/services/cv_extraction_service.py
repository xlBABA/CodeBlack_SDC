"""Milestone 11B/11E/12C-8E: orchestrates POST /api/v1/cv/parse.

Pipeline: PDF validation/extraction (cv_pdf.py, local, no network) ->
RunPod GLM-5.3 (glm_client.py) -> schema normalization of GLM's untrusted
output (_clean_glm_json — Milestone 12C-8E) -> Pydantic validation
(app.schemas.cv.GlmCvExtraction) -> per-skill evidence validation against
the locally-extracted CV text (_evidence_is_supported) -> skill mapping
(Hussain's SkillNormalizer, deterministic, never invents an ID) ->
CvDraftProfile. A skill with missing/unverifiable evidence never reaches
mapping at all — see _validate_and_map_skills.

Every GLM/parsing failure mode degrades to a "manual_review" CvParseData
rather than raising past this module (requirement 6: never fabricate a
result). A PDF with no extractable text short-circuits before ever
calling GLM at all.

Milestone 12C-8E root cause: a real GLM-5.3 deployment's response does
not always match app.schemas.cv's schema byte-for-byte (a null list
instead of [], an omitted key, a skill reported as a bare string instead
of {name, evidence}, one oversized/mistyped field on an otherwise-good
entry) — and GlmCvExtraction.model_validate() previously validated the
*entire* response as one atomic unit, so any single such mismatch
anywhere (even in one list item) discarded the whole extraction,
including every field GLM got right. _clean_glm_json() below normalizes
the harmless variations and isolates/validates each list entry on its
own, so one bad entry degrades only itself (never the whole response) —
see _clean_list_field/_coerce_skill_entry. GlmCvExtraction.model_validate()
remains the final, honest safety net for anything this normalization
cannot make sense of.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.schemas.cv import (
    CvCertificationEntry,
    CvDraftProfile,
    CvEducationEntry,
    CvExperienceEntry,
    CvMappedSkill,
    CvParseData,
    CvProjectEntry,
    CvSkillNeedsReview,
    CvUnmappedSkill,
    GlmCvExtraction,
    GlmSkillEntry,
)
from app.schemas.profile import SkillRef, StudentProfile
from app.services.cv_pdf import PdfExtractionResult
from app.services.glm_client import REQUEST_TIMEOUT_SECONDS, GlmExtractionError, extract_cv_fields
from app.services.hussain_matching.normalizer import SkillNormalizer
from app.services.role_catalog_cached import _load_json

logger = logging.getLogger(__name__)

NO_TEXT_WARNING = (
    "No selectable text was found in this PDF (it may be a scanned "
    "image). Please fill in your profile manually — automatic text "
    "recognition (OCR) is not performed."
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
# Generic, student-facing text for when automatic extraction can't run.
CV_UNAVAILABLE_WARNING = (
    "We couldn't read your CV automatically right now. Please review or "
    "fill in your details below."
)
# Guards against a trivially short "evidence" string (e.g. a single
# letter) that would make the substring check meaningless.
MIN_EVIDENCE_CHARS = 2

# Milestone 12C-8E: every top-level list field GLM may return, and the
# schema each of its items must become. Order has no significance.
_LIST_FIELD_MODELS: dict[str, type[BaseModel]] = {
    "education": CvEducationEntry,
    "projects": CvProjectEntry,
    "experience": CvExperienceEntry,
    "certifications": CvCertificationEntry,
}


@dataclass(frozen=True)
class _LlmCallConfig:
    api_key: str
    base_url: str
    model: str
    timeout: float
    provider: str
    key_name: str


def _llm_call_config(settings: Settings) -> _LlmCallConfig | None:
    """The LLM endpoint CV extraction calls, per LLM_PROVIDER.

    "runpod" is unchanged: RUNPOD_API_KEY + RUNPOD_GLM_*, with
    glm_client's own default timeout (a missing key is still reported by
    extract_cv_fields itself). "openrouter" uses only LLM_API_KEY,
    LLM_BASE_URL and LLM_MODEL — never RUNPOD_API_KEY — and returns None,
    after logging which variable names are missing (never their values),
    if any of them is unset."""
    if settings.LLM_PROVIDER == "openrouter":
        api_key = settings.LLM_API_KEY.get_secret_value() if settings.LLM_API_KEY else ""
        values = {"LLM_API_KEY": api_key, "LLM_BASE_URL": settings.LLM_BASE_URL, "LLM_MODEL": settings.LLM_MODEL}
        missing = [name for name, value in values.items() if not (value or "").strip()]
        if missing:
            logger.warning(
                "CV extraction skipped: LLM_PROVIDER=openrouter but %s not set; "
                "falling back to manual review",
                ", ".join(missing),
            )
            return None
        return _LlmCallConfig(
            api_key=api_key.strip(),
            base_url=settings.LLM_BASE_URL.strip(),
            model=settings.LLM_MODEL.strip(),
            timeout=settings.LLM_TIMEOUT_SECONDS,
            provider="openrouter",
            key_name="LLM_API_KEY",
        )
    return _LlmCallConfig(
        api_key=settings.RUNPOD_API_KEY.get_secret_value() if settings.RUNPOD_API_KEY else "",
        base_url=settings.RUNPOD_GLM_BASE_URL,
        model=settings.RUNPOD_GLM_MODEL,
        timeout=REQUEST_TIMEOUT_SECONDS,
        provider="runpod",
        key_name="RUNPOD_API_KEY",
    )


def _load_skill_catalogue() -> list[dict]:
    return _load_json("skills.json")["skills"]


def _validation_error_summary(exc: ValidationError) -> list[dict[str, str]]:
    """Safe-to-log diagnostics for a Pydantic ValidationError (Milestone
    12C-8E, requirement 4): only `loc` (the schema field path — literal
    field names and list indices baked into our own Pydantic models,
    never derived from the actual CV content) and `type` (a short, fixed
    Pydantic error-type tag, e.g. "missing"/"string_type"/"string_too_long")
    are ever extracted. Deliberately never includes `msg`, `input`, or
    `ctx` from exc.errors() — any of those can embed the actual invalid
    value, which may be raw CV text, an evidence quote, or other
    student-entered content."""
    return [
        {"loc": ".".join(str(part) for part in err["loc"]), "type": err["type"]}
        for err in exc.errors()
    ]


def _coerce_skill_entry(item: object) -> GlmSkillEntry | None:
    """Best-effort recovery of one raw GLM skill entry (requirement 5/7).
    Returns None only when there is no usable skill name at all — the
    caller drops such an entry, logging just the safe summary above.

    - A bare string (a real-world GLM deployment's legacy format, before
      evidence was required per-skill) is treated as a name with no
      evidence — never inventing a quote that was never actually given;
      it then goes through the ordinary "missing evidence" review path
      downstream (_validate_and_map_skills), exactly like a well-formed
      {"name": ..., "evidence": null} entry would.
    - A dict whose "name" is usable but whose "evidence" doesn't fit the
      schema (wrong type, or too long even after Milestone 12C-8E's
      widened bound) keeps the name and drops just the evidence — never
      substitutes an invented replacement quote. That skill then also
      goes through the ordinary "missing evidence" path.
    - Anything else (no usable name at all) is unrecoverable: returns
      None, and the one bad entry is dropped without affecting any other
      skill or any other field in the response.
    """
    if isinstance(item, str):
        item = {"name": item, "evidence": None}
    if not isinstance(item, dict):
        return None

    try:
        return GlmSkillEntry.model_validate(item)
    except ValidationError:
        pass

    name = item.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    try:
        return GlmSkillEntry.model_validate({"name": name, "evidence": None})
    except ValidationError:
        return None


def _clean_skills_field(raw_value: object) -> list[dict]:
    if raw_value is None:
        return []
    if not isinstance(raw_value, list):
        logger.warning(
            "GLM field 'skills' was not a list (got %s); treated as empty "
            "rather than guessed.",
            type(raw_value).__name__,
        )
        return []

    cleaned: list[dict] = []
    for index, raw_item in enumerate(raw_value):
        coerced = _coerce_skill_entry(raw_item)
        if coerced is None:
            logger.info(
                "Dropping an unrecoverable GLM skill entry at index %d "
                "(no usable name); the rest of the extraction is kept.",
                index,
            )
            continue
        cleaned.append(coerced.model_dump())
    return cleaned


def _clean_list_field(raw_value: object, field_name: str, model_cls: type[BaseModel]) -> list[dict]:
    """Normalize+validate one top-level list field item-by-item so a
    single malformed entry never invalidates the whole extraction
    (requirement 7). `None` or any other non-list value normalizes to an
    empty list (requirement 5) rather than failing. Each surviving item
    is returned as its already-validated .model_dump() dict, so the
    later, single GlmCvExtraction.model_validate() call is just
    re-validating already-good data."""
    if raw_value is None:
        return []
    if not isinstance(raw_value, list):
        logger.warning(
            "GLM field %r was not a list (got %s); treated as empty "
            "rather than guessed.",
            field_name, type(raw_value).__name__,
        )
        return []

    cleaned: list[dict] = []
    for index, item in enumerate(raw_value):
        try:
            validated = model_cls.model_validate(item)
        except ValidationError as exc:
            logger.info(
                "Dropping a malformed GLM %s entry at index %d (the rest "
                "of the extraction is kept): %s",
                field_name, index, _validation_error_summary(exc),
            )
            continue
        cleaned.append(validated.model_dump())
    return cleaned


def _clean_glm_json(raw_json: dict) -> dict:
    """Pre-processes GLM's raw JSON so a single malformed list entry (a
    null list, a legacy-format skill string, an oversized/mistyped
    field) never fails the whole GlmCvExtraction.model_validate() call
    below (Milestone 12C-8E). An invalid top-level name/summary is set
    to None (never replaced with a guessed value); model_validate() is
    still the final, honest fallback-to-manual_review safety net for
    anything else. This function only ever removes or repairs values,
    never invents one GLM didn't actually provide."""
    cleaned = dict(raw_json)
    for field_name in ("name", "summary"):
        # An invalid top-level scalar (wrong type, oversized) becomes None
        # instead of failing the whole extraction below.
        if cleaned.get(field_name) is not None:
            try:
                GlmCvExtraction.model_validate({field_name: cleaned[field_name]})
            except ValidationError as exc:
                logger.info(
                    "Dropping an invalid GLM %r value (the rest of the extraction is kept): %s",
                    field_name, _validation_error_summary(exc),
                )
                cleaned[field_name] = None
    if "skills" in cleaned:
        cleaned["skills"] = _clean_skills_field(cleaned["skills"])
    for field_name, model_cls in _LIST_FIELD_MODELS.items():
        if field_name in cleaned:
            cleaned[field_name] = _clean_list_field(cleaned[field_name], field_name, model_cls)
    return cleaned


def _is_effectively_empty(extraction: GlmCvExtraction) -> bool:
    """True if GLM's (cleaned, validated) output contains literally
    nothing usable — every field blank. Distinguishing this from a
    genuine partial extraction matters: a response that's effectively
    empty gets the SAME manual_review treatment (with its CV-text
    preview) as a schema failure, rather than a falsely-reassuring "ok"
    status with a blank draft and no text for the student to fall back
    on."""
    return not any(
        [
            extraction.name,
            extraction.summary,
            extraction.education,
            extraction.skills,
            extraction.projects,
            extraction.experience,
            extraction.certifications,
        ]
    )


def _normalize_whitespace(text: str) -> str:
    """Collapse all whitespace runs (spaces, tabs, newlines — including
    the kind PDF text extraction commonly introduces between words/
    lines) to single spaces, for a tolerant-but-not-loose comparison."""
    return re.sub(r"\s+", " ", text).strip()


def _evidence_is_supported(evidence: str | None, cv_text: str) -> bool:
    """True only if `evidence` appears word-for-word (modulo whitespace
    and case) in the locally-extracted CV text, as whole words — "git"
    inside "Digital" or "Java" inside "JavaScript" does not count (the
    same word-boundary rule as SkillNormalizer.find_in_text). Never a
    fuzzy/semantic match — an unrelated or hallucinated quote must fail
    this check (requirement 4)."""
    if not evidence:
        return False
    normalized_evidence = _normalize_whitespace(evidence).lower()
    if len(normalized_evidence) < MIN_EVIDENCE_CHARS:
        return False
    normalized_text = _normalize_whitespace(cv_text).lower()
    pattern = r"(?<![a-z0-9])" + re.escape(normalized_evidence) + r"(?![a-z0-9])"
    return re.search(pattern, normalized_text) is not None


def _contained_skill(normalizer: SkillNormalizer, name: str) -> str | None:
    """skill_id when `name` contains exactly one catalogue skill name or
    alias as a whole phrase, via SkillNormalizer.read_profile_skills with
    no interpreter (so only its deterministic "contains" rule applies)."""
    reading = normalizer.read_profile_skills([{"name": name}])
    interpretations = [i for i in reading.interpreted.values() if i.contains is not None]
    return interpretations[0].skill_id if len(interpretations) == 1 else None


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
        skill_id, skill_name, needs_confirmation = result.skill_id, result.name, False
        if not skill_id:
            # The matcher's own rule, no embeddings: a name containing exactly
            # one catalogue skill phrase ("Python (pandas)") maps to it.
            contained = _contained_skill(normalizer, name)
            if contained is not None:
                skill_id, skill_name, needs_confirmation = contained, normalizer.name_of(contained), True
        if skill_id and skill_id not in seen_ids:
            mapped.append(
                CvMappedSkill(
                    skill_id=skill_id, name=skill_name, raw_text=name, evidence=evidence,
                    needs_confirmation=needs_confirmation,
                )
            )
            seen_ids.add(skill_id)
        elif not skill_id:
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
    (NO_TEXT_WARNING/CV_UNAVAILABLE_WARNING) separately in CvParseData's
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

    llm = _llm_call_config(settings)
    if llm is None:
        return (
            CvParseData(
                status="manual_review",
                draft=_empty_draft(),
                page_count=pdf_result.page_count,
                extracted_text_preview=pdf_result.text[:500],
            ),
            [CV_UNAVAILABLE_WARNING],
        )
    try:
        result = extract_cv_fields(
            pdf_result.text,
            api_key=llm.api_key,
            base_url=llm.base_url,
            model=llm.model,
            timeout=llm.timeout,
            provider=llm.provider,
            key_name=llm.key_name,
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
            [CV_UNAVAILABLE_WARNING],
        )

    try:
        extraction = GlmCvExtraction.model_validate(_clean_glm_json(result.raw_json))
    except ValidationError as exc:
        logger.warning(
            "GLM output failed schema validation; falling back to manual review: %s",
            _validation_error_summary(exc),
        )
        return (
            CvParseData(
                status="manual_review",
                draft=_empty_draft(),
                page_count=pdf_result.page_count,
                extracted_text_preview=pdf_result.text[:500],
            ),
            [CV_UNAVAILABLE_WARNING],
        )
    except Exception:
        logger.warning("GLM output could not be interpreted; falling back to manual review")
        return (
            CvParseData(
                status="manual_review",
                draft=_empty_draft(),
                page_count=pdf_result.page_count,
                extracted_text_preview=pdf_result.text[:500],
            ),
            [CV_UNAVAILABLE_WARNING],
        )

    if _is_effectively_empty(extraction):
        logger.warning(
            "GLM output had no usable fields after cleaning/validation; falling back to manual review"
        )
        return (
            CvParseData(
                status="manual_review",
                draft=_empty_draft(),
                page_count=pdf_result.page_count,
                extracted_text_preview=pdf_result.text[:500],
            ),
            [CV_UNAVAILABLE_WARNING],
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
    for skill in mapped_skills:
        if skill.needs_confirmation:
            warnings.append(
                f'"{skill.raw_text}" from your CV was matched to {skill.name}; please confirm it is right.'
            )
    if skills_requiring_review:
        warnings.append(
            f"{len(skills_requiring_review)} skill(s) could not be automatically verified against "
            "your CV text and were not added to your profile automatically; add them yourself if "
            "they're accurate."
        )
    return CvParseData(status="ok", draft=draft, page_count=pdf_result.page_count, extracted_text_preview=None), warnings
