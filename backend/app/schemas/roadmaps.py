"""Pydantic v2 DTOs for POST /roadmaps/generate.

RoleProfileRequest is reused verbatim by POST /projects/recommend per
contracts/openapi.yaml's shared schema. openapi.yaml types both routes'
responses as a permissive GenericEnvelope; API_CONTRACT.md documents the
roadmap shape as {steps:[{skill_id,resource_id,estimated_hours,reason}],
total_estimated_hours} — this module is the first strict typing of that,
additive only.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.profile import DataMode, StudentProfile


class RoleProfileRequest(BaseModel):
    profile: StudentProfile
    role_id: str
    budget_limit: float | None = Field(default=None, ge=0)
    hours_per_week: int | None = Field(default=None, ge=1)
    # No schema-level default here (openapi.yaml's shared RoleProfileRequest
    # has none either) — each route resolves its own default in service code.
    limit: int | None = Field(default=None, ge=1, le=10)


class RoadmapStep(BaseModel):
    skill_id: str
    resource_id: str
    estimated_hours: float = Field(ge=0)
    reason: str


class RoadmapPayload(BaseModel):
    steps: list[RoadmapStep]
    total_estimated_hours: float = Field(ge=0)


class RoadmapResponse(BaseModel):
    data: RoadmapPayload
    data_mode: DataMode
    generated_at: str
    warnings: list[str] = Field(default_factory=list)
