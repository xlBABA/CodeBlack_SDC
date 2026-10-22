"""Milestone 6C-2B: MATCHING_MODE=fixture|hussain activation behavior,
its fail-closed interaction with ENABLE_FIXTURES and CATALOG_MODE, and
accurate provenance disclosure. HussainMatchingProvider runs fully
offline here — no RunPod endpoint, no RUNPOD_API_KEY, no heavy ML
dependency is required or contacted by any test.
"""
import itertools
import sys

import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints.careers import get_matching_provider, get_role_catalog
from app.core.config import Settings, get_settings
from app.main import app
from app.schemas.profile import StudentProfile
from app.services.hussain_matching import scoring
from app.services.hussain_matching.backend_adapter import HussainMatchingProvider
from app.services.matching_provider import FixtureMatchingProvider

EMPTY_PROFILE = {"interests": [], "skills": [], "projects": []}
SQL_PROFILE = {"interests": [], "skills": [{"skill_id": "sql", "name": "SQL"}], "projects": []}
CACHED_ROLE_IDS = {
    "data_analyst", "financial_analyst", "mechanical_engineer", "public_health_analyst",
    "software_developer", "accountant", "civil_engineer", "environmental_scientist",
}


def _override_settings(**overrides):
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, **overrides)


def _clear_override():
    app.dependency_overrides.pop(get_settings, None)


# --- Full matrix: CATALOG_MODE x MATCHING_MODE x ENABLE_FIXTURES --------
# /careers/match and /scenarios/simulate depend only on the matching
# provider and the role catalog — no fixture project/resource catalog.

_MATRIX = list(itertools.product(["fixture", "cached"], ["fixture", "hussain"], [True, False]))


def _expected_outcome(catalog_mode, matching_mode, enable_fixtures):
    """Mirrors Step 3's explicit rules, including the one fail-closed
    exception: MATCHING_MODE=hussain + CATALOG_MODE=cached does NOT
    depend on fixture role data, so ENABLE_FIXTURES=False does not block
    it there."""
    if enable_fixtures:
        return 200
    if matching_mode == "hussain" and catalog_mode == "cached":
        return 200
    return 503


@pytest.mark.parametrize("catalog_mode,matching_mode,enable_fixtures", _MATRIX)
def test_careers_match_full_matrix(client: TestClient, catalog_mode, matching_mode, enable_fixtures):
    _override_settings(CATALOG_MODE=catalog_mode, MATCHING_MODE=matching_mode, ENABLE_FIXTURES=enable_fixtures)
    try:
        response = client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 4})
    finally:
        _clear_override()

    expected = _expected_outcome(catalog_mode, matching_mode, enable_fixtures)
    assert response.status_code == expected, (catalog_mode, matching_mode, enable_fixtures, response.json())
    if expected == 200:
        assert response.json()["data_mode"] == "fixture"  # never "cached", never "live" — see Step 5
    else:
        assert response.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"


@pytest.mark.parametrize("catalog_mode,matching_mode,enable_fixtures", _MATRIX)
def test_scenarios_simulate_full_matrix(client: TestClient, catalog_mode, matching_mode, enable_fixtures):
    """scenarios/simulate shares the same dependency shape as careers/match
    (matcher + role catalog only) — same matrix outcome expected."""
    _override_settings(CATALOG_MODE=catalog_mode, MATCHING_MODE=matching_mode, ENABLE_FIXTURES=enable_fixtures)
    try:
        response = client.post(
            "/api/v1/scenarios/simulate", json={"profile": SQL_PROFILE, "scenario_id": "moderate"}
        )
    finally:
        _clear_override()

    expected = _expected_outcome(catalog_mode, matching_mode, enable_fixtures)
    assert response.status_code == expected


# --- Fail-closed: roadmaps/projects always depend on fixture data ------


@pytest.mark.parametrize("catalog_mode,matching_mode", list(itertools.product(["fixture", "cached"], ["fixture", "hussain"])))
def test_roadmaps_and_projects_fail_closed_when_fixtures_disabled_regardless_of_mode(
    client: TestClient, catalog_mode, matching_mode
):
    """Unlike careers/match, roadmaps/generate and projects/recommend+
    simulate always depend on FixtureResourceCatalog/FixtureProjectCatalog
    (no cached alternative exists) — ENABLE_FIXTURES=False must 503 them
    in every CATALOG_MODE/MATCHING_MODE combination, including the one
    combination (cached + hussain) where careers/match itself succeeds."""
    _override_settings(CATALOG_MODE=catalog_mode, MATCHING_MODE=matching_mode, ENABLE_FIXTURES=False)
    try:
        roadmap = client.post(
            "/api/v1/roadmaps/generate", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
        recommend = client.post(
            "/api/v1/projects/recommend", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
        simulate = client.post(
            "/api/v1/projects/simulate",
            json={"profile": EMPTY_PROFILE, "role_id": "data_analyst", "project_id": "project_data_dashboard_001"},
        )
    finally:
        _clear_override()

    for response in (roadmap, recommend, simulate):
        assert response.status_code == 503, (catalog_mode, matching_mode, response.json())
        assert response.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"


def test_roadmaps_and_projects_succeed_when_fixtures_enabled_in_hussain_mode(client: TestClient):
    _override_settings(CATALOG_MODE="cached", MATCHING_MODE="hussain", ENABLE_FIXTURES=True)
    try:
        roadmap = client.post(
            "/api/v1/roadmaps/generate", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
        recommend = client.post(
            "/api/v1/projects/recommend", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
    finally:
        _clear_override()

    assert roadmap.status_code == 200
    assert recommend.status_code == 200


# --- Explicit offline operation: no RunPod, no heavy ML --------------------


def test_no_heavy_ml_dependency_is_imported_by_hussain_mode(client: TestClient):
    for forbidden in ("sentence_transformers", "torch", "transformers"):
        assert forbidden not in sys.modules
    _override_settings(MATCHING_MODE="hussain")
    try:
        client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 4})
    finally:
        _clear_override()
    for forbidden in ("sentence_transformers", "torch", "transformers"):
        assert forbidden not in sys.modules


def test_runpod_is_never_contacted_even_with_credentials_present(client: TestClient, monkeypatch):
    """Ensures no environment variable can silently activate external
    inference (Step 4) — even with both RunPod env vars set, urlopen
    must never be called, because get_matching_provider() passes an
    explicit no-similarity override."""
    import urllib.request

    monkeypatch.setenv("RUNPOD_API_KEY", "fake_key_should_never_be_used")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "fake_endpoint")

    def _forbidden(*a, **k):
        raise AssertionError("urlopen must never be called")

    monkeypatch.setattr(urllib.request, "urlopen", _forbidden)

    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 4})
    finally:
        _clear_override()

    assert response.status_code == 200  # would have raised AssertionError if urlopen were called


def test_get_matching_provider_hussain_mode_uses_explicit_no_similarity():
    provider = get_matching_provider(Settings(MATCHING_MODE="hussain", _env_file=None))
    assert isinstance(provider, HussainMatchingProvider)
    assert provider.similarity is not None
    assert provider.similarity("a", "b") == 0.0


# --- Scoring weights/thresholds unchanged --------------------------------


def test_hussain_scoring_weights_are_unchanged():
    """Pins the exact weights audited in Milestone 6C-1 — this milestone
    must not alter them."""
    assert scoring.WEIGHTS == {"skills": 0.50, "experience": 0.20, "prerequisites": 0.15, "transferable": 0.15}
    assert scoring.SIMILARITY_THRESHOLD == 0.60


# --- Correct RoleMatch schema / required-optional / min_semester --------


def test_hussain_mode_response_matches_rolematch_schema(client: TestClient):
    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 4})
    finally:
        _clear_override()

    body = response.json()
    assert response.status_code == 200
    for match in body["data"]["matches"]:
        assert set(match) == {
            "role_id", "role_title", "score", "score_type", "matched_skills", "missing_skills",
            "score_breakdown", "evidence_ids", "explanation", "caveats",
        }
        assert match["score_type"] == "profile_alignment_estimate"
        assert 0.0 <= match["score"] <= 100.0


def test_canonical_cached_role_ids_work_in_hussain_mode_via_api(client: TestClient):
    """MatchRequest.limit's frozen contract maximum is 6, so a single API
    call can't exercise all 8 cached roles — see
    test_all_eight_roles_match_without_crashing_in_hussain_mode below for
    the complete, limit-unconstrained check."""
    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 6})
    finally:
        _clear_override()

    role_ids = {m["role_id"] for m in response.json()["data"]["matches"]}
    assert len(role_ids) == 6
    assert role_ids <= CACHED_ROLE_IDS


def test_all_eight_roles_match_without_crashing_in_hussain_mode():
    """Step 4: all 8 roles, MATCHING_MODE=hussain, no RunPod. Bypasses
    MatchRequest.limit<=6 by calling the provider directly, the same way
    MatchingService.match() does before truncating."""
    import urllib.request

    from app.api.v1.endpoints.careers import get_matching_provider, get_role_catalog
    from app.core.config import Settings

    def _forbidden(*a, **k):
        raise AssertionError("urlopen must never be called")

    original_urlopen = urllib.request.urlopen
    urllib.request.urlopen = _forbidden
    try:
        settings = Settings(MATCHING_MODE="hussain", CATALOG_MODE="cached", _env_file=None)
        roles = get_role_catalog(settings).list_roles()
        assert {r.role_id for r in roles} == CACHED_ROLE_IDS

        provider = get_matching_provider(settings)
        results = provider.match(StudentProfile(**EMPTY_PROFILE), roles, None, [])
        assert len(results) == 8
        for match in results:
            assert 0.0 <= match.score <= 100.0
            assert 0.0 <= match.score_breakdown.prerequisites <= 100.0
    finally:
        urllib.request.urlopen = original_urlopen


def test_optional_skills_never_appear_as_missing_in_hussain_mode_via_api(client: TestClient):
    """End-to-end through the real endpoint: data_analyst's optional
    "excel" must never be presented as a mandatory missing-skill gap."""
    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 4})
    finally:
        _clear_override()

    data_analyst = next(m for m in response.json()["data"]["matches"] if m["role_id"] == "data_analyst")
    missing_ids = {s["skill_id"] for s in data_analyst["missing_skills"]}
    assert "excel" not in missing_ids
    assert "sql" in missing_ids


def test_min_semester_none_does_not_crash_via_api_in_hussain_mode(client: TestClient):
    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 4})
    finally:
        _clear_override()

    assert response.status_code == 200
    for match in response.json()["data"]["matches"]:
        assert match["score_breakdown"]["prerequisites"] == 100.0  # no invented prerequisite, full credit


def test_unknown_role_returns_established_errors_in_hussain_mode(client: TestClient):
    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        roadmap = client.post(
            "/api/v1/roadmaps/generate", json={"profile": EMPTY_PROFILE, "role_id": "does_not_exist_anywhere"}
        )
        simulate = client.post(
            "/api/v1/projects/simulate",
            json={
                "profile": EMPTY_PROFILE, "role_id": "does_not_exist_anywhere",
                "project_id": "project_data_dashboard_001",
            },
        )
    finally:
        _clear_override()

    assert roadmap.status_code == 200
    assert roadmap.json()["data"]["steps"] == []
    assert simulate.status_code == 404
    assert simulate.json()["error"]["code"] == "ROLE_NOT_FOUND"


def test_unsupported_role_projects_are_not_invented_in_hussain_mode(client: TestClient):
    """mechanical_engineer (cached-only, no project_catalog entry) must
    get an honest empty result, never a fabricated project."""
    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post(
            "/api/v1/projects/recommend", json={"profile": EMPTY_PROFILE, "role_id": "mechanical_engineer"}
        )
    finally:
        _clear_override()

    assert response.status_code == 200
    assert response.json()["data"]["projects"] == []


# --- Honest data_mode and warnings ----------------------------------------


def test_hussain_mode_warnings_disclose_offline_operation_not_runpod_or_hiring(client: TestClient):
    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 4})
    finally:
        _clear_override()

    body = response.json()
    assert body["data_mode"] == "fixture"
    warnings_text = " ".join(body["warnings"]).lower()
    assert "hussain" in warnings_text
    assert "offline" in warnings_text
    assert "no runpod" in warnings_text or "runpod" in warnings_text
    assert "not a validated model" in warnings_text
    assert "not a hiring probability" in warnings_text
    for match in body["data"]["matches"]:
        assert "hiring" not in match["explanation"].lower() or "not a hiring" in match["explanation"].lower()


def test_cached_provenance_warning_still_names_the_active_matcher_accurately(client: TestClient):
    """Step 5: catalog_provenance_warnings() must describe whichever
    matching algorithm is actually active, not always say
    "FixtureMatchingProvider" even when Hussain's is running."""
    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 4})
    finally:
        _clear_override()

    warnings_text = " ".join(response.json()["warnings"]).lower()
    assert "cached" in warnings_text
    assert "fixturematchingprovider" not in warnings_text
    assert "hussain" in warnings_text


def test_data_mode_caveat_does_not_falsely_claim_fixture_for_cached_roles(client: TestClient):
    """Regression for the exact contradiction found while implementing
    this milestone: Hussain's per-match "Fixture role for testing; not
    verified occupational data" caveat must never fire for a genuinely
    cached role — it has no way to know the role is real, so it must not
    guess "fixture" either."""
    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 4})
    finally:
        _clear_override()

    for match in response.json()["data"]["matches"]:
        assert "Fixture role for testing" not in " ".join(match["caveats"])


# --- Existing dependency overrides remain functional ----------------------


def test_role_catalog_di_override_still_takes_precedence_in_hussain_mode(client: TestClient):
    class StubCatalog:
        def list_roles(self) -> list:
            from app.services.role_catalog import RoleFixture, RoleRequirement

            return [
                RoleFixture(
                    role_id="stub_role", role_title="Stub Role", category="Test", min_semester=1,
                    required_skills=(RoleRequirement("sql", "SQL", weight=1.0),),
                    transferable_interests=(), evidence_ids=("stub_evidence",),
                )
            ]

    _override_settings(MATCHING_MODE="hussain")
    app.dependency_overrides[get_role_catalog] = lambda: StubCatalog()
    try:
        response = client.post("/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 6})
    finally:
        _clear_override()
        app.dependency_overrides.pop(get_role_catalog, None)

    assert response.status_code == 200
    assert {m["role_id"] for m in response.json()["data"]["matches"]} == {"stub_role"}


def test_matching_provider_di_override_still_takes_precedence_over_matching_mode(client: TestClient):
    """An explicit override of get_matching_provider itself must win even
    when MATCHING_MODE=hussain is configured — the override replaces the
    whole dependency, matching_mode is never consulted."""
    class StubMatchingProvider:
        def match(self, profile, roles, scenario, signals):
            from app.schemas.matching import RoleMatch, ScoreBreakdown

            return [
                RoleMatch(
                    role_id="stub_role", role_title="Stub Role", score=42.0,
                    score_breakdown=ScoreBreakdown(skills=100, experience=100, prerequisites=100, transferable=100),
                    explanation="Stub.", caveats=["Stub caveat"],
                )
            ]

    _override_settings(MATCHING_MODE="hussain")
    app.dependency_overrides[get_matching_provider] = lambda: StubMatchingProvider()
    try:
        response = client.post("/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 6})
    finally:
        _clear_override()
        app.dependency_overrides.pop(get_matching_provider, None)

    assert response.status_code == 200
    matches = response.json()["data"]["matches"]
    assert len(matches) == 1 and matches[0]["role_id"] == "stub_role"


# --- Existing fixture default is completely unchanged ---------------------


def test_fixture_default_end_to_end_unchanged(client: TestClient):
    """No override at all — MATCHING_MODE's mere existence must not alter
    today's default behavior."""
    response = client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 6})
    assert response.status_code == 200
    body = response.json()
    assert body["data_mode"] == "fixture"
    role_ids = {m["role_id"] for m in body["data"]["matches"]}
    assert role_ids == {
        "data_analyst", "financial_analyst", "mechanical_design_engineer", "sustainability_coordinator",
    }
    for match in body["data"]["matches"]:
        assert isinstance(match["score"], float)  # FixtureMatchingProvider, not Hussain's int


def test_get_matching_provider_fixture_mode_still_returns_fixture_matching_provider():
    provider = get_matching_provider(Settings(_env_file=None))
    assert isinstance(provider, FixtureMatchingProvider)


# --- Milestone 6D-2A Extension: 8-role catalog regression tests ----------


def test_matching_service_returns_top_6_of_8_cached_roles(db_session):
    """MatchingService.match()'s existing matches[:request.limit] truncation,
    unmodified by the catalog expansion, applied to the real 8-role
    cached catalog — catalog_coverage.verified must report 8, not a
    stale hardcoded 4."""
    from app.schemas.matching import MatchRequest
    from app.services.matching_service import MatchingService
    from app.services.profile_service import ProfileService
    from app.services.role_catalog_cached import CachedRoleCatalog
    from app.services.trend_provider import NullTrendProvider

    service = MatchingService(
        profile_service=ProfileService(db_session),
        catalog=CachedRoleCatalog(),
        matcher=HussainMatchingProvider(similarity=lambda a, b: 0.0),
        trends=NullTrendProvider(),
    )
    profile = StudentProfile(**SQL_PROFILE)
    outcome = service.match(MatchRequest(profile=profile))

    assert len(outcome.payload.matches) == 6
    assert outcome.payload.catalog_coverage.verified == 8
    assert outcome.payload.catalog_coverage.total_target == 30


def test_new_roles_and_skills_do_not_change_scenario_scores(client: TestClient):
    """The scenario_id='fast' vs. baseline guarantee must hold for the
    newly added roles/skills too, not just the original 4 — scores stay
    identical because MatchingService still injects NullTrendProvider
    (no real signals), regardless of catalog size."""
    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    profile = {"interests": [], "skills": [{"skill_id": "javascript", "name": "JavaScript"}], "projects": []}
    try:
        baseline = client.post(
            "/api/v1/scenarios/simulate", json={"profile": profile, "scenario_id": "moderate"}
        )
        fast = client.post("/api/v1/scenarios/simulate", json={"profile": profile, "scenario_id": "fast"})
    finally:
        _clear_override()

    assert baseline.status_code == 200 and fast.status_code == 200
    baseline_scores = {m["role_id"]: m["score"] for m in baseline.json()["data"]["matches"]}
    fast_scores = {m["role_id"]: m["score"] for m in fast.json()["data"]["matches"]}
    assert baseline_scores == fast_scores
    assert "software_developer" in baseline_scores  # sanity: a new role was actually exercised
