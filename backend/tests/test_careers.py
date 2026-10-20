from fastapi.testclient import TestClient

from app.api.v1.endpoints.careers import get_matching_provider
from app.main import app

SAMPLE_REQUEST = {
    "profile": {
        "education_level": "undergraduate",
        "degree": "Computer Science",
        "semester": 4,
        "interests": ["analytics"],
        "skills": [{"skill_id": "sql", "name": "SQL"}, {"skill_id": "python", "name": "Python"}],
        "projects": [],
    },
    "limit": 6,
    "scenario_id": "moderate",
}


def test_openapi_includes_careers_match():
    schema = app.openapi()
    assert "/api/v1/careers/match" in schema["paths"]
    assert "post" in schema["paths"]["/api/v1/careers/match"]


def test_match_careers_inline_profile_returns_contract_shape(client: TestClient):
    response = client.post("/api/v1/careers/match", json=SAMPLE_REQUEST)
    assert response.status_code == 200

    body = response.json()
    assert body["data_mode"] == "fixture"
    assert isinstance(body["warnings"], list) and body["warnings"]

    payload = body["data"]
    assert payload["methodology_version"] == "v1"
    assert payload["catalog_coverage"] == {"verified": 4, "total_target": 30}

    matches = payload["matches"]
    assert 1 <= len(matches) <= 6
    scores = [m["score"] for m in matches]
    assert scores == sorted(scores, reverse=True)
    for match in matches:
        assert match["score_type"] == "profile_alignment_estimate"
        assert "hiring" in " ".join(match["caveats"]).lower()


def test_match_careers_with_profile_id_resolves_stored_profile(client: TestClient):
    created = client.post(
        "/api/v1/profile/analyze",
        json={
            "interests": [],
            "skills": [{"skill_id": "sql", "name": "SQL"}],
            "projects": [],
        },
    ).json()
    profile_id = created["data"]["profile_id"]

    response = client.post(
        "/api/v1/careers/match",
        json={"profile": {"profile_id": profile_id, "interests": [], "skills": [], "projects": []}},
    )
    assert response.status_code == 200

    matches = response.json()["data"]["matches"]
    data_analyst = next(m for m in matches if m["role_id"] == "data_analyst")
    assert any(s["skill_id"] == "sql" for s in data_analyst["matched_skills"])


def test_match_careers_unknown_profile_id_returns_404(client: TestClient):
    response = client.post(
        "/api/v1/careers/match",
        json={"profile": {"profile_id": "profile_missing", "interests": [], "skills": [], "projects": []}},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROFILE_NOT_FOUND"


def test_match_careers_limit_enforced(client: TestClient):
    payload = dict(SAMPLE_REQUEST)
    payload["limit"] = 2
    response = client.post("/api/v1/careers/match", json=payload)
    assert response.status_code == 200
    assert len(response.json()["data"]["matches"]) == 2


def test_match_careers_invalid_limit_returns_422(client: TestClient):
    payload = dict(SAMPLE_REQUEST)
    payload["limit"] = 7  # contract maximum is 6
    response = client.post("/api/v1/careers/match", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_match_careers_invalid_scenario_returns_422(client: TestClient):
    payload = dict(SAMPLE_REQUEST)
    payload["scenario_id"] = "super_fast"
    response = client.post("/api/v1/careers/match", json=payload)
    assert response.status_code == 422


def test_matching_provider_dependency_is_overridable(client: TestClient):
    """Section E requirement: a stub provider can replace the fixture default."""

    class StubMatchingProvider:
        def match(self, profile, roles, scenario, signals):
            from app.schemas.matching import RoleMatch, ScoreBreakdown

            return [
                RoleMatch(
                    role_id="stub_role",
                    role_title="Stub Role",
                    score=99.9,
                    score_breakdown=ScoreBreakdown(
                        skills=100, experience=100, prerequisites=100, transferable=100
                    ),
                    explanation="Stub explanation for override test.",
                    caveats=["Stub caveat"],
                )
            ]

    app.dependency_overrides[get_matching_provider] = lambda: StubMatchingProvider()
    try:
        response = client.post("/api/v1/careers/match", json=SAMPLE_REQUEST)
    finally:
        del app.dependency_overrides[get_matching_provider]

    assert response.status_code == 200
    matches = response.json()["data"]["matches"]
    assert len(matches) == 1
    assert matches[0]["role_id"] == "stub_role"
