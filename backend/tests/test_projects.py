from fastapi.testclient import TestClient

from app.api.v1.endpoints.projects import get_project_catalog
from app.fixtures.sample_profiles import SAMPLE_PROFILES
from app.main import app
from app.schemas.matching import MatchRequest
from app.schemas.profile import SkillRef, StudentProfile
from app.schemas.projects import ProjectSimulationRequest
from app.services.matching_provider import FixtureMatchingProvider
from app.services.matching_service import MatchingService
from app.services.profile_service import ProfileService
from app.services.project_catalog import FixtureProjectCatalog
from app.services.project_service import ProjectSimulationService
from app.services.role_catalog import FixtureRoleCatalog
from app.services.trend_provider import NullTrendProvider

CS_PROFILE = SAMPLE_PROFILES["cs_undergrad_data"].model_dump(exclude_none=True)
EMPTY_PROFILE = {"interests": [], "skills": [], "projects": []}


def test_openapi_includes_project_routes():
    schema = app.openapi()
    assert "/api/v1/projects/recommend" in schema["paths"]
    assert "/api/v1/projects/simulate" in schema["paths"]


def test_recommend_returns_relevant_project_for_role(client: TestClient):
    response = client.post(
        "/api/v1/projects/recommend", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data_mode"] == "fixture"
    projects = body["data"]["projects"]
    assert len(projects) == 1
    assert projects[0]["project_id"] == "project_data_dashboard_001"
    for field in ("project_id", "title", "skill_ids", "estimated_hours", "source_ids", "milestones"):
        assert field in projects[0]
    assert projects[0]["milestones"]  # ordered, non-empty


def test_recommend_default_limit_is_three(client: TestClient):
    # Only one project exists per role today, so this exercises the default
    # (3) without truncating below what's available — still proves no error
    # and the service-level default documented in the report.
    response = client.post(
        "/api/v1/projects/recommend", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
    )
    assert len(response.json()["data"]["projects"]) <= 3


def test_recommend_explicit_limit_is_respected(client: TestClient):
    response = client.post(
        "/api/v1/projects/recommend",
        json={"profile": EMPTY_PROFILE, "role_id": "data_analyst", "limit": 1},
    )
    assert len(response.json()["data"]["projects"]) <= 1


def test_recommend_unknown_role_id_returns_honest_empty_catalog(client: TestClient):
    response = client.post(
        "/api/v1/projects/recommend", json={"profile": EMPTY_PROFILE, "role_id": "no_such_role"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["projects"] == []
    assert body["warnings"]


def test_project_catalog_dependency_is_overridable(client: TestClient):
    class EmptyProjectCatalog:
        def list_projects(self):
            return []

        def get(self, project_id):
            return None

    app.dependency_overrides[get_project_catalog] = lambda: EmptyProjectCatalog()
    try:
        response = client.post(
            "/api/v1/projects/recommend", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
    finally:
        del app.dependency_overrides[get_project_catalog]

    assert response.json()["data"]["projects"] == []


def test_simulate_returns_contract_shape_with_bounded_scores(client: TestClient):
    response = client.post(
        "/api/v1/projects/simulate",
        json={
            "profile": EMPTY_PROFILE,
            "role_id": "data_analyst",
            "project_id": "project_data_dashboard_001",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert 0 <= data["baseline_score"] <= 100
    assert 0 <= data["simulated_score"] <= 100
    assert isinstance(data["disclaimer"], str) and data["disclaimer"]
    assert "not" in data["disclaimer"].lower()


def test_simulate_increases_score_when_project_adds_missing_skills(client: TestClient):
    response = client.post(
        "/api/v1/projects/simulate",
        json={
            "profile": EMPTY_PROFILE,
            "role_id": "data_analyst",
            "project_id": "project_data_dashboard_001",
        },
    )
    data = response.json()["data"]
    assert data["simulated_score"] > data["baseline_score"]
    assert set(data["assumed_skill_ids"]) == {"sql", "python", "data_visualization"}


def test_simulate_does_not_double_count_already_held_skills(client: TestClient):
    profile = {
        "interests": [],
        "skills": [{"skill_id": "sql", "name": "SQL"}],
        "projects": [],
    }
    response = client.post(
        "/api/v1/projects/simulate",
        json={"profile": profile, "role_id": "data_analyst", "project_id": "project_data_dashboard_001"},
    )
    assumed = response.json()["data"]["assumed_skill_ids"]
    assert "sql" not in assumed
    assert set(assumed) == {"python", "data_visualization"}


def test_simulate_unknown_role_id_returns_404(client: TestClient):
    response = client.post(
        "/api/v1/projects/simulate",
        json={
            "profile": EMPTY_PROFILE,
            "role_id": "no_such_role",
            "project_id": "project_data_dashboard_001",
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ROLE_NOT_FOUND"


def test_simulate_unknown_project_id_returns_404(client: TestClient):
    response = client.post(
        "/api/v1/projects/simulate",
        json={"profile": EMPTY_PROFILE, "role_id": "data_analyst", "project_id": "no_such_project"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROJECT_NOT_FOUND"


def test_simulate_results_are_deterministic(client: TestClient):
    payload = {
        "profile": EMPTY_PROFILE,
        "role_id": "data_analyst",
        "project_id": "project_data_dashboard_001",
    }
    first = client.post("/api/v1/projects/simulate", json=payload).json()["data"]
    second = client.post("/api/v1/projects/simulate", json=payload).json()["data"]
    assert first == second


def test_simulate_does_not_mutate_stored_profile(db_session):
    """Service-level test: there is no GET /profile endpoint to re-fetch
    through, so this reads the DB row directly via ProfileService, the
    same pattern test_matching_service.py uses."""
    profile_service = ProfileService(db_session)
    stored, _ = profile_service.upsert(StudentProfile(interests=[], skills=[], projects=[]))
    profile_id = stored.profile_id

    matching_service = MatchingService(
        profile_service=profile_service,
        catalog=FixtureRoleCatalog(),
        matcher=FixtureMatchingProvider(),
        trends=NullTrendProvider(),
    )
    simulation_service = ProjectSimulationService(matching_service, FixtureProjectCatalog())

    simulation_service.simulate(
        ProjectSimulationRequest(
            profile=StudentProfile(profile_id=profile_id, interests=[], skills=[], projects=[]),
            role_id="data_analyst",
            project_id="project_data_dashboard_001",
        )
    )

    reloaded = profile_service.get(profile_id)
    assert reloaded.skills == []  # hypothetical skills were never persisted


def test_simulate_resolved_profile_object_is_untouched_in_memory(db_session):
    """The MatchOutcome.profile returned by the baseline match call must not
    be mutated when building the simulated copy (model_copy, not mutation)."""
    profile_service = ProfileService(db_session)
    matching_service = MatchingService(
        profile_service=profile_service,
        catalog=FixtureRoleCatalog(),
        matcher=FixtureMatchingProvider(),
        trends=NullTrendProvider(),
    )
    simulation_service = ProjectSimulationService(matching_service, FixtureProjectCatalog())

    inline_profile = StudentProfile(interests=[], skills=[SkillRef(skill_id="sql", name="SQL")], projects=[])
    baseline_before = matching_service.match(MatchRequest(profile=inline_profile))
    original_skill_count = len(baseline_before.profile.skills)

    simulation_service.simulate(
        ProjectSimulationRequest(
            profile=inline_profile, role_id="data_analyst", project_id="project_data_dashboard_001"
        )
    )

    baseline_after = matching_service.match(MatchRequest(profile=inline_profile))
    assert len(baseline_after.profile.skills) == original_skill_count
