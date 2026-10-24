"""Pydantic v2 DTOs mirroring contracts/openapi.yaml: SkillRef, StudentProfile, ProfileResponse.

StudentProfile is used verbatim as both the POST /profile/analyze request body
and the `data` payload of ProfileResponse — the contract defines one shape for
both directions. Field constraints beyond the contract (max_length caps) are
additive-only: they reject nothing the sample contract payloads rely on.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Proficiency = Literal["beginner", "intermediate", "advanced"]
DataMode = Literal["live", "cached", "fixture"]


class SkillRef(BaseModel):
    skill_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    proficiency: Proficiency | None = None


class StudentProfile(BaseModel):
    profile_id: str | None = Field(default=None, max_length=100)
    education_level: str | None = Field(default=None, max_length=100)
    degree: str | None = Field(default=None, max_length=200)
    semester: int | None = Field(default=None, ge=1)
    target_role_id: str | None = Field(default=None, max_length=100)
    interests: list[str] = Field(max_length=50)
    skills: list[SkillRef] = Field(max_length=50)
    projects: list[str] = Field(max_length=50)
    experience_summary: str | None = Field(default=None, max_length=2000)

    @field_validator("interests", "projects")
    @classmethod
    def _no_blank_entries(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("list items must not be blank")
        return cleaned


class ProfileResponse(BaseModel):
    """Envelope per contracts/openapi.yaml#/components/schemas/ProfileResponse."""

    data: StudentProfile
    data_mode: DataMode
    generated_at: str
    warnings: list[str] = Field(default_factory=list)
