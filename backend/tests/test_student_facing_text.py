"""Student-facing warnings never expose internal configuration, file paths
or teammate names (cached catalog + Hussain's matcher, the release setup)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app
from tests.test_cv_parse import VALID_PDF, _post_cv

FORBIDDEN = (
    "CATALOG_MODE", "MATCHING_MODE", "ENABLE_FIXTURES", "Jawad", "Hussain", "placeholder",
    "RunPod API key is not configured", "app/data", ".json", "role_id",
)
PROFILE = {
    "interests": [],
    "skills": [{"skill_id": "python", "name": "Python"}, {"skill_id": "excel", "name": "Excel"}],
    "projects": [],
}


@pytest.fixture
def release_client(client: TestClient):
    app.dependency_overrides[get_settings] = lambda: Settings(
        CATALOG_MODE="cached", MATCHING_MODE="hussain", _env_file=None
    )
    yield client
    app.dependency_overrides.pop(get_settings, None)


def _responses(client: TestClient):
    yield client.post("/api/v1/careers/match", json={"profile": PROFILE})
    yield client.post("/api/v1/scenarios/simulate", json={"profile": PROFILE, "scenario_id": "fast"})
    yield client.post(
        "/api/v1/roadmaps/generate",
        json={"profile": PROFILE, "role_id": "financial_analyst", "budget_limit": 10, "hours_per_week": 5},
    )
    yield client.post("/api/v1/roadmaps/generate", json={"profile": PROFILE, "role_id": "astronaut"})
    yield client.post("/api/v1/projects/recommend", json={"profile": PROFILE, "role_id": "financial_analyst"})
    yield client.post("/api/v1/projects/recommend", json={"profile": PROFILE, "role_id": "actuary"})
    yield client.post(
        "/api/v1/projects/simulate",
        json={"profile": PROFILE, "role_id": "financial_analyst", "project_id": "fa_credit_default_analysis"},
    )
    yield client.get("/api/v1/trends")
    yield client.get("/api/v1/trends", params={"role_id": "astronaut"})
    yield client.get("/api/v1/sdgs/financial_analyst")
    yield client.get("/api/v1/sdgs/astronaut")
    yield _post_cv(client, VALID_PDF)  # no LLM key configured -> manual_review


def test_no_internal_wording_in_any_student_facing_warning(release_client: TestClient):
    seen = 0
    for response in _responses(release_client):
        assert response.status_code == 200, response.text
        for warning in response.json()["warnings"]:
            seen += 1
            for term in FORBIDDEN:
                assert term not in warning, (response.url, term, warning)
    assert seen > 10


def test_cv_failure_shows_only_the_generic_message(release_client: TestClient):
    body = _post_cv(release_client, VALID_PDF).json()
    assert body["data"]["status"] == "manual_review"
    assert body["warnings"] == [
        "We couldn't read your CV automatically right now. Please review or fill in your details below."
    ]


def test_project_gap_message_counts_roles_from_the_data(release_client: TestClient):
    import json
    from pathlib import Path

    cached = Path(__file__).resolve().parents[1] / "app" / "data" / "cached"
    role_ids = {r["role_id"] for r in json.loads((cached / "roles.json").read_text())}
    covered = {p["role_id"] for p in json.loads((cached / "projects.json").read_text())["projects"]} & role_ids
    uncovered = sorted(role_ids - covered)[0]

    body = release_client.post(
        "/api/v1/projects/recommend", json={"profile": PROFILE, "role_id": uncovered}
    ).json()
    assert body["data"]["projects"] == []
    assert f"Projects are available for {len(covered)} of {len(role_ids)} roles." in body["warnings"][0]
