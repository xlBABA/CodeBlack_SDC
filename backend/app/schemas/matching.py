"""Pydantic v2 DTOs mirroring contracts/openapi.yaml: MatchRequest, RoleMatch,
MatchPayload, MatchResponse. No hiring-probability or eligibility fields —
score_type is pinned to the contract's single allowed value.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.profile import DataMode, SkillRef, StudentProfile

ScenarioId = Literal["moderate", "fast"]
ScoreType = Literal["profile_alignment_estimate"]


class MatchRequest(BaseModel):
    profile: StudentProfile
    limit: int = Field(default=6, ge=1, le=6)
    scenario_id: ScenarioId | None = None


class ScoreBreakdown(BaseModel):
    skills: float = Field(ge=0, le=100)
    experience: float = Field(ge=0, le=100)
    prerequisites: float = Field(ge=0, le=100)
    transferable: float = Field(ge=0, le=100)


class RoleMatch(BaseModel):
    role_id: str
    role_title: str
    score: float = Field(ge=0, le=100)
    score_type: ScoreType = "profile_alignment_estimate"
    matched_skills: list[SkillRef] = Field(default_factory=list)
    missing_skills: list[SkillRef] = Field(default_factory=list)
    score_breakdown: ScoreBreakdown
    evidence_ids: list[str] = Field(default_factory=list)
    explanation: str
    caveats: list[str] = Field(default_factory=list)


class CatalogCoverage(BaseModel):
    verified: int = Field(ge=0)
    total_target: int = Field(ge=0)


class MatchPayload(BaseModel):
    matches: list[RoleMatch]
    catalog_coverage: CatalogCoverage
    methodology_version: str


class MatchResponse(BaseModel):
    """Envelope per contracts/openapi.yaml#/components/schemas/MatchResponse."""

    data: MatchPayload
    data_mode: DataMode
    generated_at: str
    warnings: list[str] = Field(default_factory=list)
