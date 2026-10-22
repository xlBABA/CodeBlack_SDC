"""Milestone 6D-2A: loading and validation only for Jawad's cached
projects.json (app/data/cached/projects.json). Nothing here wires a
CachedProjectCatalog into ProjectCatalogProvider, any route, or
FixtureProjectCatalog — see project_catalog_cached.py's docstring."""
import pytest

from app.services.project_catalog_cached import _validate_projects, load_cached_projects
from app.services.role_catalog_cached import CachedCatalogError

EXPECTED_PROJECT_COUNT = 9
JAWAD_ROLE_IDS = {"data_analyst", "financial_analyst", "mechanical_engineer", "public_health_analyst"}
CANONICAL_SKILL_IDS = {
    "critical_thinking", "mathematics", "complex_problem_solving", "systems_analysis",
    "attention_to_detail", "excel", "sql", "python", "data_visualization", "cad_software",
    "matlab", "financial_analysis_software", "analytical_scientific_software", "vba",
}


def test_loads_exactly_the_expected_project_count():
    assert len(load_cached_projects()) == EXPECTED_PROJECT_COUNT


def test_project_ids_are_unique():
    ids = [p["project_id"] for p in load_cached_projects()]
    assert len(ids) == len(set(ids))


def test_every_project_role_id_is_jawads_canonical_role_id():
    for project in load_cached_projects():
        assert project["role_id"] in JAWAD_ROLE_IDS, project["project_id"]


def test_every_project_skill_id_is_canonical():
    for project in load_cached_projects():
        for skill_id in project["skill_ids"]:
            assert skill_id in CANONICAL_SKILL_IDS, project["project_id"]


def test_every_project_has_source_ids_and_milestones():
    for project in load_cached_projects():
        assert project["source_ids"], project["project_id"]
        assert project["milestones"], project["project_id"]


def test_every_project_role_id_has_at_least_one_project():
    role_ids_with_projects = {p["role_id"] for p in load_cached_projects()}
    assert role_ids_with_projects == JAWAD_ROLE_IDS


def test_estimated_hours_are_non_negative_numbers():
    for project in load_cached_projects():
        assert isinstance(project["estimated_hours"], (int, float))
        assert project["estimated_hours"] >= 0


# --- Malformed input is rejected, not guessed around ----------------------

_BASE_PROJECT = {
    "project_id": "p1", "role_id": "data_analyst", "title": "T", "skill_ids": ["sql"],
    "difficulty": "beginner", "expected_outcome": "o", "milestones": ["m1"],
    "estimated_hours": 5.0, "hours_basis": "team_estimate", "hours_basis_note": "n",
    "source_ids": ["s1"], "source_type": "dataset", "checked_at": "2026-10-22",
}


def test_rejects_duplicate_project_id():
    with pytest.raises(CachedCatalogError, match="Duplicate project_id"):
        _validate_projects([_BASE_PROJECT, dict(_BASE_PROJECT)], {"data_analyst"}, {"sql"})


def test_rejects_unknown_role_id():
    bad = {**_BASE_PROJECT, "role_id": "not_a_real_role"}
    with pytest.raises(CachedCatalogError, match="unknown role_id"):
        _validate_projects([bad], {"data_analyst"}, {"sql"})


def test_rejects_unknown_skill_id():
    bad = {**_BASE_PROJECT, "skill_ids": ["not_a_real_skill"]}
    with pytest.raises(CachedCatalogError, match="unknown skill_id"):
        _validate_projects([bad], {"data_analyst"}, {"sql"})


def test_rejects_missing_required_field():
    bad = dict(_BASE_PROJECT)
    del bad["source_ids"]
    with pytest.raises(CachedCatalogError, match="missing fields"):
        _validate_projects([bad], {"data_analyst"}, {"sql"})


def test_rejects_unsupported_field():
    bad = {**_BASE_PROJECT, "made_up_field": "x"}
    with pytest.raises(CachedCatalogError, match="unsupported fields"):
        _validate_projects([bad], {"data_analyst"}, {"sql"})


def test_rejects_empty_source_ids():
    bad = {**_BASE_PROJECT, "source_ids": []}
    with pytest.raises(CachedCatalogError, match="no source_ids"):
        _validate_projects([bad], {"data_analyst"}, {"sql"})


def test_rejects_empty_milestones():
    bad = {**_BASE_PROJECT, "milestones": []}
    with pytest.raises(CachedCatalogError, match="no milestones"):
        _validate_projects([bad], {"data_analyst"}, {"sql"})


@pytest.mark.parametrize("hours", [-1, "five", True])
def test_rejects_malformed_estimated_hours(hours):
    bad = {**_BASE_PROJECT, "estimated_hours": hours}
    with pytest.raises(CachedCatalogError, match="estimated_hours"):
        _validate_projects([bad], {"data_analyst"}, {"sql"})


def test_valid_data_still_loads_unchanged_after_validation_hardening():
    assert len(load_cached_projects()) == EXPECTED_PROJECT_COUNT
