"""Regression tests for Milestone 5 review Finding 1: role existence must
not depend on MatchingService.match()'s top-6-ranked results.

Uses a synthetic 8-role catalog (never the real 4-role fixture catalog)
with one target role deliberately scoring below the other 7 for the test
profile, proving it still resolves correctly once the catalog exceeds the
contract's limit<=6 cap (MatchRequest.limit maximum is 6 — see
openapi.yaml). None of this touches the real role_catalog.py fixture data.
"""
from fastapi.testclient import TestClient

from app.api.v1.endpoints.careers import get_role_catalog
from app.main import app
from app.schemas.matching import MatchRequest
from app.schemas.profile import SkillRef, StudentProfile
from app.schemas.roadmaps import RoleProfileRequest
from app.services.matching_provider import FixtureMatchingProvider
from app.services.matching_service import MatchingService
from app.services.profile_service import ProfileService
from app.services.project_catalog import ProjectFixture
from app.services.project_service import ProjectRecommendationService
from app.services.role_catalog import RoleFixture, RoleRequirement
from app.services.trend_provider import NullTrendProvider

PROFILE_JSON = {
    "interests": [],
    "skills": [{"skill_id": "sql", "name": "SQL"}, {"skill_id": "python", "name": "Python"}],
    "projects": [],
}

_TARGET_ROLE_ID = "target_role_below_top_6"

# 7 "filler" roles that all fully match the test profile's skills (sql +
# python), so they dominate the default top-6 ranking; the target role
# requires an unrelated skill the profile doesn't have, so it always scores
# lower and is guaranteed to rank 8th (last).
_FILLER_SKILLS = (
    RoleRequirement("sql", "SQL", weight=1.0),
    RoleRequirement("python", "Python", weight=1.0),
)

_SYNTHETIC_ROLES: tuple[RoleFixture, ...] = tuple(
    RoleFixture(
        role_id=f"filler_role_{i}",
        role_title=f"Filler Role {i}",
        category="Test",
        min_semester=1,
        required_skills=_FILLER_SKILLS,
        transferable_interests=(),
        evidence_ids=(),
    )
    for i in range(7)
) + (
    RoleFixture(
        role_id=_TARGET_ROLE_ID,
        role_title="Target Role Below Top 6",
        category="Test",
        min_semester=1,
        required_skills=(RoleRequirement("cad", "CAD", weight=1.0),),
        transferable_interests=(),
        evidence_ids=(),
    ),
)


class EightRoleCatalog:
    def list_roles(self) -> list[RoleFixture]:
        return list(_SYNTHETIC_ROLES)


def test_synthetic_catalog_places_target_role_outside_default_top_6(client: TestClient):
    """Sanity-checks the fixture itself: confirms the target role genuinely
    does not appear in /careers/match's default (limit=6) results, so the
    tests below are actually exercising the bug condition, not a no-op."""
    app.dependency_overrides[get_role_catalog] = lambda: EightRoleCatalog()
    try:
        response = client.post("/api/v1/careers/match", json={"profile": PROFILE_JSON})
    finally:
        del app.dependency_overrides[get_role_catalog]

    role_ids = {m["role_id"] for m in response.json()["data"]["matches"]}
    assert len(role_ids) == 6
    assert _TARGET_ROLE_ID not in role_ids


def test_roadmap_generates_for_role_ranked_below_top_6(client: TestClient):
    app.dependency_overrides[get_role_catalog] = lambda: EightRoleCatalog()
    try:
        response = client.post(
            "/api/v1/roadmaps/generate", json={"profile": PROFILE_JSON, "role_id": _TARGET_ROLE_ID}
        )
    finally:
        del app.dependency_overrides[get_role_catalog]

    assert response.status_code == 200
    body = response.json()
    assert not any("was not found" in w for w in body["warnings"])
    steps = body["data"]["steps"]
    assert steps and steps[0]["skill_id"] == "cad"


def test_project_simulate_does_not_return_role_not_found_below_top_6(client: TestClient):
    app.dependency_overrides[get_role_catalog] = lambda: EightRoleCatalog()
    try:
        response = client.post(
            "/api/v1/projects/simulate",
            json={
                "profile": PROFILE_JSON,
                "role_id": _TARGET_ROLE_ID,
                "project_id": "project_data_dashboard_001",
            },
        )
    finally:
        del app.dependency_overrides[get_role_catalog]

    assert response.status_code == 200
    data = response.json()["data"]
    assert 0 <= data["baseline_score"] <= 100
    assert 0 <= data["simulated_score"] <= 100


def test_truly_unknown_role_still_returns_established_not_found_states(client: TestClient):
    """Confirms the fix didn't weaken genuine not-found handling: a role
    absent from even this 8-role catalog still behaves exactly as before."""
    app.dependency_overrides[get_role_catalog] = lambda: EightRoleCatalog()
    try:
        roadmap = client.post(
            "/api/v1/roadmaps/generate",
            json={"profile": PROFILE_JSON, "role_id": "does_not_exist_anywhere"},
        )
        simulate = client.post(
            "/api/v1/projects/simulate",
            json={
                "profile": PROFILE_JSON,
                "role_id": "does_not_exist_anywhere",
                "project_id": "project_data_dashboard_001",
            },
        )
    finally:
        del app.dependency_overrides[get_role_catalog]

    assert roadmap.status_code == 200
    assert roadmap.json()["data"]["steps"] == []
    assert simulate.status_code == 404
    assert simulate.json()["error"]["code"] == "ROLE_NOT_FOUND"


class _ProjectCatalogForTarget:
    """A tiny project catalog, local to this test, with two projects for
    the target role — one overlapping its missing skill (cad), one not —
    to prove recommend() ranks by the role's *real* missing skills even
    when that role is outside the top 6."""

    _PROJECTS = (
        ProjectFixture(
            project_id="project_with_cad",
            title="Has CAD",
            role_id=_TARGET_ROLE_ID,
            skills=(SkillRef(skill_id="cad", name="CAD"),),
            estimated_hours=5.0,
            source_ids=("source_with_cad",),
            milestones=("m1",),
        ),
        ProjectFixture(
            project_id="project_without_cad",
            title="No CAD",
            role_id=_TARGET_ROLE_ID,
            skills=(SkillRef(skill_id="unrelated_skill", name="Unrelated"),),
            estimated_hours=5.0,
            source_ids=("source_without_cad",),
            milestones=("m1",),
        ),
    )

    def list_projects(self) -> list[ProjectFixture]:
        return list(self._PROJECTS)

    def get(self, project_id: str) -> ProjectFixture | None:
        return next((p for p in self._PROJECTS if p.project_id == project_id), None)


def test_project_recommend_ranks_by_real_missing_skills_below_top_6(db_session):
    """Service-level test: proves recommend() uses the target role's actual
    missing_skills (not an empty-set fallback) even though it ranks outside
    the top 6 — the project overlapping the real missing skill ("cad")
    must rank first."""
    matching_service = MatchingService(
        profile_service=ProfileService(db_session),
        catalog=EightRoleCatalog(),
        matcher=FixtureMatchingProvider(),
        trends=NullTrendProvider(),
    )
    service = ProjectRecommendationService(matching_service, _ProjectCatalogForTarget())

    profile = StudentProfile(
        interests=[],
        skills=[SkillRef(skill_id="sql", name="SQL"), SkillRef(skill_id="python", name="Python")],
        projects=[],
    )
    outcome = service.recommend(RoleProfileRequest(profile=profile, role_id=_TARGET_ROLE_ID))

    assert [p.project_id for p in outcome.projects][0] == "project_with_cad"


def test_match_role_returns_none_for_genuinely_unknown_role(db_session):
    """Direct unit test of the new MatchingService.match_role() method."""
    matching_service = MatchingService(
        profile_service=ProfileService(db_session),
        catalog=EightRoleCatalog(),
        matcher=FixtureMatchingProvider(),
        trends=NullTrendProvider(),
    )
    profile = StudentProfile(interests=[], skills=[], projects=[])

    assert matching_service.match_role(profile, "does_not_exist_anywhere") is None
    resolution = matching_service.match_role(profile, _TARGET_ROLE_ID)
    assert resolution is not None
    assert resolution.role_match.role_id == _TARGET_ROLE_ID


def test_match_role_preserves_profile_not_found_precedence(db_session):
    """An invalid profile_id must still raise PROFILE_NOT_FOUND via
    match_role(), exactly as match() already does — same resolution
    semantics, not bypassed by the new method."""
    from app.core.errors import AppError
    import pytest

    matching_service = MatchingService(
        profile_service=ProfileService(db_session),
        catalog=EightRoleCatalog(),
        matcher=FixtureMatchingProvider(),
        trends=NullTrendProvider(),
    )
    bad_profile = StudentProfile(profile_id="profile_missing", interests=[], skills=[], projects=[])

    with pytest.raises(AppError) as exc_info:
        matching_service.match_role(bad_profile, _TARGET_ROLE_ID)
    assert exc_info.value.code == "PROFILE_NOT_FOUND"


def test_existing_4_role_fixture_catalog_unaffected(client: TestClient):
    """No override — confirms the real, production 4-role fixture catalog
    behaves exactly as before the fix (match_role() reduces to the same
    outcome match() would already give, since 4 < 6). PROFILE_JSON already
    has sql+python, so the only step is for the remaining missing skill
    with a placeholder resource (data_visualization — "statistics" has
    none, matching test_roadmaps.py's existing coverage)."""
    response = client.post(
        "/api/v1/roadmaps/generate",
        json={"profile": PROFILE_JSON, "role_id": "data_analyst"},
    )
    assert response.status_code == 200
    steps = response.json()["data"]["steps"]
    assert {s["skill_id"] for s in steps} == {"data_visualization"}


def test_match_request_without_role_id_is_unaffected_by_fix(db_session):
    """MatchingService.match() (used directly by /careers/match and
    /scenarios/simulate) keeps its exact prior signature and behavior."""
    matching_service = MatchingService(
        profile_service=ProfileService(db_session),
        catalog=EightRoleCatalog(),
        matcher=FixtureMatchingProvider(),
        trends=NullTrendProvider(),
    )
    profile = StudentProfile(interests=[], skills=[], projects=[])
    outcome = matching_service.match(MatchRequest(profile=profile))
    assert len(outcome.payload.matches) == 6
    assert outcome.payload.catalog_coverage.verified == 8
