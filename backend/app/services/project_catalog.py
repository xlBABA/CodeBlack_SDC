"""Project catalog — placeholder fixture pending Jawad's verified project
dataset (data/projects.json). Every project is explicitly synthetic: no
claim of a real client, employer, completion record or verified impact
measurement. One project per existing fixture role — the smallest set
needed to exercise recommend/simulate end-to-end.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.schemas.profile import SkillRef


@dataclass(frozen=True)
class ProjectFixture:
    project_id: str
    title: str
    role_id: str
    skills: tuple[SkillRef, ...]
    estimated_hours: float
    source_ids: tuple[str, ...]
    milestones: tuple[str, ...]
    # Additive (Milestone 6D-2B/6D-2C): None for every existing fixture
    # project above, unchanged. CachedProjectCatalog (project_catalog_cached.py)
    # populates these from Jawad's real data. RecommendedProject (the
    # frozen public DTO) has no matching fields at all — these are for
    # internal use (e.g. ProjectRecommendationService's warnings), never
    # exposed as their own response field.
    difficulty: str | None = None
    expected_outcome: str | None = None
    hours_basis: str | None = None
    hours_basis_note: str | None = None
    source_type: str | None = None
    checked_at: str | None = None

    @property
    def skill_ids(self) -> tuple[str, ...]:
        return tuple(skill.skill_id for skill in self.skills)


class ProjectCatalogProvider(Protocol):
    def list_projects(self) -> list[ProjectFixture]:
        """Return the currently available placeholder projects."""
        ...

    def get(self, project_id: str) -> ProjectFixture | None:
        """Look up a single placeholder project by id."""
        ...


_PROJECTS: tuple[ProjectFixture, ...] = (
    ProjectFixture(
        project_id="project_data_dashboard_001",
        title="Synthetic sales-data dashboard",
        role_id="data_analyst",
        skills=(
            SkillRef(skill_id="sql", name="SQL"),
            SkillRef(skill_id="python", name="Python"),
            SkillRef(skill_id="data_visualization", name="Data Visualization"),
        ),
        estimated_hours=12.0,
        source_ids=("source_project_data_dashboard_001",),
        milestones=(
            "Define a synthetic dataset and the questions it should answer",
            "Write SQL queries to extract and aggregate the data",
            "Build charts visualizing the results",
            "Write a short summary of findings",
        ),
    ),
    ProjectFixture(
        project_id="project_budget_model_001",
        title="Synthetic department budget model",
        role_id="financial_analyst",
        skills=(
            SkillRef(skill_id="excel", name="Excel"),
            SkillRef(skill_id="financial_modeling", name="Financial Modeling"),
        ),
        estimated_hours=10.0,
        source_ids=("source_project_budget_model_001",),
        milestones=(
            "Define synthetic revenue and cost line items",
            "Build a basic 3-statement spreadsheet model",
            "Run a simple sensitivity scenario",
            "Summarize assumptions and results",
        ),
    ),
    ProjectFixture(
        project_id="project_cad_prototype_001",
        title="Synthetic small-part CAD prototype",
        role_id="mechanical_design_engineer",
        skills=(
            SkillRef(skill_id="cad", name="CAD"),
            SkillRef(skill_id="mechanics", name="Mechanics"),
        ),
        estimated_hours=14.0,
        source_ids=("source_project_cad_prototype_001",),
        milestones=(
            "Sketch a simple synthetic part requirement",
            "Model the part in CAD",
            "Run a basic hand-calculated load check",
            "Document the design rationale",
        ),
    ),
    ProjectFixture(
        project_id="project_sustainability_report_001",
        title="Synthetic sustainability reporting exercise",
        role_id="sustainability_coordinator",
        skills=(
            SkillRef(skill_id="sustainability_reporting", name="Sustainability Reporting"),
            SkillRef(skill_id="project_management", name="Project Management"),
        ),
        estimated_hours=8.0,
        source_ids=("source_project_sustainability_report_001",),
        milestones=(
            "Pick a synthetic organization scenario",
            "Draft a basic sustainability reporting outline",
            "Plan a simple project timeline for implementation",
            "Write a short stakeholder summary",
        ),
    ),
)


class FixtureProjectCatalog:
    """Deterministic, in-memory stand-in for Jawad's real project catalog."""

    def list_projects(self) -> list[ProjectFixture]:
        return list(_PROJECTS)

    def get(self, project_id: str) -> ProjectFixture | None:
        return next((p for p in _PROJECTS if p.project_id == project_id), None)
