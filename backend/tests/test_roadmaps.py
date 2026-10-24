from fastapi.testclient import TestClient

from app.api.v1.endpoints.roadmaps import get_resource_catalog
from app.main import app

PROFILE_NO_SKILLS = {"interests": [], "skills": [], "projects": []}


def test_openapi_includes_roadmaps_generate():
    schema = app.openapi()
    assert "/api/v1/roadmaps/generate" in schema["paths"]
    assert "post" in schema["paths"]["/api/v1/roadmaps/generate"]


def test_roadmap_steps_cover_missing_skills_with_resources(client: TestClient):
    response = client.post(
        "/api/v1/roadmaps/generate",
        json={"profile": PROFILE_NO_SKILLS, "role_id": "data_analyst"},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["data_mode"] == "fixture"
    steps = body["data"]["steps"]
    # data_analyst requires sql, python, data_visualization, statistics;
    # only the first three have placeholder resources — "statistics" is an
    # honest gap, not a fabricated step.
    step_skill_ids = {s["skill_id"] for s in steps}
    assert step_skill_ids == {"sql", "python", "data_visualization"}
    assert "statistics" not in step_skill_ids
    assert any("Statistics" in w for w in body["warnings"])


def test_roadmap_steps_ordered_by_role_weight_descending(client: TestClient):
    response = client.post(
        "/api/v1/roadmaps/generate",
        json={"profile": PROFILE_NO_SKILLS, "role_id": "data_analyst"},
    )
    steps = response.json()["data"]["steps"]
    # data_analyst weights: sql=1.0, python=1.0, data_visualization=0.8 ->
    # sql/python tie at the top (skill_id ascending tiebreak), then data_visualization.
    assert [s["skill_id"] for s in steps] == ["python", "sql", "data_visualization"]


def test_roadmap_total_hours_matches_sum_of_steps(client: TestClient):
    response = client.post(
        "/api/v1/roadmaps/generate",
        json={"profile": PROFILE_NO_SKILLS, "role_id": "data_analyst"},
    )
    data = response.json()["data"]
    assert data["total_estimated_hours"] == sum(s["estimated_hours"] for s in data["steps"])


def test_roadmap_reasons_explain_which_skill_each_step_addresses(client: TestClient):
    response = client.post(
        "/api/v1/roadmaps/generate",
        json={"profile": PROFILE_NO_SKILLS, "role_id": "data_analyst"},
    )
    for step in response.json()["data"]["steps"]:
        assert step["skill_id"] in step["reason"] or "Closes a missing skill" in step["reason"]


def test_roadmap_budget_limit_produces_informational_warning(client: TestClient):
    response = client.post(
        "/api/v1/roadmaps/generate",
        json={"profile": PROFILE_NO_SKILLS, "role_id": "data_analyst", "budget_limit": 50},
    )
    assert any("budget limit" in w.lower() for w in response.json()["warnings"])


def test_roadmap_hours_per_week_produces_weeks_estimate_warning(client: TestClient):
    response = client.post(
        "/api/v1/roadmaps/generate",
        json={"profile": PROFILE_NO_SKILLS, "role_id": "data_analyst", "hours_per_week": 5},
    )
    assert any("week" in w.lower() for w in response.json()["warnings"])


def test_roadmap_already_skilled_profile_has_fewer_steps(client: TestClient):
    profile = {
        "interests": [],
        "skills": [
            {"skill_id": "sql", "name": "SQL"},
            {"skill_id": "python", "name": "Python"},
            {"skill_id": "data_visualization", "name": "Data Visualization"},
        ],
        "projects": [],
    }
    response = client.post(
        "/api/v1/roadmaps/generate", json={"profile": profile, "role_id": "data_analyst"}
    )
    assert response.json()["data"]["steps"] == []


def test_roadmap_unknown_role_id_returns_honest_empty_response(client: TestClient):
    response = client.post(
        "/api/v1/roadmaps/generate",
        json={"profile": PROFILE_NO_SKILLS, "role_id": "no_such_role"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["steps"] == []
    assert data["total_estimated_hours"] == 0


def test_roadmap_results_are_deterministic(client: TestClient):
    payload = {"profile": PROFILE_NO_SKILLS, "role_id": "data_analyst"}
    first = client.post("/api/v1/roadmaps/generate", json=payload).json()["data"]
    second = client.post("/api/v1/roadmaps/generate", json=payload).json()["data"]
    assert first == second


def test_resource_catalog_dependency_is_overridable(client: TestClient):
    class EmptyResourceCatalog:
        def list_resources(self):
            return []

    app.dependency_overrides[get_resource_catalog] = lambda: EmptyResourceCatalog()
    try:
        response = client.post(
            "/api/v1/roadmaps/generate",
            json={"profile": PROFILE_NO_SKILLS, "role_id": "data_analyst"},
        )
    finally:
        del app.dependency_overrides[get_resource_catalog]

    assert response.json()["data"]["steps"] == []
