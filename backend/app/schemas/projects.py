"""Pydantic v2 DTOs for POST /projects/recommend and POST /projects/simulate.

RoleProfileRequest (recommend) is imported from app.schemas.roadmaps —
the same shared schema the contract reuses across both routes.
openapi.yaml types both routes' responses as a permissive GenericEnvelope;
API_CONTRACT.md documents the actual shapes — this module is the first
strict typing of those, additive only.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.profile import DataMode, StudentProfile


class RecommendedProject(BaseModel):
    project_id: str
    title: str
    skill_ids: list[str]
    estimated_hours: float = Field(ge=0)
    source_ids: list[str]
    milestones: list[str]


class ProjectRecommendationPayload(BaseModel):
    projects: list[RecommendedProject]


class ProjectRecommendationResponse(BaseModel):
    data: ProjectRecommendationPayload
    data_mode: DataMode
    generated_at: str
    warnings: list[str] = Field(default_factory=list)


class ProjectSimulationRequest(BaseModel):
    profile: StudentProfile
    role_id: str
    project_id: str


class ProjectSimulationPayload(BaseModel):
    baseline_score: float = Field(ge=0, le=100)
    simulated_score: float = Field(ge=0, le=100)
    assumed_skill_ids: list[str]
    disclaimer: str


class ProjectSimulationResponse(BaseModel):
    data: ProjectSimulationPayload
    data_mode: DataMode
    generated_at: str
    warnings: list[str] = Field(default_factory=list)
