"""SDG mapping catalog — placeholder fixture pending Jawad's verified
SDG-mapping dataset (data/sdg_mappings.json). Mappings here are
illustrative demonstration rationale only: not a United Nations
endorsement or official certification of any role or skill. Covers only
the 4 existing fixture roles — not an attempt at the full 30-role catalog.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RoleSdgFixture:
    sdg_id: int
    reason: str


@dataclass(frozen=True)
class SkillSdgFixture:
    skill_id: str
    sdg_id: int
    reason: str


@dataclass(frozen=True)
class RoleSdgMappingSet:
    role_id: str
    role_sdg: tuple[RoleSdgFixture, ...]
    skill_sdg: tuple[SkillSdgFixture, ...]


class SdgCatalogProvider(Protocol):
    def get(self, role_id: str) -> RoleSdgMappingSet | None:
        """Look up the placeholder SDG mapping set for a role_id."""
        ...


_MAPPINGS: tuple[RoleSdgMappingSet, ...] = (
    RoleSdgMappingSet(
        role_id="data_analyst",
        role_sdg=(
            RoleSdgFixture(
                sdg_id=9,
                reason=(
                    "Illustrative demonstration mapping: data analysis skills "
                    "generally support resilient infrastructure and innovation "
                    "capacity (SDG 9); a general skill-to-goal association, "
                    "not a certified or externally sourced claim."
                ),
            ),
        ),
        skill_sdg=(
            SkillSdgFixture(
                skill_id="data_visualization",
                sdg_id=4,
                reason=(
                    "Illustrative demonstration mapping: clear data "
                    "visualization supports public understanding and quality "
                    "education (SDG 4); a general association only."
                ),
            ),
        ),
    ),
    RoleSdgMappingSet(
        role_id="financial_analyst",
        role_sdg=(
            RoleSdgFixture(
                sdg_id=8,
                reason=(
                    "Illustrative demonstration mapping: financial analysis "
                    "skills generally support decent work and economic growth "
                    "(SDG 8); a general association, not a sourced claim."
                ),
            ),
        ),
        skill_sdg=(
            SkillSdgFixture(
                skill_id="financial_modeling",
                sdg_id=8,
                reason=(
                    "Illustrative demonstration mapping: financial modeling "
                    "supports sound economic decision-making (SDG 8); a "
                    "general association only."
                ),
            ),
        ),
    ),
    RoleSdgMappingSet(
        role_id="mechanical_design_engineer",
        role_sdg=(
            RoleSdgFixture(
                sdg_id=9,
                reason=(
                    "Illustrative demonstration mapping: mechanical design "
                    "generally supports industry and infrastructure innovation "
                    "(SDG 9); a general association, not a sourced claim."
                ),
            ),
        ),
        skill_sdg=(
            SkillSdgFixture(
                skill_id="cad",
                sdg_id=9,
                reason=(
                    "Illustrative demonstration mapping: CAD skills support "
                    "designing and building infrastructure (SDG 9); a general "
                    "association only."
                ),
            ),
        ),
    ),
    RoleSdgMappingSet(
        role_id="sustainability_coordinator",
        role_sdg=(
            RoleSdgFixture(
                sdg_id=13,
                reason=(
                    "Illustrative demonstration mapping: sustainability "
                    "coordination generally supports climate action (SDG 13); "
                    "a general association, not a sourced claim."
                ),
            ),
        ),
        skill_sdg=(
            SkillSdgFixture(
                skill_id="sustainability_reporting",
                sdg_id=12,
                reason=(
                    "Illustrative demonstration mapping: sustainability "
                    "reporting supports responsible consumption and "
                    "production (SDG 12); a general association only."
                ),
            ),
        ),
    ),
)


class FixtureSdgCatalog:
    """Deterministic, in-memory stand-in for Jawad's real SDG mapping dataset."""

    def get(self, role_id: str) -> RoleSdgMappingSet | None:
        return next((m for m in _MAPPINGS if m.role_id == role_id), None)
