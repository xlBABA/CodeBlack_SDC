"""Pydantic v2 DTOs for GET /trends.

contracts/openapi.yaml types this route's response as a permissive
GenericEnvelope (data: additionalProperties true); contracts/API_CONTRACT.md's
"TrendSignal" section is the actual documented shape
({signals, last_successful_refresh_at?, source_status}). This module is the
first strict typing of that documented shape — additive only, not a
contract change, and no field beyond what API_CONTRACT.md writes out.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_serializer, field_validator

from app.core.time import to_utc_z
from app.schemas.profile import DataMode

Direction = Literal["rising", "stable", "falling", "unknown"]
SourceStatus = Literal["ok", "stale", "unavailable"]


def _require_timezone_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return value


class TrendSignal(BaseModel):
    signal_id: str
    skill_id: str
    source_id: str
    signal_type: str
    metric_name: str
    metric_value: float | None = None
    unit: str | None = None
    observed_at: datetime
    retrieved_at: datetime
    direction: Direction
    confidence_note: str
    role_ids: list[str] = Field(default_factory=list)

    @field_validator("observed_at", "retrieved_at")
    @classmethod
    def _tz_aware(cls, value: datetime) -> datetime:
        return _require_timezone_aware(value)

    @field_serializer("observed_at", "retrieved_at")
    def _serialize_dt(self, value: datetime) -> str:
        return to_utc_z(value)


class TrendsPayload(BaseModel):
    signals: list[TrendSignal] = Field(default_factory=list)
    last_successful_refresh_at: datetime | None = None
    source_status: SourceStatus

    @field_validator("last_successful_refresh_at")
    @classmethod
    def _tz_aware_optional(cls, value: datetime | None) -> datetime | None:
        return value if value is None else _require_timezone_aware(value)

    @field_serializer("last_successful_refresh_at")
    def _serialize_refresh(self, value: datetime | None) -> str | None:
        return None if value is None else to_utc_z(value)


class TrendsResponse(BaseModel):
    """Envelope per contracts/openapi.yaml GenericEnvelope, typed to the shape
    contracts/API_CONTRACT.md documents for GET /trends."""

    data: TrendsPayload
    data_mode: DataMode
    generated_at: str
    warnings: list[str] = Field(default_factory=list)
