"""Milestone 6D-2C: CachedSdgCatalog adapter — implementation and
testing ONLY. Not wired into any route or FastAPI dependency; GET
/sdgs/{role_id} still uses only FixtureSdgCatalog by default.
"""
from app.services.role_catalog_cached import load_cached_roles
from app.services.sdg_catalog import FixtureSdgCatalog
from app.services.sdg_catalog_cached import CachedSdgCatalog
from app.services.sdg_service import SdgService

CANONICAL_ROLE_IDS = {
    "data_analyst", "financial_analyst", "mechanical_engineer", "public_health_analyst",
    "software_developer", "accountant", "civil_engineer", "environmental_scientist",
}
CANONICAL_SKILL_IDS = {
    "critical_thinking", "mathematics", "complex_problem_solving", "systems_analysis",
    "attention_to_detail", "excel", "sql", "python", "data_visualization", "cad_software",
    "matlab", "financial_analysis_software", "analytical_scientific_software", "vba",
    "programming", "javascript", "git", "accounting_software", "gis", "science",
}


# --- 7. All 11 role SDG mappings and 20 skill mappings remain intact ------


def test_all_eight_canonical_roles_return_a_mapping_set():
    catalog = CachedSdgCatalog()
    for role_id in CANONICAL_ROLE_IDS:
        result = catalog.get(role_id)
        assert result is not None, role_id
        assert result.role_sdg  # at least one SDG per role


def test_total_role_sdg_mapping_count_is_eleven():
    catalog = CachedSdgCatalog()
    total = sum(len(catalog.get(role_id).role_sdg) for role_id in CANONICAL_ROLE_IDS)
    assert total == 11


def test_total_distinct_skill_sdg_entries_covers_all_twenty_skills():
    """skill_sdg_mappings is a flat, global 20-entry list in the source
    data — confirm every canonical skill_id appears somewhere across all
    eight roles' skill_sdg once joined back by role."""
    from app.services.sdg_catalog_cached import load_cached_sdg_mappings

    all_skill_ids = {m["skill_id"] for m in load_cached_sdg_mappings()["skill_sdg_mappings"]}
    assert all_skill_ids == CANONICAL_SKILL_IDS
    assert len(load_cached_sdg_mappings()["skill_sdg_mappings"]) == 20


# --- 8. Multiple SDGs per role survive adapter conversion ------------------


def test_accountant_has_exactly_two_sdgs_preserved_as_a_tuple():
    result = CachedSdgCatalog().get("accountant")
    sdg_ids = {m.sdg_id for m in result.role_sdg}
    assert sdg_ids == {8, 16}
    assert isinstance(result.role_sdg, tuple)


def test_civil_engineer_has_exactly_two_sdgs_preserved_as_a_tuple():
    result = CachedSdgCatalog().get("civil_engineer")
    sdg_ids = {m.sdg_id for m in result.role_sdg}
    assert sdg_ids == {9, 11}


def test_single_sdg_roles_still_work_correctly():
    result = CachedSdgCatalog().get("data_analyst")
    assert len(result.role_sdg) == 1
    assert result.role_sdg[0].sdg_id == 8


# --- Original SDG numbers, skill IDs and rationale text preserved --------


def test_reason_text_is_preserved_verbatim_not_rewritten():
    from app.services.sdg_catalog_cached import load_cached_sdg_mappings

    raw = next(
        m for m in load_cached_sdg_mappings()["role_sdg_mappings"] if m["role_id"] == "data_analyst"
    )
    result = CachedSdgCatalog().get("data_analyst")
    assert result.role_sdg[0].reason == raw["reason"]


def test_all_sdg_ids_are_within_1_to_17():
    catalog = CachedSdgCatalog()
    for role_id in CANONICAL_ROLE_IDS:
        for mapping in catalog.get(role_id).role_sdg:
            assert 1 <= mapping.sdg_id <= 17
        for mapping in catalog.get(role_id).skill_sdg:
            assert 1 <= mapping.sdg_id <= 17


# --- 6/9. Honest-empty for unknown and fixture-only role IDs --------------


def test_unknown_role_id_returns_none():
    assert CachedSdgCatalog().get("does_not_exist_anywhere") is None


def test_fixture_only_role_ids_return_none_not_an_accidental_join():
    """mechanical_design_engineer/sustainability_coordinator exist in our
    fixture catalog but are not among Jawad's canonical role_ids — must
    never silently resolve to a mapping meant for a different role."""
    catalog = CachedSdgCatalog()
    assert catalog.get("mechanical_design_engineer") is None
    assert catalog.get("sustainability_coordinator") is None


def test_no_mapping_is_invented_for_unsupported_roles_or_skills():
    """Every mapping returned must trace back to the real source data —
    no synthesized skill_sdg entry for a skill the role doesn't require."""
    result = CachedSdgCatalog().get("data_analyst")
    role = next(r for r in load_cached_roles() if r.role_id == "data_analyst")
    role_skill_ids = {req.skill_id for req in role.required_skills}
    for mapping in result.skill_sdg:
        assert mapping.skill_id in role_skill_ids


# --- 8 (certification disclaimer) / SdgService compatibility -------------


def test_sdg_service_compatible_with_cached_catalog_and_keeps_its_disclaimer():
    service = SdgService(CachedSdgCatalog())
    outcome = service.get_mappings("civil_engineer")

    assert len(outcome.payload.role_sdg_mappings) == 2
    assert any("not" in w.lower() and "certification" in w.lower() for w in outcome.warnings)
    assert any("united nations" in w.lower() or "endorsement" in w.lower() for w in outcome.warnings)


def test_sdg_service_honest_empty_for_unknown_role_via_cached_catalog():
    service = SdgService(CachedSdgCatalog())
    outcome = service.get_mappings("does_not_exist_anywhere")

    assert outcome.payload.role_sdg_mappings == []
    assert outcome.payload.skill_sdg_mappings == []
    assert outcome.warnings  # still discloses something, not a silent empty


def test_frozen_sdg_dto_validates_for_every_canonical_role():
    service = SdgService(CachedSdgCatalog())
    for role_id in CANONICAL_ROLE_IDS:
        outcome = service.get_mappings(role_id)
        for mapping in outcome.payload.role_sdg_mappings:
            assert 1 <= mapping.sdg_id <= 17
            assert mapping.reason


# --- No fixture leakage / no effect on active routes -----------------------


def test_cached_catalog_never_returns_fixture_only_mappings():
    fixture = FixtureSdgCatalog()
    cached = CachedSdgCatalog()
    # The 2 overlapping role_ids (data_analyst, financial_analyst) must
    # resolve to Jawad's real reasons, never the fixture's illustrative text.
    for role_id in ("data_analyst", "financial_analyst"):
        fixture_reason = fixture.get(role_id).role_sdg[0].reason
        cached_reason = cached.get(role_id).role_sdg[0].reason
        assert cached_reason != fixture_reason


def test_default_sdg_route_still_uses_fixture_catalog_only(client):
    response = client.get("/api/v1/sdgs/data_analyst")
    assert response.status_code == 200
    body = response.json()
    assert "Illustrative demonstration mapping" in body["data"]["role_sdg_mappings"][0]["reason"]


def test_cached_sdg_catalog_not_referenced_by_any_route():
    import app.api.v1.endpoints.sdgs as sdgs_endpoint

    source = open(sdgs_endpoint.__file__, encoding="utf-8").read()
    assert "CachedSdgCatalog" not in source
