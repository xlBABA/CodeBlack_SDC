"""Milestone 11B: POST /api/v1/cv/parse — CV PDF -> GLM-5.3 -> validated
structured draft. New, additive-only; does not touch the frozen
StudentProfile contract (app.schemas.profile) — a draft is returned for
user confirmation, never written to the stored profile directly (see
app/api/v1/endpoints/cv.py's module docstring and requirement 5).

GLM's raw output is untrusted model output: GlmCvExtraction below is the
*only* thing ever constructed directly from it, with `extra="ignore"`
(unknown keys dropped, not rejected, since a model may add commentary
fields) and bounded list lengths (a prompt-injected "list 500 skills"
reply cannot blow up downstream processing). Nothing here invents a
value GLM didn't provide — every field is Optional/defaults to empty.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.profile import StudentProfile

CvParseStatus = Literal["ok", "manual_review", "no_extractable_text"]


class CvEducationEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    institution: str | None = Field(default=None, max_length=300)
    degree: str | None = Field(default=None, max_length=300)
    field_of_study: str | None = Field(default=None, max_length=300)
    start_date: str | None = Field(default=None, max_length=50)
    end_date: str | None = Field(default=None, max_length=50)


class CvExperienceEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role: str | None = Field(default=None, max_length=300)
    organization: str | None = Field(default=None, max_length=300)
    start_date: str | None = Field(default=None, max_length=50)
    end_date: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=1000)


class CvProjectEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str = Field(max_length=300)
    description: str | None = Field(default=None, max_length=1000)


class CvCertificationEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(max_length=300)
    issuer: str | None = Field(default=None, max_length=300)
    year: str | None = Field(default=None, max_length=20)


class GlmCvExtraction(BaseModel):
    """The *only* schema ever built directly from GLM's raw JSON output.
    Treat as untrusted: extra keys are dropped, every field is optional
    or defaults empty, and every list is capped — a model never gets to
    force an unbounded or malformed structure further downstream."""

    model_config = ConfigDict(extra="ignore")

    name: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=2000)
    education: list[CvEducationEntry] = Field(default_factory=list, max_length=20)
    skills: list[str] = Field(default_factory=list, max_length=100)
    projects: list[CvProjectEntry] = Field(default_factory=list, max_length=30)
    experience: list[CvExperienceEntry] = Field(default_factory=list, max_length=30)
    certifications: list[CvCertificationEntry] = Field(default_factory=list, max_length=30)


class CvMappedSkill(BaseModel):
    """A skill GLM extracted that matched Jawad's canonical catalogue
    (via app.services.hussain_matching.normalizer.SkillNormalizer —
    deterministic exact/alias match only, never a guess)."""

    skill_id: str
    name: str
    raw_text: str


class CvUnmappedSkill(BaseModel):
    """A skill GLM extracted with no catalogue match — kept for the
    user's own review, never silently dropped and never assigned an
    invented skill_id (requirement 4)."""

    raw_text: str


class CvDraftProfile(BaseModel):
    """Everything extracted, for Mohammad's editable review UI. Never
    written to the stored profile automatically — see requirement 5."""

    name: str | None = None
    summary: str | None = None
    education: list[CvEducationEntry] = Field(default_factory=list)
    mapped_skills: list[CvMappedSkill] = Field(default_factory=list)
    unmapped_skills: list[CvUnmappedSkill] = Field(default_factory=list)
    projects: list[CvProjectEntry] = Field(default_factory=list)
    experience: list[CvExperienceEntry] = Field(default_factory=list)
    certifications: list[CvCertificationEntry] = Field(default_factory=list)
    # Ready to submit as-is to POST /profile/analyze once the user
    # confirms (requirement 5) — a sensible pre-filled default, not an
    # authoritative result; the UI may edit any field before submitting.
    suggested_profile: StudentProfile


class CvParseData(BaseModel):
    status: CvParseStatus
    draft: CvDraftProfile
    page_count: int
    # Only populated for "manual_review"/"no_extractable_text" (requirement
    # 6: "avoid returning raw sensitive CV text unnecessarily") — a short,
    # bounded preview so the user can self-serve manual entry, never the
    # full document.
    extracted_text_preview: str | None = Field(default=None, max_length=500)


class CvParseResponse(BaseModel):
    """Envelope consistent with every other route's {data, data_mode,
    generated_at, warnings} shape (contracts/API_CONTRACT.md's
    APIEnvelope). data_mode is always "live": this is a synchronous,
    per-request extraction attempt, never fixture or cached data."""

    data: CvParseData
    data_mode: Literal["live"] = "live"
    generated_at: str
    warnings: list[str] = Field(default_factory=list)
