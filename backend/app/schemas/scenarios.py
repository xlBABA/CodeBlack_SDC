"""Pydantic v2 DTOs for POST /scenarios/simulate.

contracts/API_CONTRACT.md: request = ScenarioRequest{profile,scenario_id};
response data = "same matches" + {scenario_id, assumptions,
uncertainty_note}. openapi.yaml types the response as a permissive
GenericEnvelope — this module is the first strict typing of that
documented shape. No fields beyond what's written there.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.matching import RoleMatch, ScenarioId
from app.schemas.profile import DataMode, StudentProfile


class ScenarioRequest(BaseModel):
    profile: StudentProfile
    scenario_id: ScenarioId


class ScenarioPayload(BaseModel):
    matches: list[RoleMatch]
    scenario_id: ScenarioId
    assumptions: list[str]
    uncertainty_note: str


class ScenarioResponse(BaseModel):
    data: ScenarioPayload
    data_mode: DataMode
    generated_at: str
    warnings: list[str] = Field(default_factory=list)
