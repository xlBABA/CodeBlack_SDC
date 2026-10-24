import re

from fastapi.testclient import TestClient

from app.api.v1.endpoints.scenarios import get_scenario_assumptions
from app.fixtures.sample_profiles import SAMPLE_PROFILES
from app.main import app

PROFILE = SAMPLE_PROFILES["cs_undergrad_data"].model_dump(exclude_none=True)
_DIGIT_RE = re.compile(r"\d")


def test_openapi_includes_scenarios_simulate():
    schema = app.openapi()
    assert "/api/v1/scenarios/simulate" in schema["paths"]
    assert "post" in schema["paths"]["/api/v1/scenarios/simulate"]


def test_moderate_scenario_returns_contract_shape(client: TestClient):
    response = client.post(
        "/api/v1/scenarios/simulate", json={"profile": PROFILE, "scenario_id": "moderate"}
    )
    assert response.status_code == 200

    body = response.json()
    assert body["data_mode"] == "fixture"
    payload = body["data"]
    assert payload["scenario_id"] == "moderate"
    assert isinstance(payload["assumptions"], list) and payload["assumptions"]
    assert isinstance(payload["uncertainty_note"], str) and payload["uncertainty_note"]
    assert isinstance(payload["matches"], list) and payload["matches"]


def test_fast_scenario_returns_contract_shape(client: TestClient):
    response = client.post(
        "/api/v1/scenarios/simulate", json={"profile": PROFILE, "scenario_id": "fast"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["scenario_id"] == "fast"


def test_moderate_and_fast_assumptions_are_meaningfully_different(client: TestClient):
    moderate = client.post(
        "/api/v1/scenarios/simulate", json={"profile": PROFILE, "scenario_id": "moderate"}
    ).json()["data"]
    fast = client.post(
        "/api/v1/scenarios/simulate", json={"profile": PROFILE, "scenario_id": "fast"}
    ).json()["data"]

    assert moderate["assumptions"] != fast["assumptions"]


def test_scenario_does_not_change_matching_scores(client: TestClient):
    baseline = client.post("/api/v1/careers/match", json={"profile": PROFILE}).json()
    baseline_scores = {m["role_id"]: m["score"] for m in baseline["data"]["matches"]}

    for scenario_id in ("moderate", "fast"):
        scenario = client.post(
            "/api/v1/scenarios/simulate", json={"profile": PROFILE, "scenario_id": scenario_id}
        ).json()
        scenario_scores = {m["role_id"]: m["score"] for m in scenario["data"]["matches"]}
        assert scenario_scores == baseline_scores


def test_scenario_results_are_deterministic(client: TestClient):
    first = client.post(
        "/api/v1/scenarios/simulate", json={"profile": PROFILE, "scenario_id": "fast"}
    ).json()
    second = client.post(
        "/api/v1/scenarios/simulate", json={"profile": PROFILE, "scenario_id": "fast"}
    ).json()

    assert first["data"] == second["data"]


def test_invalid_scenario_id_returns_422(client: TestClient):
    response = client.post(
        "/api/v1/scenarios/simulate", json={"profile": PROFILE, "scenario_id": "super_fast"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_missing_scenario_id_returns_422(client: TestClient):
    response = client.post("/api/v1/scenarios/simulate", json={"profile": PROFILE})
    assert response.status_code == 422


def test_match_scores_within_numeric_bounds(client: TestClient):
    response = client.post(
        "/api/v1/scenarios/simulate", json={"profile": PROFILE, "scenario_id": "moderate"}
    )
    for match in response.json()["data"]["matches"]:
        assert 0 <= match["score"] <= 100
        for value in match["score_breakdown"].values():
            assert 0 <= value <= 100


def test_assumptions_and_uncertainty_note_are_qualitative_not_numeric(client: TestClient):
    response = client.post(
        "/api/v1/scenarios/simulate", json={"profile": PROFILE, "scenario_id": "fast"}
    )
    payload = response.json()["data"]

    assert not _DIGIT_RE.search(payload["uncertainty_note"])
    for assumption in payload["assumptions"]:
        assert not _DIGIT_RE.search(assumption)
    assert "not a labor-market forecast" in payload["uncertainty_note"].lower()


def test_unknown_profile_id_returns_404(client: TestClient):
    response = client.post(
        "/api/v1/scenarios/simulate",
        json={
            "profile": {"profile_id": "profile_missing", "interests": [], "skills": [], "projects": []},
            "scenario_id": "moderate",
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROFILE_NOT_FOUND"


def test_scenario_assumptions_dependency_is_overridable(client: TestClient):
    class StubAssumptions:
        def assumptions_for(self, scenario_id):
            return ["stub assumption"]

        def uncertainty_note(self):
            return "stub uncertainty note"

    app.dependency_overrides[get_scenario_assumptions] = lambda: StubAssumptions()
    try:
        response = client.post(
            "/api/v1/scenarios/simulate", json={"profile": PROFILE, "scenario_id": "moderate"}
        )
    finally:
        del app.dependency_overrides[get_scenario_assumptions]

    payload = response.json()["data"]
    assert payload["assumptions"] == ["stub assumption"]
    assert payload["uncertainty_note"] == "stub uncertainty note"
