"""Milestone 7B, section 5: automated checks that FRONTEND_HANDOFF.md's
documented examples and claims actually agree with the implementation.
The request bodies below are copied verbatim from the handoff doc (kept
in sync by hand) — if either drifts, these tests catch it.
"""
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.matching import MatchRequest
from app.schemas.profile import StudentProfile
from app.schemas.projects import ProjectSimulationRequest
from app.schemas.roadmaps import RoleProfileRequest
from app.schemas.scenarios import ScenarioRequest

# Exact example from FRONTEND_HANDOFF.md's "POST /profile/analyze" section.
HANDOFF_PROFILE_EXAMPLE = {
    "education_level": "undergraduate",
    "degree": "Computer Science",
    "semester": 4,
    "interests": ["analytics", "data engineering"],
    "skills": [
        {"skill_id": "sql", "name": "SQL", "proficiency": "intermediate"},
        {"skill_id": "python", "name": "Python", "proficiency": "intermediate"},
    ],
    "projects": ["Fictional course project: sales dashboard with SQL + Python"],
    "experience_summary": "Fictional demo profile for contract/testing purposes only.",
}

MVP_ENDPOINTS = (
    "/api/v1/health",
    "/api/v1/profile/analyze",
    "/api/v1/careers/match",
    "/api/v1/trends",
    "/api/v1/scenarios/simulate",
    "/api/v1/roadmaps/generate",
    "/api/v1/projects/recommend",
    "/api/v1/projects/simulate",
    "/api/v1/sdgs/{role_id}",
)

ENVELOPE_RESPONSE_ENDPOINTS = (
    "/api/v1/profile/analyze",
    "/api/v1/careers/match",
    "/api/v1/trends",
    "/api/v1/scenarios/simulate",
    "/api/v1/roadmaps/generate",
    "/api/v1/projects/recommend",
    "/api/v1/projects/simulate",
    "/api/v1/sdgs/{role_id}",
)


def test_openapi_includes_every_documented_mvp_endpoint():
    schema = app.openapi()
    for path in MVP_ENDPOINTS:
        assert path in schema["paths"], f"{path} missing from OpenAPI"


def test_envelope_responses_have_stable_required_fields(client: TestClient):
    """Every non-health MVP response must carry exactly the contract's
    envelope keys: data, data_mode, generated_at, warnings."""
    profile_id = client.post("/api/v1/profile/analyze", json=HANDOFF_PROFILE_EXAMPLE).json()["data"][
        "profile_id"
    ]
    profile_ref = {"profile_id": profile_id, "interests": [], "skills": [], "projects": []}

    responses = {
        "/api/v1/profile/analyze": client.post(
            "/api/v1/profile/analyze", json=HANDOFF_PROFILE_EXAMPLE
        ),
        "/api/v1/careers/match": client.post(
            "/api/v1/careers/match", json={"profile": profile_ref}
        ),
        "/api/v1/trends": client.get("/api/v1/trends", params={"role_id": "data_analyst"}),
        "/api/v1/scenarios/simulate": client.post(
            "/api/v1/scenarios/simulate", json={"profile": profile_ref, "scenario_id": "moderate"}
        ),
        "/api/v1/roadmaps/generate": client.post(
            "/api/v1/roadmaps/generate", json={"profile": profile_ref, "role_id": "data_analyst"}
        ),
        "/api/v1/projects/recommend": client.post(
            "/api/v1/projects/recommend", json={"profile": profile_ref, "role_id": "data_analyst"}
        ),
        "/api/v1/projects/simulate": client.post(
            "/api/v1/projects/simulate",
            json={
                "profile": profile_ref,
                "role_id": "data_analyst",
                "project_id": "project_data_dashboard_001",
            },
        ),
        "/api/v1/sdgs/{role_id}": client.get("/api/v1/sdgs/data_analyst"),
    }

    for path, response in responses.items():
        assert response.status_code == 200, f"{path} -> {response.status_code}"
        body = response.json()
        assert set(body.keys()) == {"data", "data_mode", "generated_at", "warnings"}, path


def test_only_profile_analyze_uses_live_data_mode_everything_else_is_fixture(client: TestClient):
    """Matches the handoff doc's explicit claim: data_mode is "live" only
    for /profile/analyze; every other implemented route is "fixture"."""
    profile_id = client.post("/api/v1/profile/analyze", json=HANDOFF_PROFILE_EXAMPLE).json()["data"][
        "profile_id"
    ]
    profile_ref = {"profile_id": profile_id, "interests": [], "skills": [], "projects": []}

    analyze_body = client.post("/api/v1/profile/analyze", json=HANDOFF_PROFILE_EXAMPLE).json()
    assert analyze_body["data_mode"] == "live"

    fixture_checks = {
        "/api/v1/careers/match": client.post("/api/v1/careers/match", json={"profile": profile_ref}),
        "/api/v1/trends": client.get("/api/v1/trends", params={"role_id": "data_analyst"}),
        "/api/v1/scenarios/simulate": client.post(
            "/api/v1/scenarios/simulate", json={"profile": profile_ref, "scenario_id": "moderate"}
        ),
        "/api/v1/roadmaps/generate": client.post(
            "/api/v1/roadmaps/generate", json={"profile": profile_ref, "role_id": "data_analyst"}
        ),
        "/api/v1/projects/recommend": client.post(
            "/api/v1/projects/recommend", json={"profile": profile_ref, "role_id": "data_analyst"}
        ),
        "/api/v1/sdgs/{role_id}": client.get("/api/v1/sdgs/data_analyst"),
    }
    for path, response in fixture_checks.items():
        assert response.json()["data_mode"] == "fixture", path


def test_handoff_profile_example_validates_against_the_real_schema():
    StudentProfile.model_validate(HANDOFF_PROFILE_EXAMPLE)


def test_handoff_profile_example_succeeds_via_the_real_endpoint(client: TestClient):
    response = client.post("/api/v1/profile/analyze", json=HANDOFF_PROFILE_EXAMPLE)
    assert response.status_code == 200


def test_handoff_profile_ref_pattern_validates_against_every_consuming_schema():
    """The {"profile_id": ..., "interests": [], "skills": [], "projects": []}
    pattern the handoff doc tells Mohammad to reuse on every call must be
    valid input for each schema that embeds StudentProfile."""
    profile_ref = {"profile_id": "profile_example", "interests": [], "skills": [], "projects": []}

    MatchRequest.model_validate({"profile": profile_ref})
    ScenarioRequest.model_validate({"profile": profile_ref, "scenario_id": "moderate"})
    RoleProfileRequest.model_validate({"profile": profile_ref, "role_id": "data_analyst"})
    ProjectSimulationRequest.model_validate(
        {"profile": profile_ref, "role_id": "data_analyst", "project_id": "project_data_dashboard_001"}
    )
