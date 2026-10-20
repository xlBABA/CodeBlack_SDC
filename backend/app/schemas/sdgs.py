"""Pydantic v2 DTOs for GET /sdgs/{role_id}.

openapi.yaml types the response as a permissive GenericEnvelope;
API_CONTRACT.md documents the shape as {role_sdg_mappings:[{sdg_id,reason}],
skill_sdg_mappings:[{skill_id,sdg_id,reason}]}. sdg_id is constrained to
1-17 per IMPLEMENTATION_PLAN.md ("include SDG ID(s) among 1-17").
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.profile import DataMode


class RoleSdgMapping(BaseModel):
    sdg_id: int = Field(ge=1, le=17)
    reason: str


class SkillSdgMapping(BaseModel):
    skill_id: str
    sdg_id: int = Field(ge=1, le=17)
    reason: str


class SdgPayload(BaseModel):
    role_sdg_mappings: list[RoleSdgMapping]
    skill_sdg_mappings: list[SkillSdgMapping]


class SdgResponse(BaseModel):
    data: SdgPayload
    data_mode: DataMode
    generated_at: str
    warnings: list[str] = Field(default_factory=list)
