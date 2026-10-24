"""Role catalog — placeholder fixture pending Jawad's verified 30-role dataset
(services/catalog/**, data/roles.json). Not authoritative; exists only so
/careers/match is independently testable before that real catalog lands.

CLAUDE.md: "Start with 4 verified roles..." and "20 base roles: 5 Technology
& AI, 5 Business & Finance, 5 Engineering & Manufacturing, 5 Healthcare &
Sustainability." This supplies exactly one illustrative role per category —
the smallest set needed to exercise matching end-to-end. `data_analyst`
reuses the role_id/skills already shown in contracts/API_CONTRACT.md's own
sample response rather than inventing a new example. evidence_ids are
fixture-only placeholders, never claimed as real pre-registered sources.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RoleRequirement:
    skill_id: str
    name: str
    weight: float = 1.0
    # Preserves the source data's required/optional distinction (e.g.
    # Jawad's roles.json required_skills[].required). Defaults to True so
    # the 4 existing fixture roles above are unaffected. Metadata only:
    # app.services.matching_provider._skills_score does not read this field
    # yet, so an optional skill a student lacks is still listed in
    # missing_skills exactly like a required one until matching
    # integration is updated to treat them differently.
    required: bool = True


@dataclass(frozen=True)
class RoleFixture:
    role_id: str
    role_title: str
    category: str
    # int for the 4 original fixture roles; None means "no semester
    # prerequisite in the source data" (e.g. Jawad's cached O*NET-derived
    # roles, which carry an empty prerequisites list) — never invented.
    # app.services.matching_provider._prerequisites_score currently assumes
    # a concrete int and will raise on None; a cached-catalog role must not
    # be passed to FixtureMatchingProvider until that is resolved.
    min_semester: int | None
    required_skills: tuple[RoleRequirement, ...]
    transferable_interests: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    verified: bool = True
    # Milestone 13C-7: Hussain's matcher reads this ("limited") to caveat
    # a role whose real-world tools aren't all in our 20-skill catalogue
    # yet — see app.services.hussain_matching.matcher.LIMITED_COVERAGE_CAVEAT.
    # Defaults to None so every existing RoleFixture construction (the 4
    # fixture roles here, and any other caller) is unaffected.
    skills_coverage: str | None = None


class RoleCatalogProvider(Protocol):
    def list_roles(self) -> list[RoleFixture]:
        """Return the currently verified roles to match against."""
        ...


_FIXTURE_ROLES: tuple[RoleFixture, ...] = (
    RoleFixture(
        role_id="data_analyst",
        role_title="Data Analyst",
        category="Technology & AI",
        min_semester=3,
        required_skills=(
            RoleRequirement("sql", "SQL", weight=1.0),
            RoleRequirement("python", "Python", weight=1.0),
            RoleRequirement("data_visualization", "Data Visualization", weight=0.8),
            RoleRequirement("statistics", "Statistics", weight=0.6),
        ),
        transferable_interests=("analytics", "data"),
        evidence_ids=("source_role_data_analyst_001",),
    ),
    RoleFixture(
        role_id="financial_analyst",
        role_title="Financial Analyst",
        category="Business & Finance",
        min_semester=4,
        required_skills=(
            RoleRequirement("excel", "Excel", weight=1.0),
            RoleRequirement("accounting", "Accounting", weight=0.8),
            RoleRequirement("financial_modeling", "Financial Modeling", weight=0.8),
        ),
        transferable_interests=("finance", "fintech"),
        evidence_ids=("source_role_financial_analyst_001",),
    ),
    RoleFixture(
        role_id="mechanical_design_engineer",
        role_title="Mechanical Design Engineer",
        category="Engineering & Manufacturing",
        min_semester=5,
        required_skills=(
            RoleRequirement("cad", "CAD", weight=1.0),
            RoleRequirement("mechanics", "Mechanics", weight=0.8),
            RoleRequirement("matlab", "MATLAB", weight=0.5),
        ),
        transferable_interests=("robotics", "manufacturing"),
        evidence_ids=("source_role_mechanical_design_engineer_001",),
    ),
    RoleFixture(
        role_id="sustainability_coordinator",
        role_title="Sustainability Coordinator",
        category="Healthcare & Sustainability",
        min_semester=2,
        required_skills=(
            RoleRequirement("sustainability_reporting", "Sustainability Reporting", weight=1.0),
            RoleRequirement("stakeholder_communication", "Stakeholder Communication", weight=0.7),
            RoleRequirement("project_management", "Project Management", weight=0.6),
        ),
        transferable_interests=("sustainability", "renewable energy"),
        evidence_ids=("source_role_sustainability_coordinator_001",),
    ),
)


class FixtureRoleCatalog:
    """Deterministic, in-memory stand-in for Jawad's real role catalog."""

    def list_roles(self) -> list[RoleFixture]:
        return [role for role in _FIXTURE_ROLES if role.verified]
