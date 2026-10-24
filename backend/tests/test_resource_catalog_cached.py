"""Milestone 6D-2A: loading and validation only for Jawad's cached
resources.json (app/data/cached/resources.json). Nothing here wires a
CachedResourceCatalog into ResourceCatalogProvider, any route, or
FixtureResourceCatalog — see resource_catalog_cached.py's docstring."""
import pytest

from app.services.resource_catalog_cached import (
    _validate_resources,
    load_cached_resources,
    skills_without_resource,
)
from app.services.role_catalog_cached import CachedCatalogError

EXPECTED_RESOURCE_COUNT = 16
CANONICAL_SKILL_IDS = {
    "critical_thinking", "mathematics", "complex_problem_solving", "systems_analysis",
    "attention_to_detail", "excel", "sql", "python", "data_visualization", "cad_software",
    "matlab", "financial_analysis_software", "analytical_scientific_software", "vba",
    "programming", "javascript", "git", "accounting_software", "gis", "science",
}


def test_loads_exactly_the_expected_resource_count():
    resources = load_cached_resources()
    assert len(resources) == EXPECTED_RESOURCE_COUNT


def test_resource_ids_are_unique():
    resources = load_cached_resources()
    ids = [r["resource_id"] for r in resources]
    assert len(ids) == len(set(ids))


def test_every_resource_skill_id_is_canonical():
    for resource in load_cached_resources():
        for skill_id in resource["skill_ids"]:
            assert skill_id in CANONICAL_SKILL_IDS, resource["resource_id"]


def test_every_resource_url_is_a_real_https_url():
    for resource in load_cached_resources():
        assert resource["url"].startswith("https://"), resource["resource_id"]


def test_every_resource_has_a_documented_hours_basis():
    """estimated_hours is either provider-stated (non-null, with
    hours_source text) or null with an explicit team_estimate_hours +
    team_estimate_basis — never an unsourced guess."""
    for resource in load_cached_resources():
        if resource["estimated_hours"] is None:
            assert "team_estimate_hours" in resource, resource["resource_id"]
            assert resource.get("team_estimate_basis", "").startswith("Team estimate:"), resource["resource_id"]
        assert resource["hours_source"].strip(), resource["resource_id"]


def test_skills_without_resource_are_canonical_and_not_contradicted():
    gaps = skills_without_resource()
    assert len(gaps) == 5  # +"science", added alongside the 4-role catalog expansion
    covered = {sid for r in load_cached_resources() for sid in r["skill_ids"]}
    for skill_id in gaps:
        assert skill_id in CANONICAL_SKILL_IDS
        assert skill_id not in covered


def test_resources_and_gaps_together_cover_every_canonical_skill():
    covered = {sid for r in load_cached_resources() for sid in r["skill_ids"]}
    gaps = set(skills_without_resource())
    assert covered | gaps == CANONICAL_SKILL_IDS


# --- Malformed input is rejected, not guessed around ----------------------

_BASE_RESOURCE = {
    "resource_id": "r1", "source_id": "s1", "skill_ids": ["sql"], "title": "T",
    "provider": "P", "url": "https://example.com", "level": "beginner",
    "price": {"status": "free_stated", "note": "n"}, "estimated_hours": 1.0,
    "hours_source": "Provider-stated: 1h.", "prerequisites": {"text": "", "skill_ids": []},
    "checked_at": "2026-10-22", "checked_by": "test",
}


def test_rejects_duplicate_resource_id():
    with pytest.raises(CachedCatalogError, match="Duplicate resource_id"):
        _validate_resources([_BASE_RESOURCE, dict(_BASE_RESOURCE)], {"sql"}, set())


def test_rejects_unknown_skill_id():
    bad = {**_BASE_RESOURCE, "skill_ids": ["not_a_real_skill"]}
    with pytest.raises(CachedCatalogError, match="unknown skill_id"):
        _validate_resources([bad], {"sql"}, set())


def test_rejects_missing_required_field():
    bad = dict(_BASE_RESOURCE)
    del bad["url"]
    with pytest.raises(CachedCatalogError, match="missing fields"):
        _validate_resources([bad], {"sql"}, set())


def test_rejects_unsupported_field():
    bad = {**_BASE_RESOURCE, "made_up_field": "x"}
    with pytest.raises(CachedCatalogError, match="unsupported fields"):
        _validate_resources([bad], {"sql"}, set())


def test_rejects_non_https_url():
    bad = {**_BASE_RESOURCE, "url": "http://example.com"}
    with pytest.raises(CachedCatalogError, match="https"):
        _validate_resources([bad], {"sql"}, set())


@pytest.mark.parametrize("hours", [-1, "five", True])
def test_rejects_malformed_estimated_hours(hours):
    bad = {**_BASE_RESOURCE, "estimated_hours": hours}
    with pytest.raises(CachedCatalogError, match="estimated_hours"):
        _validate_resources([bad], {"sql"}, set())


def test_rejects_null_hours_without_team_estimate():
    bad = {**_BASE_RESOURCE, "estimated_hours": None}
    with pytest.raises(CachedCatalogError, match="team_estimate_hours"):
        _validate_resources([bad], {"sql"}, set())


def test_rejects_unknown_prerequisite_skill_id():
    bad = {**_BASE_RESOURCE, "prerequisites": {"text": "", "skill_ids": ["not_a_real_skill"]}}
    with pytest.raises(CachedCatalogError, match="prerequisite skill_id"):
        _validate_resources([bad], {"sql"}, set())


def test_rejects_skills_without_resource_claiming_an_unknown_skill():
    with pytest.raises(CachedCatalogError, match="unknown skill_id"):
        _validate_resources([_BASE_RESOURCE], {"sql"}, {"not_a_real_skill"})


def test_rejects_skills_without_resource_contradicted_by_a_real_resource():
    with pytest.raises(CachedCatalogError, match="DO have one"):
        _validate_resources([_BASE_RESOURCE], {"sql"}, {"sql"})


def test_valid_data_still_loads_unchanged_after_validation_hardening():
    assert len(load_cached_resources()) == EXPECTED_RESOURCE_COUNT
