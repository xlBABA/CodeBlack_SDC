"""Milestone (Jawad fix, 2026-10-25): a comprehensive, cross-endpoint audit
following up on Milestone 13E-4, which only cleaned careers.py's three
provenance-warning functions. Jawad's live test of the deployed app found
the same "CATALOG_MODE=cached: ... Jawad's verified ..." pattern leaking
on /sdgs, /trends, /roadmaps/generate and /projects/recommend too, plus a
teammate's name baked into FixtureMatchingProvider's own caveat and into
/projects/simulate's warning. This file is the single place that checks
every one of those response surfaces at once, so a future regression in
any of them is caught here rather than requiring a fresh audit each time.

No real RunPod call anywhere in this file.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.v1.endpoints.careers import get_settings
from app.core.config import Settings
from app.main import app

EMPTY_PROFILE = {"interests": [], "skills": [], "projects": []}

# Terms that must never appear in any student-facing response body — env
# var names, teammate names, internal class/module names. Deliberately
# narrower than Milestone 13E-4's list (no "matching_mode"/"catalog_mode"
# substring here, since some of these endpoints' own JSON field names or
# fixtures could coincidentally contain "mode"; checked individually below
# where that risk exists) — the common, always-safe core.
FORBIDDEN_TERMS = ("jawad", "hussain", "catalog_mode=", "fixturematchingprovider")


def _override(**kwargs):
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, **kwargs)


def _clear():
    app.dependency_overrides.pop(get_settings, None)


def _assert_clean(text: str) -> None:
    lowered = text.lower()
    for term in FORBIDDEN_TERMS:
        assert term not in lowered, term


def test_sdgs_cached_mode_never_leaks_internal_terms(client: TestClient):
    _override(CATALOG_MODE="cached")
    try:
        response = client.get("/api/v1/sdgs/data_analyst")
    finally:
        _clear()

    assert response.status_code == 200
    body = response.json()
    assert body["data_mode"] == "cached"
    all_text = " ".join(body["warnings"])
    _assert_clean(all_text)
    # meaningful disclosures survive
    assert "cached" in all_text.lower()
    assert "united nations" in all_text.lower()


def test_sdgs_fixture_mode_never_leaks_internal_terms(client: TestClient):
    response = client.get("/api/v1/sdgs/data_analyst")
    assert response.status_code == 200
    body = response.json()
    all_text = " ".join(body["warnings"])
    _assert_clean(all_text)
    assert "united nations" in all_text.lower()


def test_trends_cached_mode_never_leaks_internal_terms(client: TestClient):
    _override(CATALOG_MODE="cached")
    try:
        response = client.get("/api/v1/trends")
    finally:
        _clear()

    assert response.status_code == 200
    body = response.json()
    all_text = " ".join(body["warnings"])
    _assert_clean(all_text)
    assert "cached" in all_text.lower()
    assert "hiring" in all_text.lower()  # "NOT verified hiring demand"


def test_roadmaps_cached_mode_never_leaks_internal_terms(client: TestClient):
    _override(CATALOG_MODE="cached")
    try:
        response = client.post(
            "/api/v1/roadmaps/generate", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
    finally:
        _clear()

    assert response.status_code == 200
    body = response.json()
    all_text = " ".join(body["warnings"])
    _assert_clean(all_text)
    assert "cached" in all_text.lower()


def test_projects_recommend_cached_mode_never_leaks_internal_terms(client: TestClient):
    _override(CATALOG_MODE="cached")
    try:
        response = client.post(
            "/api/v1/projects/recommend", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
    finally:
        _clear()

    assert response.status_code == 200
    body = response.json()
    all_text = " ".join(body["warnings"])
    _assert_clean(all_text)
    assert "cached" in all_text.lower()


def test_projects_simulate_never_leaks_internal_terms(client: TestClient):
    _override(CATALOG_MODE="cached", MATCHING_MODE="hussain", ENABLE_FIXTURES=False)
    try:
        response = client.post(
            "/api/v1/projects/simulate",
            json={
                "profile": EMPTY_PROFILE,
                "role_id": "data_analyst",
                "project_id": "da_online_retail_dashboard",
            },
        )
    finally:
        _clear()

    assert response.status_code == 200
    body = response.json()
    all_text = " ".join(body["warnings"])
    _assert_clean(all_text)
    assert "not a validated prediction" in all_text.lower()  # the real disclosure survives


def test_fixture_matching_provider_caveats_never_leak_a_teammate_name():
    from app.schemas.profile import StudentProfile
    from app.services.matching_provider import FixtureMatchingProvider
    from app.services.role_catalog import FixtureRoleCatalog

    role = FixtureRoleCatalog().list_roles()[0]
    profile = StudentProfile(interests=[], skills=[], projects=[])
    match = FixtureMatchingProvider().match(profile, [role], None, [])[0]

    all_text = " ".join(match.caveats)
    _assert_clean(all_text)
    assert "hiring" in all_text.lower()


def test_hussain_mode_fail_closed_503_never_leaks_a_teammate_name(client: TestClient):
    """ENABLE_FIXTURES=False + MATCHING_MODE=hussain + CATALOG_MODE=fixture
    (the default) is a genuine misconfiguration the backend fails closed
    on with a 503 — that error message is still returned to whoever made
    the request, so it must stay as internal-jargon-free as any other
    student-facing text."""
    _override(MATCHING_MODE="hussain", ENABLE_FIXTURES=False)
    try:
        response = client.post(
            "/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 6}
        )
    finally:
        _clear()

    assert response.status_code == 503
    message = response.json()["error"]["message"]
    _assert_clean(message)
    assert "catalog_mode" not in message.lower()
    assert "enable_fixtures" not in message.lower()
