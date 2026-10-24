"""Milestone 6B-1: loading and validation only for Jawad's cached O*NET-
derived catalog (app/data/cached/roles.json, skills.json). Nothing here
wires CachedRoleCatalog into matching, roadmaps, projects or SDGs — see
app/services/role_catalog_cached.py's module docstring."""
import pytest

from app.services.role_catalog import FixtureRoleCatalog, RoleFixture
from app.services.role_catalog_cached import (
    CachedCatalogError,
    CachedRoleCatalog,
    _to_role_fixture,
    _validate_roles,
    _validate_skills,
    load_cached_roles,
)

# Milestone 13C-4: Jawad's catalog expanded from the original 8 verified
# roles to the full 30-role target — the original 8 are unchanged, 22
# new O*NET occupations were added.
EXPECTED_ROLE_IDS = {
    "accountant", "actuary", "aerospace_engineer", "biomedical_engineer", "budget_analyst",
    "chemical_engineer", "civil_engineer", "computer_systems_analyst", "data_analyst",
    "data_scientist", "database_administrator", "electrical_engineer", "environmental_engineer",
    "environmental_scientist", "financial_analyst", "financial_risk_specialist", "hydrologist",
    "industrial_engineer", "information_security_analyst", "logistician", "management_analyst",
    "market_research_analyst", "mechanical_engineer", "operations_research_analyst",
    "public_health_analyst", "software_developer", "statistician", "surveyor",
    "urban_regional_planner", "web_developer",
}


def test_loads_exactly_jawads_eight_canonical_roles():
    """Milestone 6D-2A Extension: Jawad's catalog expanded from 4 to 8
    roles (origin/feat/jawad-trends-data @ 4ba98a0) — the original 4
    role_ids are unchanged, 4 new ones were added, none removed."""
    roles = load_cached_roles()
    assert {role.role_id for role in roles} == EXPECTED_ROLE_IDS
    assert len(roles) == 30  # Milestone 13C-4: the full 30-role catalog, up from 8


def test_role_ids_and_skill_ids_are_unique():
    roles = load_cached_roles()
    role_ids = [role.role_id for role in roles]
    assert len(role_ids) == len(set(role_ids))

    skill_ids = [req.skill_id for role in roles for req in role.required_skills]
    # Skills repeat across roles (e.g. "excel") — uniqueness is checked at
    # the skills.json level, not across the flattened role/skill pairs.
    assert len(skill_ids) == sum(len(role.required_skills) for role in roles)


def test_referential_integrity_every_required_skill_is_in_skills_json():
    for role in load_cached_roles():
        for req in role.required_skills:
            assert req.name, f"{role.role_id}: skill '{req.skill_id}' has no resolved name"


def test_verified_and_source_metadata_preserved():
    roles = load_cached_roles()
    for role in roles:
        assert role.verified is True
        assert role.evidence_ids, f"{role.role_id}: evidence_ids must be preserved, not dropped"
        # Preserved verbatim from Jawad's data, e.g. "onet_15_2051_01" — real,
        # traceable O*NET source ids, never invented.
        assert all(eid.startswith("onet_") for eid in role.evidence_ids)


def test_prerequisites_not_invented_min_semester_is_none():
    """Jawad's source data has an empty prerequisites list for every role —
    this must surface as None, never a fabricated semester number."""
    for role in load_cached_roles():
        assert role.min_semester is None


def test_transferable_interests_not_invented():
    for role in load_cached_roles():
        assert role.transferable_interests == ()


def test_loads_exactly_jawads_twenty_canonical_skill_ids():
    """Milestone 6D-2A Extension: skills.json expanded from 14 to 20
    (programming, javascript, git, accounting_software, gis, science
    added; none renamed or removed; the original 14 names/aliases are
    unchanged, only source_ids provenance arrays grew)."""
    from app.services.role_catalog_cached import _load_json

    skills = _load_json("skills.json")["skills"]
    skill_ids = {s["skill_id"] for s in skills}
    assert skill_ids == {
        "critical_thinking", "mathematics", "complex_problem_solving", "systems_analysis",
        "attention_to_detail", "excel", "sql", "python", "data_visualization", "cad_software",
        "matlab", "financial_analysis_software", "analytical_scientific_software", "vba",
        "programming", "javascript", "git", "accounting_software", "gis", "science",
    }
    assert len(skills) == 20


def test_canonical_lookup_by_role_id():
    roles = load_cached_roles()
    data_analyst = next(r for r in roles if r.role_id == "data_analyst")
    assert data_analyst.role_title == "Data Analyst"
    assert data_analyst.category == "Technology & AI"


def test_unknown_role_id_behavior():
    roles = load_cached_roles()
    assert next((r for r in roles if r.role_id == "no_such_role"), None) is None


def test_canonical_cached_role_ids_remain_unchanged():
    """Milestone 6B-2 compatibility mapping, pinned as a regression test:
    Jawad's canonical role_ids must never be silently renamed to match
    our fixture catalog's vocabulary. 2 overlap (data_analyst,
    financial_analyst); the other 6 (now including the 4 roles added in
    the Milestone 6D-2A Extension) do not — see role_catalog_cached.py /
    the 6B-2 report for what this means once cached mode is ever
    activated."""
    cached_ids = {role.role_id for role in load_cached_roles()}
    fixture_ids = {role.role_id for role in FixtureRoleCatalog().list_roles()}

    assert cached_ids == EXPECTED_ROLE_IDS
    assert cached_ids & fixture_ids == {"data_analyst", "financial_analyst"}
    # Milestone 13C-4: the non-overlapping side now holds all 28
    # non-fixture roles (30 total minus the 2 overlapping ones) —
    # derived from EXPECTED_ROLE_IDS itself rather than re-listed, so
    # this can never drift out of sync with it again.
    assert cached_ids - fixture_ids == EXPECTED_ROLE_IDS - {"data_analyst", "financial_analyst"}
    assert fixture_ids - cached_ids == {"mechanical_design_engineer", "sustainability_coordinator"}


def test_cached_role_catalog_satisfies_the_role_catalog_provider_protocol():
    catalog = CachedRoleCatalog()
    roles = catalog.list_roles()
    assert all(isinstance(role, RoleFixture) for role in roles)
    assert {role.role_id for role in roles} == EXPECTED_ROLE_IDS


def test_fixture_mode_is_unchanged_by_the_cached_provider():
    """Regression guard: adding the cached provider must not alter the
    original 4-role FixtureRoleCatalog used by every existing route today."""
    roles = FixtureRoleCatalog().list_roles()
    assert {role.role_id for role in roles} == {
        "data_analyst", "financial_analyst", "mechanical_design_engineer", "sustainability_coordinator",
    }
    assert all(isinstance(role.min_semester, int) for role in roles)


def test_fixture_roles_default_every_skill_to_required_true():
    """Existing fixture roles never set `required` explicitly — they must
    still default to True, unchanged from before this field existed."""
    for role in FixtureRoleCatalog().list_roles():
        assert all(req.required is True for req in role.required_skills), role.role_id


def test_cached_roles_preserve_jawads_actual_required_optional_split():
    """Metadata preservation only (Fix 1) — this does NOT change how
    matching treats these skills; app.services.matching_provider still
    lists an unmatched optional skill in missing_skills exactly like a
    required one until a future matching-integration milestone reads
    this field."""
    expected_optional = {
        "data_analyst": {"excel"},
        "financial_analyst": {"analytical_scientific_software", "vba"},
        "mechanical_engineer": {"python", "excel"},
        # public_health_analyst was rebuilt in Milestone 13D-9 (Jawad's approved
        # "Option C" fix, origin/feat/jawad-ph-fix @ 1cf9b74): python, sql and
        # the new gis skill became optional, alongside excel/data_visualization.
        "public_health_analyst": {"python", "sql", "gis", "excel", "data_visualization"},
        # Added in the Milestone 6D-2A Extension (origin/feat/jawad-trends-data @ 4ba98a0):
        "software_developer": {"mathematics"},
        "accountant": {"sql", "vba", "data_visualization"},
        "civil_engineer": {"matlab", "excel"},
        "environmental_scientist": {"excel", "sql"},
    }
    roles = {role.role_id: role for role in load_cached_roles()}
    for role_id, optional_skill_ids in expected_optional.items():
        role = roles[role_id]
        actual_optional = {req.skill_id for req in role.required_skills if not req.required}
        actual_required = {req.skill_id for req in role.required_skills if req.required}
        assert actual_optional == optional_skill_ids, role_id
        assert actual_required == {req.skill_id for req in role.required_skills} - optional_skill_ids, role_id
        # Every mandatory skill really is marked required, not silently
        # downgraded or left ambiguous.
        assert all(req.required for req in role.required_skills if req.skill_id not in optional_skill_ids)


# --- Validation: malformed/invalid data is rejected, not guessed around ---


def test_rejects_duplicate_skill_id():
    with pytest.raises(CachedCatalogError, match="Duplicate skill_id"):
        _validate_skills([{"skill_id": "sql", "name": "SQL"}, {"skill_id": "sql", "name": "SQL again"}])


def test_rejects_duplicate_role_id():
    role = {
        "role_id": "data_analyst", "role_title": "x", "verified": True,
        "required_skills": [{"skill_id": "sql", "importance": 3, "required": True}],
        "transferable_skills": [], "transferable_interests": [], "prerequisites": [],
        "evidence_ids": ["onet_x"],
    }
    with pytest.raises(CachedCatalogError, match="Duplicate role_id"):
        _validate_roles([role, dict(role)], {"sql": "SQL"})


def test_rejects_unknown_skill_reference():
    role = {
        "role_id": "data_analyst", "role_title": "x", "verified": True, "industry_category": "Technology & AI",
        "required_skills": [{"skill_id": "no_such_skill", "importance": 3, "required": True}],
        "transferable_skills": [], "transferable_interests": [], "prerequisites": [],
        "evidence_ids": ["onet_x"],
    }
    with pytest.raises(CachedCatalogError, match="unknown skill_id"):
        _validate_roles([role], {"sql": "SQL"})


@pytest.mark.parametrize("importance", [0, 6, -1, "5", None])
def test_rejects_malformed_importance(importance):
    role = {
        "role_id": "data_analyst", "role_title": "x", "verified": True, "industry_category": "Technology & AI",
        "required_skills": [{"skill_id": "sql", "importance": importance, "required": True}],
        "transferable_skills": [], "transferable_interests": [], "prerequisites": [],
        "evidence_ids": ["onet_x"],
    }
    with pytest.raises(CachedCatalogError, match="importance must be"):
        _validate_roles([role], {"sql": "SQL"})


def test_rejects_missing_required_flag():
    role = {
        "role_id": "data_analyst", "role_title": "x", "verified": True, "industry_category": "Technology & AI",
        "required_skills": [{"skill_id": "sql", "importance": 3}],
        "transferable_skills": [], "transferable_interests": [], "prerequisites": [],
        "evidence_ids": ["onet_x"],
    }
    with pytest.raises(CachedCatalogError, match="missing fields"):
        _validate_roles([role], {"sql": "SQL"})


def test_rejects_non_bool_required_flag():
    role = {
        "role_id": "data_analyst", "role_title": "x", "verified": True, "industry_category": "Technology & AI",
        "required_skills": [{"skill_id": "sql", "importance": 3, "required": "yes"}],
        "transferable_skills": [], "transferable_interests": [], "prerequisites": [],
        "evidence_ids": ["onet_x"],
    }
    with pytest.raises(CachedCatalogError, match="'required' flag must be a bool"):
        _validate_roles([role], {"sql": "SQL"})


def test_rejects_role_with_no_evidence_ids():
    role = {
        "role_id": "data_analyst", "role_title": "x", "verified": True, "industry_category": "Technology & AI",
        "required_skills": [{"skill_id": "sql", "importance": 3, "required": True}],
        "transferable_skills": [], "transferable_interests": [], "prerequisites": [],
        "evidence_ids": [],
    }
    with pytest.raises(CachedCatalogError, match="evidence_ids"):
        _validate_roles([role], {"sql": "SQL"})


def test_rejects_role_with_no_required_skills():
    role = {
        "role_id": "data_analyst", "role_title": "x", "verified": True, "industry_category": "Technology & AI",
        "required_skills": [],
        "transferable_skills": [], "transferable_interests": [], "prerequisites": [],
        "evidence_ids": ["onet_x"],
    }
    with pytest.raises(CachedCatalogError, match="no required_skills"):
        _validate_roles([role], {"sql": "SQL"})


def test_rejects_missing_schema_field():
    role = {
        "role_id": "data_analyst", "role_title": "x", "verified": True,
        "required_skills": [{"skill_id": "sql", "importance": 3, "required": True}],
        "evidence_ids": ["onet_x"],
        # transferable_skills / transferable_interests / prerequisites omitted
    }
    with pytest.raises(CachedCatalogError, match="missing fields"):
        _validate_roles([role], {"sql": "SQL"})


def test_load_cached_roles_rejects_a_live_labelled_skills_file(monkeypatch):
    """Guards against the exact regression already seen once on Jawad's
    branch (commit dcee82f): a one-time O*NET snapshot must never be
    labelled 'live' — only 'cached' or 'fixture'."""
    import app.services.role_catalog_cached as module

    monkeypatch.setattr(
        module, "_load_json", lambda name: {"data_mode": "live", "skills": []} if name == "skills.json" else []
    )
    with pytest.raises(CachedCatalogError, match="data_mode must be 'cached'"):
        module.load_cached_roles()


# --- Fix 2: malformed non-dict entries fail cleanly, not with a raw ---
# --- AttributeError/TypeError. ---


@pytest.mark.parametrize("malformed_entry", ["not_a_dict", 123, None, ["nested", "list"]])
def test_rejects_non_dict_skill_entries(malformed_entry):
    with pytest.raises(CachedCatalogError, match="expected an object"):
        _validate_skills([malformed_entry])


@pytest.mark.parametrize("malformed_entry", ["not_a_dict", 123, None, ["nested", "list"]])
def test_rejects_non_dict_role_entries(malformed_entry):
    with pytest.raises(CachedCatalogError, match="expected an object"):
        _validate_roles([malformed_entry], {"sql": "SQL"})


@pytest.mark.parametrize("malformed_entry", ["not_a_dict", 123, None, ["nested", "list"]])
def test_rejects_non_dict_required_skill_entries(malformed_entry):
    role = {
        "role_id": "data_analyst", "role_title": "x", "verified": True, "industry_category": "Technology & AI",
        "required_skills": [malformed_entry],
        "transferable_skills": [], "transferable_interests": [], "prerequisites": [],
        "evidence_ids": ["onet_x"],
    }
    with pytest.raises(CachedCatalogError, match="expected an object"):
        _validate_roles([role], {"sql": "SQL"})


def test_valid_jawad_data_still_loads_unchanged_after_fix_2_and_fix_3():
    """The isinstance/schema-field guards added for Fixes 2 and 3 must not
    reject the real, valid cached data."""
    roles = load_cached_roles()
    assert {role.role_id for role in roles} == EXPECTED_ROLE_IDS


# --- Fix 3: deliberate unsupported-field validation policy. ---


def test_known_onet_metadata_fields_are_not_rejected():
    """onet_soc_code, onet_title, source_id, notes, skills_coverage are
    real O*NET provenance fields in Jawad's data (docs/source-register.md
    on feat/jawad-trends-data) — permitted alongside the functional
    fields, not treated as unsupported."""
    role = {
        "role_id": "data_analyst", "role_title": "x", "verified": True, "industry_category": "Technology & AI",
        "required_skills": [{"skill_id": "sql", "importance": 3, "required": True}],
        "transferable_skills": [], "transferable_interests": [], "prerequisites": [],
        "evidence_ids": ["onet_x"],
        "onet_soc_code": "15-2051.01", "onet_title": "Business Intelligence Analysts",
        "source_id": "onet_15_2051_01", "notes": "some provenance note", "skills_coverage": "limited",
    }
    _validate_roles([role], {"sql": "SQL"})  # must not raise


def test_known_skill_metadata_fields_are_not_rejected():
    """aliases/source_ids are real skill metadata (used by Hussain's
    normalizer and for traceability) — permitted, not unsupported."""
    names = _validate_skills(
        [{"skill_id": "sql", "name": "SQL", "aliases": ["Structured Query Language"], "source_ids": ["onet_x"]}]
    )
    assert names == {"sql": "SQL"}


def test_rejects_genuinely_unsupported_role_field():
    role = {
        "role_id": "data_analyst", "role_title": "x", "verified": True, "industry_category": "Technology & AI",
        "required_skills": [{"skill_id": "sql", "importance": 3, "required": True}],
        "transferable_skills": [], "transferable_interests": [], "prerequisites": [],
        "evidence_ids": ["onet_x"],
        "made_up_field": "should not be silently accepted",
    }
    with pytest.raises(CachedCatalogError, match="unsupported fields"):
        _validate_roles([role], {"sql": "SQL"})


def test_rejects_genuinely_unsupported_skill_field():
    with pytest.raises(CachedCatalogError, match="unsupported fields"):
        _validate_skills([{"skill_id": "sql", "name": "SQL", "made_up_field": "x"}])


def test_weight_is_importance_scaled_to_the_existing_0_to_1_convention():
    """RoleRequirement.weight elsewhere in the fixture catalog is a 0-1
    float (see role_catalog.py); importance (1-5) is converted the same
    way, not left on its own 1-5 scale."""
    role = {
        "role_id": "r", "role_title": "x", "verified": True, "industry_category": "Technology & AI",
        "required_skills": [{"skill_id": "sql", "importance": 5, "required": True}],
        "transferable_skills": [], "transferable_interests": [], "prerequisites": [],
        "evidence_ids": ["onet_x"],
    }
    fixture = _to_role_fixture(role, {"sql": "SQL"})
    assert fixture.required_skills[0].weight == 1.0
