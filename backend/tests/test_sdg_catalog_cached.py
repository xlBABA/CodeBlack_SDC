"""Milestone 6D-2A: loading and validation only for Jawad's cached
sdg_mappings.json (app/data/cached/sdg_mappings.json). Nothing here
wires a CachedSdgCatalog into SdgCatalogProvider, GET /sdgs/{role_id},
or FixtureSdgCatalog — see sdg_catalog_cached.py's docstring."""
import pytest

from app.services.role_catalog_cached import CachedCatalogError
from app.services.sdg_catalog_cached import _validate_sdg_mappings, load_cached_sdg_mappings

# Milestone 13C-4: Jawad's catalog expanded from the original 8 verified
# roles to the full 30-role target — the original 8 are unchanged, 22
# new O*NET occupations were added.
JAWAD_ROLE_IDS = {
    "accountant", "actuary", "aerospace_engineer", "biomedical_engineer", "budget_analyst",
    "chemical_engineer", "civil_engineer", "computer_systems_analyst", "data_analyst",
    "data_scientist", "database_administrator", "electrical_engineer", "environmental_engineer",
    "environmental_scientist", "financial_analyst", "financial_risk_specialist", "hydrologist",
    "industrial_engineer", "information_security_analyst", "logistician", "management_analyst",
    "market_research_analyst", "mechanical_engineer", "operations_research_analyst",
    "public_health_analyst", "software_developer", "statistician", "surveyor",
    "urban_regional_planner", "web_developer",
}
CANONICAL_SKILL_IDS = {
    "critical_thinking", "mathematics", "complex_problem_solving", "systems_analysis",
    "attention_to_detail", "excel", "sql", "python", "data_visualization", "cad_software",
    "matlab", "financial_analysis_software", "analytical_scientific_software", "vba",
    "programming", "javascript", "git", "accounting_software", "gis", "science",
}


def test_loads_exactly_the_expected_mapping_counts():
    """Milestone 13C-4: 39 role mappings for the full 30-role catalog
    (some roles, e.g. accountant/civil_engineer, have more than one SDG
    — our validator only requires at least one per role, so this is not
    a regression) and still 20 skill mappings, one per catalog skill."""
    d = load_cached_sdg_mappings()
    assert len(d["role_sdg_mappings"]) == 39
    assert len(d["skill_sdg_mappings"]) == 20


def test_every_role_sdg_mapping_uses_a_canonical_role_id():
    d = load_cached_sdg_mappings()
    for mapping in d["role_sdg_mappings"]:
        assert mapping["role_id"] in JAWAD_ROLE_IDS


def test_every_skill_sdg_mapping_uses_a_canonical_skill_id():
    d = load_cached_sdg_mappings()
    for mapping in d["skill_sdg_mappings"]:
        assert mapping["skill_id"] in CANONICAL_SKILL_IDS


def test_every_sdg_id_is_within_1_to_17():
    d = load_cached_sdg_mappings()
    for mapping in d["role_sdg_mappings"] + d["skill_sdg_mappings"]:
        assert 1 <= mapping["sdg_id"] <= 17


def test_full_role_and_skill_coverage():
    d = load_cached_sdg_mappings()
    assert {m["role_id"] for m in d["role_sdg_mappings"]} == JAWAD_ROLE_IDS
    assert {m["skill_id"] for m in d["skill_sdg_mappings"]} == CANONICAL_SKILL_IDS


def test_no_certification_or_endorsement_language():
    d = load_cached_sdg_mappings()
    for mapping in d["role_sdg_mappings"] + d["skill_sdg_mappings"]:
        reason = mapping["reason"].lower()
        assert "certified" not in reason and "officially endorsed" not in reason


# --- Malformed input is rejected, not guessed around ----------------------

_BASE_ROLE_MAPPING = {"role_id": "data_analyst", "sdg_id": 8, "reason": "A real, non-trivial reason."}
_BASE_SKILL_MAPPING = {"skill_id": "sql", "sdg_id": 8, "reason": "A real, non-trivial reason."}


def test_rejects_unknown_role_id():
    bad = {**_BASE_ROLE_MAPPING, "role_id": "not_a_real_role"}
    with pytest.raises(CachedCatalogError, match="unknown role_id"):
        _validate_sdg_mappings([bad], [_BASE_SKILL_MAPPING], {"data_analyst"}, {"sql"})


def test_rejects_unknown_skill_id():
    bad = {**_BASE_SKILL_MAPPING, "skill_id": "not_a_real_skill"}
    with pytest.raises(CachedCatalogError, match="unknown skill_id"):
        _validate_sdg_mappings([_BASE_ROLE_MAPPING], [bad], {"data_analyst"}, {"sql"})


@pytest.mark.parametrize("sdg_id", [0, 18, -1, "8", True])
def test_rejects_sdg_id_outside_1_to_17(sdg_id):
    bad = {**_BASE_ROLE_MAPPING, "sdg_id": sdg_id}
    with pytest.raises(CachedCatalogError, match="sdg_id"):
        _validate_sdg_mappings([bad], [_BASE_SKILL_MAPPING], {"data_analyst"}, {"sql"})


def test_rejects_trivial_reason():
    bad = {**_BASE_ROLE_MAPPING, "reason": "x"}
    with pytest.raises(CachedCatalogError, match="reason"):
        _validate_sdg_mappings([bad], [_BASE_SKILL_MAPPING], {"data_analyst"}, {"sql"})


def test_rejects_missing_required_field():
    bad = dict(_BASE_ROLE_MAPPING)
    del bad["reason"]
    with pytest.raises(CachedCatalogError, match="missing fields"):
        _validate_sdg_mappings([bad], [_BASE_SKILL_MAPPING], {"data_analyst"}, {"sql"})


def test_rejects_unsupported_field():
    bad = {**_BASE_ROLE_MAPPING, "made_up_field": "x"}
    with pytest.raises(CachedCatalogError, match="unsupported fields"):
        _validate_sdg_mappings([bad], [_BASE_SKILL_MAPPING], {"data_analyst"}, {"sql"})


def test_rejects_incomplete_role_coverage():
    """A role missing an SDG mapping must fail loud — never silently
    serve an incomplete catalog or invent a mapping to fill the gap."""
    with pytest.raises(CachedCatalogError, match="Roles missing an SDG mapping"):
        _validate_sdg_mappings(
            [_BASE_ROLE_MAPPING], [_BASE_SKILL_MAPPING], {"data_analyst", "financial_analyst"}, {"sql"}
        )


def test_rejects_incomplete_skill_coverage():
    with pytest.raises(CachedCatalogError, match="Skills missing an SDG mapping"):
        _validate_sdg_mappings([_BASE_ROLE_MAPPING], [_BASE_SKILL_MAPPING], {"data_analyst"}, {"sql", "python"})


def test_valid_data_still_loads_unchanged_after_validation_hardening():
    d = load_cached_sdg_mappings()
    assert len(d["role_sdg_mappings"]) == 39 and len(d["skill_sdg_mappings"]) == 20
