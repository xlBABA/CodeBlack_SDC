"""Milestone 7B: end-to-end integration tests for the complete synthetic
student journey across every implemented MVP route, plus cross-endpoint
failure-case coverage.

Focuses on data flowing correctly BETWEEN endpoints — profile_id/role_id
continuity, determinism, absence of cross-profile contamination, and
consistent data_mode/error-envelope behavior across the whole flow — not
re-verifying per-endpoint business logic already covered by existing unit
tests (test_matching_provider.py, test_roadmaps.py, test_sdgs.py, etc.).

All profile data below is fictional/synthetic (same shape as
app/fixtures/sample_profiles.py; repeated here as literal request bodies
since the contract requires exact field names, not a Python import).
"""
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app
from app.services.profile_service import ProfileService

SYNTHETIC_PROFILE = {
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

SECOND_SYNTHETIC_PROFILE = {
    "education_level": "undergraduate",
    "degree": "Business Administration",
    "semester": 6,
    "interests": ["fintech", "financial analysis"],
    "skills": [
        {"skill_id": "excel", "name": "Excel", "proficiency": "advanced"},
        {"skill_id": "accounting", "name": "Accounting", "proficiency": "beginner"},
    ],
    "projects": ["Fictional case study: budget forecasting model"],
    "experience_summary": "Fictional demo profile for contract/testing purposes only.",
}

# Chosen because it has >=1 missing skill with a placeholder resource
# (data_visualization), a tied project, a trend signal, and an SDG mapping
# — every step of the journey below is meaningfully non-empty for it.
ROLE_ID = "data_analyst"
PROJECT_ID = "project_data_dashboard_001"

# Deliberately affirmative-only phrasings, not bare nouns like "hiring
# probability" — the real explanation/caveat text in matching_provider.py
# legitimately says "not a hiring probability" (a disclaimer), which a
# bare substring check would wrongly flag. Same class of false positive
# fixed in Milestone 5's SDG certification test.
_FORBIDDEN_HIRING_PHRASES = (
    "is a hiring probability",
    "guaranteed job",
    "will be hired",
    "chance of getting hired",
    "job offer guarantee",
    "guarantees employment",
)


def _assert_no_hiring_probability_language(payload_text: str) -> None:
    lowered = payload_text.lower()
    for phrase in _FORBIDDEN_HIRING_PHRASES:
        assert phrase not in lowered, f"found forbidden phrase: {phrase!r}"


def _profile_ref(profile_id: str) -> dict:
    """A minimal StudentProfile body carrying only profile_id. Per
    MatchingService._resolve_profile, a known profile_id makes the backend
    load the stored profile and ignore these placeholder empty fields —
    this is how profile_id continuity is exercised across every route
    below."""
    return {"profile_id": profile_id, "interests": [], "skills": [], "projects": []}


# --- 1-9: the full synthetic student journey --------------------------------


def test_full_synthetic_student_journey_for_data_analyst(client: TestClient, db_session):
    # 1. Submit synthetic profile.
    analyze_response = client.post("/api/v1/profile/analyze", json=SYNTHETIC_PROFILE)
    assert analyze_response.status_code == 200
    analyze_body = analyze_response.json()
    assert analyze_body["data_mode"] == "live"  # real persistence, not a fixture
    profile_id = analyze_body["data"]["profile_id"]
    assert profile_id.startswith("profile_")
    _assert_no_hiring_probability_language(analyze_response.text)

    # 2. Career matches using the returned profile_id.
    match_response = client.post("/api/v1/careers/match", json={"profile": _profile_ref(profile_id)})
    assert match_response.status_code == 200
    match_body = match_response.json()
    assert match_body["data_mode"] == "fixture"
    matches = match_body["data"]["matches"]
    assert matches
    assert ROLE_ID in {m["role_id"] for m in matches}
    data_analyst_match = next(m for m in matches if m["role_id"] == ROLE_ID)
    assert data_analyst_match["score_type"] == "profile_alignment_estimate"
    assert {s["skill_id"] for s in data_analyst_match["matched_skills"]} == {"sql", "python"}
    assert {s["skill_id"] for s in data_analyst_match["missing_skills"]} == {
        "data_visualization",
        "statistics",
    }
    _assert_no_hiring_probability_language(match_response.text)

    # 3. Role selected: ROLE_ID — confirmed present in the real returned
    # matches above, not assumed.

    # 4. Trends for the selected role.
    trends_response = client.get("/api/v1/trends", params={"role_id": ROLE_ID})
    assert trends_response.status_code == 200
    trends_body = trends_response.json()
    assert trends_body["data_mode"] == "fixture"
    assert trends_body["data"]["signals"]
    assert all(ROLE_ID in s["role_ids"] for s in trends_body["data"]["signals"])

    # 5. Scenario simulation — moderate and fast — same profile_id; scores
    # identical to the baseline match (no validated scenario-scoring model
    # exists yet — only the qualitative assumptions differ).
    scenario_results = {}
    for scenario_id in ("moderate", "fast"):
        response = client.post(
            "/api/v1/scenarios/simulate",
            json={"profile": _profile_ref(profile_id), "scenario_id": scenario_id},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data_mode"] == "fixture"
        assert body["data"]["scenario_id"] == scenario_id
        assert body["data"]["assumptions"]
        assert body["data"]["uncertainty_note"]
        scenario_results[scenario_id] = body["data"]
        _assert_no_hiring_probability_language(response.text)

    assert scenario_results["moderate"]["assumptions"] != scenario_results["fast"]["assumptions"]
    moderate_role = next(m for m in scenario_results["moderate"]["matches"] if m["role_id"] == ROLE_ID)
    fast_role = next(m for m in scenario_results["fast"]["matches"] if m["role_id"] == ROLE_ID)
    assert moderate_role["score"] == fast_role["score"] == data_analyst_match["score"]

    # 6. Learning roadmap for the selected role.
    roadmap_response = client.post(
        "/api/v1/roadmaps/generate", json={"profile": _profile_ref(profile_id), "role_id": ROLE_ID}
    )
    assert roadmap_response.status_code == 200
    roadmap_body = roadmap_response.json()
    assert roadmap_body["data_mode"] == "fixture"
    steps = roadmap_body["data"]["steps"]
    assert steps  # data_visualization has a placeholder resource; statistics doesn't
    assert {s["skill_id"] for s in steps} == {"data_visualization"}
    assert roadmap_body["data"]["total_estimated_hours"] > 0

    # 7. Project recommendations for the selected role.
    recommend_response = client.post(
        "/api/v1/projects/recommend", json={"profile": _profile_ref(profile_id), "role_id": ROLE_ID}
    )
    assert recommend_response.status_code == 200
    recommend_body = recommend_response.json()
    assert recommend_body["data_mode"] == "fixture"
    recommended_projects = recommend_body["data"]["projects"]
    assert recommended_projects
    assert any(p["project_id"] == PROJECT_ID for p in recommended_projects)

    # 8. Simulate the recommended project.
    simulate_response = client.post(
        "/api/v1/projects/simulate",
        json={"profile": _profile_ref(profile_id), "role_id": ROLE_ID, "project_id": PROJECT_ID},
    )
    assert simulate_response.status_code == 200
    simulate_body = simulate_response.json()["data"]
    assert simulate_body["simulated_score"] > simulate_body["baseline_score"]
    assert "data_visualization" in simulate_body["assumed_skill_ids"]
    assert "sql" not in simulate_body["assumed_skill_ids"]  # already held, not double counted
    assert "not" in simulate_body["disclaimer"].lower()
    _assert_no_hiring_probability_language(simulate_response.text)

    # 9. SDG mappings for the selected role.
    sdg_response = client.get(f"/api/v1/sdgs/{ROLE_ID}")
    assert sdg_response.status_code == 200
    sdg_body = sdg_response.json()
    assert sdg_body["data_mode"] == "fixture"
    assert sdg_body["data"]["role_sdg_mappings"]
    assert sdg_body["data"]["skill_sdg_mappings"]

    # Cross-cutting: the hypothetical project simulation above must never
    # have touched the persisted profile row (same isolated test DB,
    # verified directly rather than inferred from another HTTP response).
    stored = ProfileService(db_session).get(profile_id)
    assert {s.skill_id for s in stored.skills} == {"sql", "python"}


def test_journey_is_deterministic_across_repeated_calls(client: TestClient):
    profile_id = client.post("/api/v1/profile/analyze", json=SYNTHETIC_PROFILE).json()["data"]["profile_id"]

    first_match = client.post("/api/v1/careers/match", json={"profile": _profile_ref(profile_id)}).json()
    second_match = client.post("/api/v1/careers/match", json={"profile": _profile_ref(profile_id)}).json()
    assert first_match["data"]["matches"] == second_match["data"]["matches"]

    first_roadmap = client.post(
        "/api/v1/roadmaps/generate", json={"profile": _profile_ref(profile_id), "role_id": ROLE_ID}
    ).json()
    second_roadmap = client.post(
        "/api/v1/roadmaps/generate", json={"profile": _profile_ref(profile_id), "role_id": ROLE_ID}
    ).json()
    assert first_roadmap["data"] == second_roadmap["data"]


def test_two_profiles_do_not_contaminate_each_others_results(client: TestClient):
    profile_a = client.post("/api/v1/profile/analyze", json=SYNTHETIC_PROFILE).json()["data"]["profile_id"]
    profile_b = client.post(
        "/api/v1/profile/analyze", json=SECOND_SYNTHETIC_PROFILE
    ).json()["data"]["profile_id"]
    assert profile_a != profile_b

    match_a = client.post("/api/v1/careers/match", json={"profile": _profile_ref(profile_a)}).json()
    match_b = client.post("/api/v1/careers/match", json={"profile": _profile_ref(profile_b)}).json()

    data_analyst_a = next(m for m in match_a["data"]["matches"] if m["role_id"] == ROLE_ID)
    data_analyst_b = next(m for m in match_b["data"]["matches"] if m["role_id"] == ROLE_ID)

    assert {s["skill_id"] for s in data_analyst_a["matched_skills"]} == {"sql", "python"}
    assert {s["skill_id"] for s in data_analyst_b["matched_skills"]} == set()
    assert data_analyst_a["score"] != data_analyst_b["score"]


# --- Failure cases -----------------------------------------------------------


def test_unknown_profile_id_returns_404_across_profile_dependent_routes(client: TestClient):
    bad_ref = _profile_ref("profile_does_not_exist")

    match_response = client.post("/api/v1/careers/match", json={"profile": bad_ref})
    assert match_response.status_code == 404
    assert match_response.json()["error"]["code"] == "PROFILE_NOT_FOUND"

    roadmap_response = client.post(
        "/api/v1/roadmaps/generate", json={"profile": bad_ref, "role_id": ROLE_ID}
    )
    assert roadmap_response.status_code == 404
    assert roadmap_response.json()["error"]["code"] == "PROFILE_NOT_FOUND"


def test_unknown_role_id_handling_differs_by_route_as_designed(client: TestClient):
    """Discovery/listing routes (roadmaps, sdgs) return an honest empty 200
    for an unknown role; /projects/simulate needs one specific existing
    role to proceed, so it 404s — a deliberate, documented distinction."""
    profile_id = client.post("/api/v1/profile/analyze", json=SYNTHETIC_PROFILE).json()["data"]["profile_id"]
    bad_role = "role_does_not_exist"

    roadmap_response = client.post(
        "/api/v1/roadmaps/generate", json={"profile": _profile_ref(profile_id), "role_id": bad_role}
    )
    assert roadmap_response.status_code == 200
    assert roadmap_response.json()["data"]["steps"] == []

    sdg_response = client.get(f"/api/v1/sdgs/{bad_role}")
    assert sdg_response.status_code == 200
    assert sdg_response.json()["data"]["role_sdg_mappings"] == []

    simulate_response = client.post(
        "/api/v1/projects/simulate",
        json={"profile": _profile_ref(profile_id), "role_id": bad_role, "project_id": PROJECT_ID},
    )
    assert simulate_response.status_code == 404
    assert simulate_response.json()["error"]["code"] == "ROLE_NOT_FOUND"


def test_unknown_project_id_returns_404(client: TestClient):
    profile_id = client.post("/api/v1/profile/analyze", json=SYNTHETIC_PROFILE).json()["data"]["profile_id"]
    response = client.post(
        "/api/v1/projects/simulate",
        json={
            "profile": _profile_ref(profile_id),
            "role_id": ROLE_ID,
            "project_id": "project_does_not_exist",
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROJECT_NOT_FOUND"


def test_invalid_request_payload_returns_422_contract_error(client: TestClient):
    response = client.post(
        "/api/v1/careers/match", json={"profile": {"interests": [], "projects": []}}  # missing "skills"
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in body


def test_missing_and_invalid_limits_are_rejected(client: TestClient):
    profile_id = client.post("/api/v1/profile/analyze", json=SYNTHETIC_PROFILE).json()["data"]["profile_id"]

    over_match_limit = client.post(
        "/api/v1/careers/match", json={"profile": _profile_ref(profile_id), "limit": 7}
    )
    assert over_match_limit.status_code == 422

    zero_match_limit = client.post(
        "/api/v1/careers/match", json={"profile": _profile_ref(profile_id), "limit": 0}
    )
    assert zero_match_limit.status_code == 422

    over_project_limit = client.post(
        "/api/v1/projects/recommend",
        json={"profile": _profile_ref(profile_id), "role_id": ROLE_ID, "limit": 11},
    )
    assert over_project_limit.status_code == 422


def test_enable_fixtures_false_blocks_matching_routes_but_not_role_or_profile_independent_routes(
    client: TestClient,
):
    profile_id = client.post("/api/v1/profile/analyze", json=SYNTHETIC_PROFILE).json()["data"]["profile_id"]

    app.dependency_overrides[get_settings] = lambda: Settings(ENABLE_FIXTURES=False, _env_file=None)
    try:
        matching_routes = [
            ("post", "/api/v1/careers/match", {"profile": _profile_ref(profile_id)}),
            (
                "post",
                "/api/v1/scenarios/simulate",
                {"profile": _profile_ref(profile_id), "scenario_id": "moderate"},
            ),
            (
                "post",
                "/api/v1/roadmaps/generate",
                {"profile": _profile_ref(profile_id), "role_id": ROLE_ID},
            ),
            (
                "post",
                "/api/v1/projects/recommend",
                {"profile": _profile_ref(profile_id), "role_id": ROLE_ID},
            ),
            (
                "post",
                "/api/v1/projects/simulate",
                {"profile": _profile_ref(profile_id), "role_id": ROLE_ID, "project_id": PROJECT_ID},
            ),
        ]
        for method, path, body in matching_routes:
            response = getattr(client, method)(path, json=body)
            assert response.status_code == 503, f"{path} should be 503 under ENABLE_FIXTURES=False"
            assert response.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"

        # These never go through get_matching_provider — unaffected.
        assert client.get("/api/v1/trends", params={"role_id": ROLE_ID}).status_code == 200
        assert client.get(f"/api/v1/sdgs/{ROLE_ID}").status_code == 200
        assert client.post("/api/v1/profile/analyze", json=SYNTHETIC_PROFILE).status_code == 200
    finally:
        del app.dependency_overrides[get_settings]


def test_cors_allows_configured_local_frontend_origin_on_a_journey_endpoint(client: TestClient):
    response = client.post(
        "/api/v1/careers/match",
        json={"profile": SYNTHETIC_PROFILE},
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
