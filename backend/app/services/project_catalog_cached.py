"""Cached portfolio-project dataset — Jawad's verified projects.json
(app/data/cached/projects.json; byte-identical copy of
feat/jawad-trends-data:data/projects.json as of commit 2838340).

Milestone 6D-2A added import and validation (load_cached_projects()).
Milestone 6D-2C adds CachedProjectCatalog, satisfying
app.services.project_catalog.ProjectCatalogProvider — still not wired
into any route or DI, and never mixes in anything from
FixtureProjectCatalog (see CachedProjectCatalog's own docstring).

Known gap, preserved rather than reconciled: every project's role_id
uses Jawad's own canonical set (data_analyst, financial_analyst,
mechanical_engineer, public_health_analyst) — 2 of our 4 fixture
role_ids (mechanical_design_engineer, sustainability_coordinator) have
no project here, and never will under this role_id vocabulary. Not
fixed here; that is a cross-cutting role-ID decision, not a data
validation concern.
"""
from __future__ import annotations

from app.schemas.profile import SkillRef
from app.services.project_catalog import ProjectFixture
from app.services.role_catalog_cached import CachedCatalogError, _load_json, _require_dict, load_cached_roles

_REQUIRED_PROJECT_FIELDS = {
    "project_id", "role_id", "title", "skill_ids", "difficulty", "expected_outcome",
    "milestones", "estimated_hours", "hours_basis", "hours_basis_note", "source_ids",
    "source_type", "checked_at",
}
_ALLOWED_PROJECT_METADATA_FIELDS = {"data_note"}


def _canonical_skill_ids() -> set[str]:
    skills_doc = _load_json("skills.json")
    return {s["skill_id"] for s in skills_doc["skills"]}


def _canonical_role_ids() -> set[str]:
    # Jawad's own canonical role_ids (already fully validated by
    # load_cached_roles(), which never falls back to fixture on failure).
    return {role.role_id for role in load_cached_roles()}


def _validate_projects(projects: list, role_ids: set[str], skill_ids: set[str]) -> None:
    dict_projects = [_require_dict(p, f"projects[{i}]") for i, p in enumerate(projects)]

    seen_ids = [p["project_id"] for p in dict_projects if "project_id" in p]
    if len(set(seen_ids)) != len(seen_ids):
        raise CachedCatalogError("Duplicate project_id in cached projects.json")

    for project in dict_projects:
        missing = _REQUIRED_PROJECT_FIELDS - project.keys()
        if missing:
            raise CachedCatalogError(f"{project.get('project_id')}: missing fields {missing}")
        unsupported = project.keys() - _REQUIRED_PROJECT_FIELDS - _ALLOWED_PROJECT_METADATA_FIELDS
        if unsupported:
            raise CachedCatalogError(f"{project['project_id']}: unsupported fields {unsupported}")

        if project["role_id"] not in role_ids:
            raise CachedCatalogError(
                f"{project['project_id']}: unknown role_id '{project['role_id']}' not present in cached roles.json"
            )
        if not project.get("skill_ids"):
            raise CachedCatalogError(f"{project['project_id']}: no skill_ids")
        for skill_id in project["skill_ids"]:
            if skill_id not in skill_ids:
                raise CachedCatalogError(f"{project['project_id']}: unknown skill_id '{skill_id}'")

        if not project.get("source_ids"):
            raise CachedCatalogError(f"{project['project_id']}: no source_ids (unverifiable provenance)")
        if not project.get("milestones"):
            raise CachedCatalogError(f"{project['project_id']}: no milestones")

        estimated_hours = project["estimated_hours"]
        if (
            not isinstance(estimated_hours, (int, float))
            or isinstance(estimated_hours, bool)
            or estimated_hours < 0
        ):
            raise CachedCatalogError(
                f"{project['project_id']}: estimated_hours must be a non-negative number, got {estimated_hours!r}"
            )
        if not isinstance(project.get("hours_basis_note"), str) or not project["hours_basis_note"].strip():
            raise CachedCatalogError(f"{project['project_id']}: hours_basis_note must be a non-empty string")


def load_cached_projects() -> list[dict]:
    """Load, validate and return app/data/cached/projects.json's project
    records as plain dicts. Raises CachedCatalogError on any integrity
    problem rather than silently dropping or guessing."""
    doc = _load_json("projects.json")
    if doc.get("data_mode") != "cached":
        raise CachedCatalogError(
            f"cached projects.json data_mode must be 'cached', got {doc.get('data_mode')!r} "
            "(must never be labelled 'live')"
        )
    role_ids = _canonical_role_ids()
    skill_ids = _canonical_skill_ids()
    projects = doc.get("projects") or []
    _validate_projects(projects, role_ids, skill_ids)
    return projects


def _skill_names() -> dict[str, str]:
    skills_doc = _load_json("skills.json")
    return {s["skill_id"]: s["name"] for s in skills_doc["skills"]}


def _to_project_fixture(project: dict, skill_names: dict[str, str]) -> ProjectFixture:
    skills = []
    for skill_id in project["skill_ids"]:
        if skill_id not in skill_names:
            # load_cached_projects() already validated every skill_id
            # against cached skills.json — this is a defensive guard
            # against that invariant breaking, never a place to invent
            # a name for an unknown skill.
            raise CachedCatalogError(
                f"{project['project_id']}: unknown skill_id '{skill_id}' has no resolvable name"
            )
        skills.append(SkillRef(skill_id=skill_id, name=skill_names[skill_id]))
    return ProjectFixture(
        project_id=project["project_id"],
        title=project["title"],
        role_id=project["role_id"],
        skills=tuple(skills),
        estimated_hours=float(project["estimated_hours"]),
        source_ids=tuple(project["source_ids"]),
        milestones=tuple(project["milestones"]),
        difficulty=project.get("difficulty"),
        expected_outcome=project.get("expected_outcome"),
        hours_basis=project.get("hours_basis"),
        hours_basis_note=project.get("hours_basis_note"),
        source_type=project.get("source_type"),
        checked_at=project.get("checked_at"),
    )


class CachedProjectCatalog:
    """Satisfies app.services.project_catalog.ProjectCatalogProvider
    using Jawad's real, cached project dataset exclusively — never mixes
    in anything from FixtureProjectCatalog. Loads and validates on every
    call (same reasoning as CachedRoleCatalog/CachedResourceCatalog).
    Not wired into any route or FastAPI dependency yet (Milestone 6D-2C
    scope: adapter implementation and testing only)."""

    def list_projects(self) -> list[ProjectFixture]:
        skill_names = _skill_names()
        return [_to_project_fixture(p, skill_names) for p in load_cached_projects()]

    def get(self, project_id: str) -> ProjectFixture | None:
        return next((p for p in self.list_projects() if p.project_id == project_id), None)
