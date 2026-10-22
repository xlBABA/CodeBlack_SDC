"""Milestone 6D-2B: CachedResourceCatalog adapter — implementation and
testing ONLY. Not wired into any route or FastAPI dependency; GET
/roadmaps/generate still uses only FixtureResourceCatalog by default.
"""
from app.schemas.profile import StudentProfile
from app.schemas.roadmaps import RoleProfileRequest
from app.services.matching_provider import FixtureMatchingProvider
from app.services.matching_service import MatchingService
from app.services.resource_catalog import FixtureResourceCatalog
from app.services.resource_catalog_cached import (
    CachedResourceCatalog,
    _provenance_text,
    _to_resource_fixtures,
)
from app.services.role_catalog_cached import CachedRoleCatalog
from app.services.roadmap_service import RoadmapService
from app.services.trend_provider import NullTrendProvider

CANONICAL_SKILL_IDS = {
    "critical_thinking", "mathematics", "complex_problem_solving", "systems_analysis",
    "attention_to_detail", "excel", "sql", "python", "data_visualization", "cad_software",
    "matlab", "financial_analysis_software", "analytical_scientific_software", "vba",
    "programming", "javascript", "git", "accounting_software", "gis", "science",
}


def _profile_service(db_session):
    from app.services.profile_service import ProfileService

    return ProfileService(db_session)


def _roadmap_service(db_session) -> RoadmapService:
    catalog = CachedRoleCatalog()
    matching_service = MatchingService(
        profile_service=_profile_service(db_session),
        catalog=catalog,
        matcher=FixtureMatchingProvider(),
        trends=NullTrendProvider(),
    )
    return RoadmapService(matching_service, catalog, CachedResourceCatalog())


# --- 1. All 16 cached resources --------------------------------------------


def test_lists_all_sixteen_cached_resources():
    fixtures = CachedResourceCatalog().list_resources()
    assert len(fixtures) == 16
    assert len({f.resource_id for f in fixtures}) == 16


# --- 2. Canonical 20-skill references --------------------------------------


def test_every_fixture_skill_id_is_canonical():
    for fixture in CachedResourceCatalog().list_resources():
        assert fixture.skill_id in CANONICAL_SKILL_IDS


# --- 3. Resource IDs and URLs preserved ------------------------------------


def test_resource_ids_and_urls_match_the_real_source_data():
    fixtures = {f.resource_id: f for f in CachedResourceCatalog().list_resources()}
    sql_resource = fixtures["mslearn_tsql_query_modify"]
    assert sql_resource.skill_id == "sql"
    assert sql_resource.url == (
        "https://learn.microsoft.com/en-us/training/paths/get-started-querying-with-transact-sql/"
    )
    assert sql_resource.estimated_hours == 5.75


def test_no_resource_url_is_invented():
    """Every url must be a real https:// link straight from the source
    data — never fabricated here."""
    for fixture in CachedResourceCatalog().list_resources():
        assert fixture.url is not None and fixture.url.startswith("https://")


# --- 4. Multiple skills mapped correctly -----------------------------------


def test_multi_skill_resource_fans_out_without_duplicating_the_record():
    """No resource currently covers more than one skill, but the source
    schema allows it — this must fan out into one ResourceFixture per
    skill_id, same resource_id/title/hours/url, not be silently dropped
    or merged into a single entry."""
    synthetic = {
        "resource_id": "multi_skill_example", "skill_ids": ["sql", "python"],
        "title": "T", "estimated_hours": 2.0, "hours_source": "Provider-stated: 2h.",
        "url": "https://example.com", "price": {"status": "free_stated"},
    }
    fixtures = _to_resource_fixtures(synthetic)
    assert len(fixtures) == 2
    assert {f.skill_id for f in fixtures} == {"sql", "python"}
    assert all(f.resource_id == "multi_skill_example" for f in fixtures)
    assert all(f.estimated_hours == 2.0 for f in fixtures)
    assert all(f.url == "https://example.com" for f in fixtures)


def test_current_real_data_has_no_multi_skill_resources_yet():
    """Sanity check for the test above: today's 16 resources are all
    single-skill, so the 16-resource count and the 16-fixture count
    (test 1) are expected to match exactly."""
    from app.services.resource_catalog_cached import load_cached_resources

    assert all(len(r["skill_ids"]) == 1 for r in load_cached_resources())


# --- 5/9. Required vs optional roadmap behavior + RoadmapService compat ---


def test_optional_skills_never_become_roadmap_steps_even_with_a_resource_available(db_session):
    """accountant: sql/vba/data_visualization are optional AND have a
    real cached resource — they must never appear as roadmap steps,
    because the matching provider never puts an unmatched optional
    skill in missing_skills at all (Milestone 6B-2/6C-2A)."""
    service = _roadmap_service(db_session)
    profile = StudentProfile(interests=[], skills=[], projects=[])

    outcome = service.generate(RoleProfileRequest(profile=profile, role_id="accountant"))

    step_skill_ids = {s.skill_id for s in outcome.payload.steps}
    assert step_skill_ids == {"excel", "critical_thinking", "mathematics", "accounting_software"}
    assert "sql" not in step_skill_ids
    assert "vba" not in step_skill_ids
    assert "data_visualization" not in step_skill_ids


def test_required_skills_without_a_resource_produce_an_honest_warning_not_a_step(db_session):
    """accountant: attention_to_detail and complex_problem_solving are
    required but have no cached resource — honest gap, never fabricated."""
    service = _roadmap_service(db_session)
    profile = StudentProfile(interests=[], skills=[], projects=[])

    outcome = service.generate(RoleProfileRequest(profile=profile, role_id="accountant"))

    step_skill_ids = {s.skill_id for s in outcome.payload.steps}
    assert "attention_to_detail" not in step_skill_ids
    assert "complex_problem_solving" not in step_skill_ids
    assert any("attention_to_detail" in w for w in outcome.warnings)
    assert any("complex_problem_solving" in w for w in outcome.warnings)


# --- 6. Unknown skills and honest-empty behavior ---------------------------


def test_unknown_role_id_returns_honest_empty_roadmap(db_session):
    service = _roadmap_service(db_session)
    profile = StudentProfile(interests=[], skills=[], projects=[])

    outcome = service.generate(RoleProfileRequest(profile=profile, role_id="does_not_exist_anywhere"))

    assert outcome.payload.steps == []
    assert any("was not found" in w for w in outcome.warnings)


# --- 7. Provenance and hour-estimate disclosure ----------------------------


def test_provenance_text_distinguishes_provider_stated_from_team_estimate():
    from app.services.resource_catalog_cached import load_cached_resources

    resources_by_id = {r["resource_id"]: r for r in load_cached_resources()}
    provider_stated = resources_by_id["mslearn_tsql_query_modify"]
    team_estimate = resources_by_id["mathworks_matlab_onramp"]

    assert _provenance_text(provider_stated).startswith("Provider-stated:")
    assert _provenance_text(team_estimate).startswith("Team estimate:")
    assert "Price not stated by provider." in _provenance_text(team_estimate)


def test_roadmap_step_reason_discloses_provenance_for_cached_resources(db_session):
    """civil_engineer's required, resourced skills (mathematics,
    critical_thinking, cad_software, gis) must each carry the base
    'Closes a missing skill' reason PLUS a provenance disclosure —
    optional matlab/excel never appear as steps even though both have a
    resource (same guarantee as the accountant test above)."""
    service = _roadmap_service(db_session)
    profile = StudentProfile(interests=[], skills=[], projects=[])

    outcome = service.generate(RoleProfileRequest(profile=profile, role_id="civil_engineer"))

    step_skill_ids = {s.skill_id for s in outcome.payload.steps}
    assert step_skill_ids == {"mathematics", "critical_thinking", "cad_software", "gis"}
    assert "matlab" not in step_skill_ids and "excel" not in step_skill_ids

    for step in outcome.payload.steps:
        assert step.reason.startswith("Closes a missing skill")
        assert "Provider-stated" in step.reason or "Team estimate" in step.reason


# --- 8. No fixture resource leakage ----------------------------------------


def test_cached_resources_never_overlap_with_fixture_resource_ids():
    cached_ids = {f.resource_id for f in CachedResourceCatalog().list_resources()}
    fixture_ids = {f.resource_id for f in FixtureResourceCatalog().list_resources()}
    assert cached_ids.isdisjoint(fixture_ids)


def test_cached_resources_are_all_marked_verified_unlike_fixtures():
    assert all(f.verified is True for f in CachedResourceCatalog().list_resources())
    assert all(f.verified is False for f in FixtureResourceCatalog().list_resources())


# --- 10. No effect on currently active FastAPI providers -------------------


def test_default_roadmap_route_still_uses_fixture_resources_only(client):
    """No override — CachedResourceCatalog's mere existence in the
    codebase must not change today's active /roadmaps/generate route."""
    response = client.post(
        "/api/v1/roadmaps/generate",
        json={"profile": {"interests": [], "skills": [], "projects": []}, "role_id": "data_analyst"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data_mode"] == "fixture"
    fixture_resource_ids = {f.resource_id for f in FixtureResourceCatalog().list_resources()}
    for step in body["data"]["steps"]:
        assert step["resource_id"] in fixture_resource_ids


# --- 11. Existing default fixture behavior unchanged -----------------------


def test_fixture_mode_roadmap_reason_text_is_byte_identical_to_before(client):
    """Regression guard for the roadmap_service.py edit in this milestone:
    FixtureResourceCatalog's resources all have provenance=None, so the
    reason-text format must be completely unaffected."""
    response = client.post(
        "/api/v1/roadmaps/generate",
        json={"profile": {"interests": [], "skills": [], "projects": []}, "role_id": "data_analyst"},
    )
    steps = response.json()["data"]["steps"]
    sql_step = next(s for s in steps if s["skill_id"] == "sql")
    assert sql_step["reason"] == "Closes a missing skill for Data Analyst (role-weighted priority 1.0)."


def test_fixture_resource_fixture_defaults_are_unchanged():
    """ResourceFixture's new url/provenance fields default to None for
    every existing fixture resource — purely additive widening."""
    for fixture in FixtureResourceCatalog().list_resources():
        assert fixture.url is None
        assert fixture.provenance is None
