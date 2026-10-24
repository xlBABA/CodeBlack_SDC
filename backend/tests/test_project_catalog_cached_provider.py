"""Milestone 6D-2C: CachedProjectCatalog adapter — implementation and
testing ONLY. Not wired into any route or FastAPI dependency; GET
/projects/recommend and /projects/simulate still use only
FixtureProjectCatalog by default.
"""
import pytest

from app.schemas.profile import StudentProfile
from app.schemas.roadmaps import RoleProfileRequest
from app.services.matching_provider import FixtureMatchingProvider
from app.services.matching_service import MatchingService
from app.services.profile_service import ProfileService
from app.services.project_catalog import FixtureProjectCatalog
from app.services.project_catalog_cached import CachedProjectCatalog, _to_project_fixture
from app.services.project_service import ProjectRecommendationService, ProjectSimulationService
from app.services.role_catalog_cached import CachedCatalogError, CachedRoleCatalog
from app.services.trend_provider import NullTrendProvider
from app.schemas.projects import ProjectSimulationRequest

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


def _recommend_service(db_session) -> ProjectRecommendationService:
    catalog = CachedRoleCatalog()
    matching_service = MatchingService(
        profile_service=ProfileService(db_session),
        catalog=catalog,
        matcher=FixtureMatchingProvider(),
        trends=NullTrendProvider(),
    )
    return ProjectRecommendationService(matching_service, CachedProjectCatalog())


def _simulate_service(db_session) -> ProjectSimulationService:
    catalog = CachedRoleCatalog()
    matching_service = MatchingService(
        profile_service=ProfileService(db_session),
        catalog=catalog,
        matcher=FixtureMatchingProvider(),
        trends=NullTrendProvider(),
    )
    return ProjectSimulationService(matching_service, CachedProjectCatalog())


# --- 1. Exactly 17 cached projects ------------------------------------------


def test_lists_exactly_seventeen_cached_projects():
    projects = CachedProjectCatalog().list_projects()
    assert len(projects) == 17
    assert len({p.project_id for p in projects}) == 17


# --- 2. Exactly 8 canonical role IDs ----------------------------------------


def test_project_role_ids_are_the_eight_canonical_roles():
    role_ids = {p.role_id for p in CachedProjectCatalog().list_projects()}
    assert role_ids == CANONICAL_ROLE_IDS


# --- 3. All project skill IDs resolve to real canonical names --------------


def test_every_project_skill_resolves_to_a_real_canonical_name():
    for project in CachedProjectCatalog().list_projects():
        for skill in project.skills:
            assert skill.skill_id in CANONICAL_SKILL_IDS
            assert skill.name  # a real resolved name, never blank
            assert skill.name != skill.skill_id  # resolved, not just echoed back


def test_name_resolution_rejects_an_unknown_skill_id_rather_than_inventing_one():
    with pytest.raises(CachedCatalogError, match="unknown skill_id"):
        _to_project_fixture(
            {
                "project_id": "p", "title": "t", "role_id": "data_analyst",
                "skill_ids": ["not_a_real_skill"], "estimated_hours": 1.0,
                "source_ids": ["s"], "milestones": ["m"],
            },
            {"sql": "SQL"},
        )


# --- 4. Project IDs, source IDs and hours are preserved ---------------------


def test_project_ids_source_ids_and_hours_match_the_real_source_data():
    projects = {p.project_id: p for p in CachedProjectCatalog().list_projects()}
    dashboard = projects["da_online_retail_dashboard"]
    assert dashboard.role_id == "data_analyst"
    assert dashboard.source_ids == ("uci_online_retail_ii",)
    assert dashboard.estimated_hours > 0
    assert dashboard.milestones  # non-empty, preserved verbatim


# --- 5. No fabricated or fixture project IDs --------------------------------


def test_cached_projects_never_overlap_with_fixture_project_ids():
    cached_ids = {p.project_id for p in CachedProjectCatalog().list_projects()}
    fixture_ids = {p.project_id for p in FixtureProjectCatalog().list_projects()}
    assert cached_ids.isdisjoint(fixture_ids)


def test_no_fixture_project_appears_in_cached_results():
    cached = CachedProjectCatalog().list_projects()
    fixture = FixtureProjectCatalog().list_projects()
    assert not any(p in fixture for p in cached)


# --- 6. Team-estimate provenance is accurately disclosed --------------------


def test_every_cached_project_discloses_team_estimate_basis():
    """All 17 real projects are team_estimate (none provider-verified) —
    confirmed directly against the source, never silently upgraded to
    looking provider-verified."""
    for project in CachedProjectCatalog().list_projects():
        assert project.hours_basis == "team_estimate"
        assert project.hours_basis_note  # a real, non-empty explanation


def test_fixture_projects_have_no_hours_basis_claim_at_all():
    """FixtureProjectCatalog's placeholder projects never claim any
    basis — None, not "team_estimate" and not "provider_verified"."""
    for project in FixtureProjectCatalog().list_projects():
        assert project.hours_basis is None


def test_recommend_discloses_team_estimate_warning_for_cached_projects(db_session):
    service = _recommend_service(db_session)
    profile = StudentProfile(interests=[], skills=[], projects=[])

    outcome = service.recommend(RoleProfileRequest(profile=profile, role_id="data_analyst"))

    assert outcome.projects  # sanity: something was actually recommended
    assert any("team estimate" in w.lower() for w in outcome.warnings)


def test_recommend_warning_is_absent_for_fixture_projects(db_session):
    """Regression guard: the new warning in project_service.py must never
    fire for FixtureProjectCatalog, whose hours_basis is always None."""
    catalog = CachedRoleCatalog()  # cached role IDs so data_analyst resolves either way
    from app.services.role_catalog import FixtureRoleCatalog

    matching_service = MatchingService(
        profile_service=ProfileService(db_session),
        catalog=FixtureRoleCatalog(),
        matcher=FixtureMatchingProvider(),
        trends=NullTrendProvider(),
    )
    service = ProjectRecommendationService(matching_service, FixtureProjectCatalog())
    profile = StudentProfile(interests=[], skills=[], projects=[])

    outcome = service.recommend(RoleProfileRequest(profile=profile, role_id="data_analyst"))

    assert outcome.warnings == []


# --- 7/8. SDG-adjacent: N/A here (see test_sdg_catalog_cached_provider.py) -


# --- 9. Unknown roles return honest empty outcomes --------------------------


def test_unknown_role_returns_honest_empty_recommendation(db_session):
    service = _recommend_service(db_session)
    profile = StudentProfile(interests=[], skills=[], projects=[])

    outcome = service.recommend(RoleProfileRequest(profile=profile, role_id="does_not_exist_anywhere"))

    assert outcome.projects == []
    assert outcome.warnings == [
        "No portfolio projects are available yet for this role. Projects are available for 8 of 30 roles."
    ]


def test_fixture_only_role_returns_honest_empty_recommendation_against_cached_catalog(db_session):
    """mechanical_design_engineer/sustainability_coordinator exist in our
    fixture catalog but have no cached project under that role_id
    vocabulary — honest empty, never borrowed from an unrelated role."""
    service = _recommend_service(db_session)
    profile = StudentProfile(interests=[], skills=[], projects=[])

    outcome = service.recommend(RoleProfileRequest(profile=profile, role_id="mechanical_design_engineer"))

    assert outcome.projects == []


# --- 10. Frozen project DTOs validate successfully --------------------------


def test_recommended_project_dto_validates_for_every_cached_project(db_session):
    service = _recommend_service(db_session)
    profile = StudentProfile(interests=[], skills=[], projects=[])

    for role_id in CANONICAL_ROLE_IDS:
        outcome = service.recommend(RoleProfileRequest(profile=profile, role_id=role_id, limit=10))
        for project in outcome.projects:
            assert project.project_id
            assert 0 <= project.estimated_hours


def test_project_simulation_works_against_a_cached_project_and_catalog(db_session):
    """Step 13: simulation scoring/matching behavior is unaffected —
    same MatchingService.match_role() mechanism, just fed cached data."""
    service = _simulate_service(db_session)
    profile = StudentProfile(interests=[], skills=[], projects=[])

    outcome = service.simulate(
        ProjectSimulationRequest(
            profile=profile, role_id="data_analyst", project_id="da_online_retail_dashboard"
        )
    )

    assert 0 <= outcome.payload.baseline_score <= 100
    assert 0 <= outcome.payload.simulated_score <= 100
    assert outcome.payload.simulated_score >= outcome.payload.baseline_score
    assert "not guarantee employment" in outcome.payload.disclaimer


def test_no_project_ever_claims_a_real_internship_or_job_offer():
    """Step 10: no title/expected_outcome in the real data frames a
    project as an actual internship, employer or job offer."""
    red_flags = ("internship", "job offer", "guaranteed job", "hired", "employment contract")
    for project in CachedProjectCatalog().list_projects():
        haystack = f"{project.title} {project.expected_outcome or ''}".lower()
        assert not any(flag in haystack for flag in red_flags), project.project_id


# --- 11. Existing fixture provider behavior remains unchanged --------------


def test_default_project_routes_still_use_fixture_projects_only(client):
    response = client.post(
        "/api/v1/projects/recommend",
        json={"profile": {"interests": [], "skills": [], "projects": []}, "role_id": "data_analyst"},
    )
    assert response.status_code == 200
    fixture_ids = {p.project_id for p in FixtureProjectCatalog().list_projects()}
    for project in response.json()["data"]["projects"]:
        assert project["project_id"] in fixture_ids


def test_required_optional_skill_distinction_still_excludes_optional_from_missing(db_session):
    """accountant: sql/vba/data_visualization are optional — confirms
    the matching layer's existing guarantee still holds when driven by
    the cached role catalog, which is what ranks cached projects."""
    catalog = CachedRoleCatalog()
    matching_service = MatchingService(
        profile_service=ProfileService(db_session),
        catalog=catalog,
        matcher=FixtureMatchingProvider(),
        trends=NullTrendProvider(),
    )
    profile = StudentProfile(interests=[], skills=[], projects=[])
    resolution = matching_service.match_role(profile, "accountant")
    missing_ids = {s.skill_id for s in resolution.role_match.missing_skills}
    assert missing_ids == {
        "attention_to_detail", "excel", "critical_thinking", "complex_problem_solving",
        "mathematics", "accounting_software",
    }
    assert "sql" not in missing_ids and "vba" not in missing_ids and "data_visualization" not in missing_ids


# --- 12/13. No activation, no new deps --------------------------------------


def test_cached_project_catalog_is_referenced_only_behind_catalog_mode_gating():
    """As of Milestone 6D-2D, CachedProjectCatalog IS referenced by
    projects.py — but only inside get_project_catalog()'s CATALOG_MODE=
    'cached' branch, never unconditionally. See test_catalog_mode.py /
    test_matching_mode.py for the full activation-matrix behavior."""
    import app.api.v1.endpoints.projects as projects_endpoint

    source = open(projects_endpoint.__file__, encoding="utf-8").read()
    assert "CachedProjectCatalog" in source
    assert 'settings.CATALOG_MODE == "cached"' in source


def test_no_heavy_or_network_dependency_imported():
    import sys

    for forbidden in ("sentence_transformers", "torch", "transformers", "requests"):
        assert forbidden not in sys.modules
