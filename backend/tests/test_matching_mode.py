"""Milestone 6C-2B: MATCHING_MODE=fixture|hussain activation behavior,
its fail-closed interaction with ENABLE_FIXTURES and CATALOG_MODE, and
accurate provenance disclosure. No heavy ML dependency is required or
imported by any test here.

Milestone 10A: a real RunPod endpoint is never contacted — tests that
exercise the "configured" path set fake RUNPOD_API_KEY/RUNPOD_ENDPOINT_ID
values and always mock the network boundary (urllib.request.urlopen, or
the RunPodEmbeddingProvider class itself), so no outbound request is ever
made. Tests that need the *unconfigured* path explicitly clear both env
vars rather than assuming the ambient environment lacks them.
"""
import itertools
import sys

import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints.careers import get_matching_provider, get_role_catalog, get_trend_provider
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


@pytest.mark.parametrize(
    "catalog_mode,matching_mode",
    [("fixture", "fixture"), ("fixture", "hussain"), ("cached", "fixture")],
)
def test_roadmaps_and_projects_fail_closed_when_fixtures_disabled_and_catalog_mode_is_not_fully_cached(
    client: TestClient, catalog_mode, matching_mode
):
    """roadmaps/generate and projects/recommend+simulate must 503 under
    ENABLE_FIXTURES=False whenever at least one required provider
    (matching, resources or projects) would still be fixture-sourced.
    The one combination NOT covered here — cached + hussain — is now
    (Milestone 6D-2D) fully non-fixture and succeeds instead; see
    test_roadmaps_and_projects_succeed_with_fixtures_disabled_when_fully_cached below."""
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
            json={"profile": EMPTY_PROFILE, "role_id": "data_analyst", "project_id": "da_online_retail_dashboard"},
        )
    finally:
        _clear_override()

    for response in (roadmap, recommend, simulate):
        assert response.status_code == 503, (catalog_mode, matching_mode, response.json())
        assert response.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"


def test_roadmaps_and_projects_succeed_with_fixtures_disabled_when_fully_cached(client: TestClient):
    """Milestone 6D-2D: CATALOG_MODE=cached + MATCHING_MODE=hussain means
    every required provider (matcher, role catalog, resource catalog,
    project catalog) is genuinely non-fixture — ENABLE_FIXTURES=False
    must NOT 503 this combination, unlike every other one above."""
    _override_settings(CATALOG_MODE="cached", MATCHING_MODE="hussain", ENABLE_FIXTURES=False)
    try:
        roadmap = client.post(
            "/api/v1/roadmaps/generate", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
        recommend = client.post(
            "/api/v1/projects/recommend", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
        simulate = client.post(
            "/api/v1/projects/simulate",
            json={"profile": EMPTY_PROFILE, "role_id": "data_analyst", "project_id": "da_online_retail_dashboard"},
        )
    finally:
        _clear_override()

    assert roadmap.status_code == 200
    assert recommend.status_code == 200
    assert simulate.status_code == 200


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


def test_runpod_is_attempted_when_configured_but_degrades_safely_on_endpoint_failure(
    client: TestClient, monkeypatch
):
    """Milestone 10A: with both RunPod env vars set, the endpoint is now
    genuinely attempted (unlike before) — but a failing/unreachable
    endpoint must never break the request: it degrades to exact skill
    matching with DEGRADED_CAVEAT, exactly like the no-credentials case.
    Network is mocked (never a real call) per Milestone 10A's own
    requirement; urlopen is allowed to be called at most once per
    request (bounded — no retry storm, no excessive latency)."""
    import urllib.request

    from app.services.hussain_matching.backend_adapter import DEGRADED_CAVEAT

    monkeypatch.setenv("RUNPOD_API_KEY", "fake_key_never_sent_to_a_real_endpoint")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "fake_endpoint")

    call_count = {"n": 0}

    def _simulated_network_failure(*a, **k):
        call_count["n"] += 1
        raise OSError("simulated network failure — no real request was made")

    monkeypatch.setattr(urllib.request, "urlopen", _simulated_network_failure)

    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 4})
    finally:
        _clear_override()

    assert response.status_code == 200
    # One retry is allowed inside runpod_client.py's own transient-error
    # handling; this proves it's bounded, not unbounded or repeated
    # beyond that per request.
    assert call_count["n"] <= 2
    for match in response.json()["data"]["matches"]:
        assert DEGRADED_CAVEAT in match["caveats"]


def test_runpod_is_never_contacted_when_not_configured(client: TestClient, monkeypatch):
    """The no-credentials case must still never touch the network at
    all — not even one attempt — unlike the configured-but-failing case
    above."""
    import urllib.request

    from app.services.hussain_matching.backend_adapter import DEGRADED_CAVEAT

    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    monkeypatch.delenv("RUNPOD_ENDPOINT_ID", raising=False)

    def _forbidden(*a, **k):
        raise AssertionError("urlopen must never be called when RunPod is not configured")

    monkeypatch.setattr(urllib.request, "urlopen", _forbidden)

    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 4})
    finally:
        _clear_override()

    assert response.status_code == 200  # would have raised AssertionError if urlopen were called
    for match in response.json()["data"]["matches"]:
        assert DEGRADED_CAVEAT in match["caveats"]


def test_get_matching_provider_hussain_mode_no_longer_forces_no_similarity():
    """Milestone 10A: get_matching_provider() must stop forcing a
    no-similarity override — HussainMatchingProvider's own
    runpod_configured() check decides instead, per request."""
    provider = get_matching_provider(Settings(MATCHING_MODE="hussain", _env_file=None))
    assert isinstance(provider, HussainMatchingProvider)
    assert provider.similarity is None


def test_runpod_is_used_end_to_end_when_configured_and_reachable(client: TestClient, monkeypatch):
    """Milestone 10A acceptance criterion: when RunPod is configured and
    the endpoint succeeds, the semantic embedding adapter is genuinely
    used (no DEGRADED_CAVEAT) — proven via the real API route, not just
    the adapter directly. The RunPod wire protocol itself is Hussain's
    own, separately-tested surface (app/services/hussain_matching/tests/
    test_runpod_client.py); here we mock at the RunPodEmbeddingProvider
    boundary so this test proves our wiring, not his HTTP parsing, and
    never makes a real network call."""
    import app.services.hussain_matching.backend_adapter as adapter_module
    from app.services.hussain_matching.backend_adapter import DEGRADED_CAVEAT

    monkeypatch.setenv("RUNPOD_API_KEY", "fake_key_never_sent_to_a_real_endpoint")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "fake_endpoint")

    class _FakeConfiguredProvider:
        """Duck-typed stand-in for a successfully configured
        RunPodEmbeddingProvider: precompute() never touches the network,
        and calling it returns a fixed similarity."""

        def precompute(self) -> None:
            return None

        def __call__(self, skill_a: str, skill_b: str) -> float:
            return 0.0  # deterministic; the exact value isn't what's under test

        @classmethod
        def from_skills(cls, *_args, **_kwargs) -> "_FakeConfiguredProvider":
            return cls()

    monkeypatch.setattr(adapter_module, "RunPodEmbeddingProvider", _FakeConfiguredProvider)

    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 4})
    finally:
        _clear_override()

    assert response.status_code == 200
    for match in response.json()["data"]["matches"]:
        assert DEGRADED_CAVEAT not in match["caveats"]
        # Unchanged API contract: same RoleMatch shape regardless of path.
        assert set(match) == {
            "role_id", "role_title", "score", "score_type", "matched_skills", "missing_skills",
            "score_breakdown", "evidence_ids", "explanation", "caveats",
        }


def test_unknown_skill_is_interpreted_via_runpod_with_partial_credit(client: TestClient, monkeypatch):
    """Milestone 10C acceptance (Part D.3): a free-text skill name not in
    the catalogue (e.g. "Database Querying") is offered to the configured
    semantic provider's new .interpret() method and, above the similarity
    threshold, credited as partial/unconfirmed — never silently dropped,
    never full credit, and always disclosed in the explanation and a
    per-match caveat naming the exact interpretation. Network is mocked
    (never a real RunPod call)."""
    import app.services.hussain_matching.backend_adapter as adapter_module

    monkeypatch.setenv("RUNPOD_API_KEY", "fake_key_never_sent_to_a_real_endpoint")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "fake_endpoint")

    class _FakeInterpretingProvider:
        def precompute(self) -> None:
            return None

        def __call__(self, skill_a: str, skill_b: str) -> float:
            return 0.0

        def interpret(self, names, *, threshold=0.60):
            return [("sql", 0.71) if "database" in n.lower() else None for n in names]

        @classmethod
        def from_skills(cls, *_args, **_kwargs) -> "_FakeInterpretingProvider":
            return cls()

    monkeypatch.setattr(adapter_module, "RunPodEmbeddingProvider", _FakeInterpretingProvider)

    profile = {
        "interests": [],
        "skills": [{"skill_id": "database_querying", "name": "Database Querying"}],
        "projects": [],
    }
    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": profile, "limit": 4})
    finally:
        _clear_override()

    assert response.status_code == 200
    data_analyst = next(m for m in response.json()["data"]["matches"] if m["role_id"] == "data_analyst")
    assert "interpreted" in data_analyst["explanation"].lower()
    assert any("Interpreted \"Database Querying\" as" in c for c in data_analyst["caveats"])
    assert any("please confirm" in c.lower() for c in data_analyst["caveats"])


# --- Milestone 10B: RunPod circuit breaker persists across requests -----


def test_get_matching_provider_returns_the_same_shared_instance_across_calls():
    """The fix itself: get_matching_provider() must return the identical
    HussainMatchingProvider object on repeated calls within the process
    (not a fresh one each time) — this is what lets the RunPod circuit
    breaker actually persist across separate HTTP requests."""
    settings = Settings(MATCHING_MODE="hussain", _env_file=None)
    first = get_matching_provider(settings)
    second = get_matching_provider(settings)
    assert first is second


def test_shared_provider_rebuilds_when_runpod_credentials_change(monkeypatch):
    """Milestone 10C's credential-rotation fix, now directly tested: the
    shared singleton must rebuild (discarding its stale embedding-client
    cache) when RUNPOD_API_KEY/RUNPOD_ENDPOINT_ID change — not keep
    reusing a provider whose cached RunPodEmbeddingProvider baked in the
    OLD key at construction time."""
    settings = Settings(MATCHING_MODE="hussain", _env_file=None)

    monkeypatch.setenv("RUNPOD_API_KEY", "fake_key_version_one")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "fake_endpoint")
    first = get_matching_provider(settings)

    monkeypatch.setenv("RUNPOD_API_KEY", "fake_key_version_two_after_rotation")
    second = get_matching_provider(settings)

    assert first is not second


def test_shared_provider_rebuilds_when_runpod_endpoint_id_changes(monkeypatch):
    """Same fix, the other half of the credential pair."""
    settings = Settings(MATCHING_MODE="hussain", _env_file=None)

    monkeypatch.setenv("RUNPOD_API_KEY", "fake_key")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "fake_endpoint_one")
    first = get_matching_provider(settings)

    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "fake_endpoint_two")
    second = get_matching_provider(settings)

    assert first is not second


def test_shared_provider_does_not_rebuild_when_credentials_are_unchanged(monkeypatch):
    """The negative case: unrelated repeated calls with the SAME
    credentials (including both unset) must keep reusing one instance —
    confirms the rebuild is specifically credential-change-triggered, not
    happening on every call regardless."""
    settings = Settings(MATCHING_MODE="hussain", _env_file=None)
    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    monkeypatch.delenv("RUNPOD_ENDPOINT_ID", raising=False)

    first = get_matching_provider(settings)
    second = get_matching_provider(settings)
    third = get_matching_provider(settings)

    assert first is second is third


def test_shared_provider_rebuilds_after_max_age_elapses(monkeypatch):
    """Milestone 10C's bounded-retention fix for the free-text
    interpretation cache (EmbeddingProvider._query_vectors, keyed by a
    student's own typed skill text) — the shared provider must not
    persist unboundedly for the entire process lifetime. Simulated by
    advancing the clock past _SHARED_PROVIDER_MAX_AGE_SECONDS, never a
    real sleep."""
    import app.api.v1.endpoints.careers as careers_module

    settings = Settings(MATCHING_MODE="hussain", _env_file=None)
    clock = {"t": 1_000_000.0}
    monkeypatch.setattr(careers_module.time, "monotonic", lambda: clock["t"])

    first = get_matching_provider(settings)
    clock["t"] += careers_module._SHARED_PROVIDER_MAX_AGE_SECONDS - 1
    still_fresh = get_matching_provider(settings)
    clock["t"] += 2  # now past the max age
    rebuilt = get_matching_provider(settings)

    assert first is still_fresh
    assert first is not rebuilt


def test_reset_shared_hussain_provider_for_tests_actually_clears_it():
    """The test-isolation hook (used by conftest.py's autouse fixture)
    must genuinely replace the singleton, not just appear to."""
    from app.api.v1.endpoints.careers import reset_shared_hussain_provider_for_tests

    settings = Settings(MATCHING_MODE="hussain", _env_file=None)
    first = get_matching_provider(settings)
    reset_shared_hussain_provider_for_tests()
    second = get_matching_provider(settings)
    assert first is not second


def test_cooldown_persists_across_separate_requests_and_skips_the_second_attempt(
    client: TestClient, monkeypatch
):
    """Milestone 10B acceptance (task 7): a RunPod failure's cooldown
    must survive between separate HTTP requests, not just within one —
    the second request must make zero new network attempts while still
    returning a safe, degraded result."""
    import urllib.request

    from app.services.hussain_matching.backend_adapter import DEGRADED_CAVEAT

    monkeypatch.setenv("RUNPOD_API_KEY", "fake_key_never_sent_to_a_real_endpoint")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "fake_endpoint")

    call_count = {"n": 0}

    def _simulated_network_failure(*a, **k):
        call_count["n"] += 1
        raise OSError("simulated network failure — no real request was made")

    monkeypatch.setattr(urllib.request, "urlopen", _simulated_network_failure)

    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        first = client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 4})
        calls_after_first_request = call_count["n"]
        second = client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 4})
    finally:
        _clear_override()

    assert first.status_code == 200
    assert second.status_code == 200
    assert calls_after_first_request > 0  # the first request did attempt RunPod (and failed)
    # The second request made ZERO new network attempts — the cooldown
    # from the first request's failure held, proving persistence.
    assert call_count["n"] == calls_after_first_request
    for response in (first, second):
        for match in response.json()["data"]["matches"]:
            assert DEGRADED_CAVEAT in match["caveats"]


def test_runpod_attempts_resume_after_the_cooldown_elapses(client: TestClient, monkeypatch):
    """Milestone 10B acceptance (task 8): once retry_after_seconds has
    passed, the next request must attempt RunPod again — the circuit
    breaker is a temporary cooldown, not a permanent kill switch. The
    elapsed-time wait itself is simulated (never a real sleep in a test)
    by resetting the shared provider's own timer directly."""
    import urllib.request

    from app.api.v1.endpoints.careers import _get_shared_hussain_provider

    monkeypatch.setenv("RUNPOD_API_KEY", "fake_key_never_sent_to_a_real_endpoint")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "fake_endpoint")

    call_count = {"n": 0}

    def _simulated_network_failure(*a, **k):
        call_count["n"] += 1
        raise OSError("simulated network failure — no real request was made")

    monkeypatch.setattr(urllib.request, "urlopen", _simulated_network_failure)

    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 4})
        calls_after_failure = call_count["n"]
        assert calls_after_failure > 0

        _get_shared_hussain_provider()._down_until = 0.0  # simulate cooldown elapsed

        client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 4})
    finally:
        _clear_override()

    assert call_count["n"] > calls_after_failure  # a new attempt was made once cooldown had elapsed


def test_shared_provider_survives_concurrent_requests_without_crashing_or_corrupting_matches(
    client: TestClient, monkeypatch
):
    """Milestone 10D concurrency review: route handlers are sync `def`,
    so FastAPI runs them in a thread pool — concurrent requests really do
    call _get_shared_hussain_provider()/.match() on the same instance at
    once. This does not assume the GIL makes that safe; it empirically
    fires many real concurrent requests (no credentials set, so every
    thread takes the cheap "not configured" path — still exercises the
    shared singleton's check-then-use logic and HussainMatchingProvider's
    internal dict reads/writes under real thread concurrency) and checks
    every response is a well-formed 200 with a complete, uncorrupted
    RoleMatch list — never a crash, never a malformed/partial result."""
    from concurrent.futures import ThreadPoolExecutor

    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    monkeypatch.delenv("RUNPOD_ENDPOINT_ID", raising=False)

    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        def _one_request(_: int):
            return client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 4})

        with ThreadPoolExecutor(max_workers=16) as pool:
            responses = list(pool.map(_one_request, range(32)))
    finally:
        _clear_override()

    for response in responses:
        assert response.status_code == 200
        matches = response.json()["data"]["matches"]
        assert len(matches) > 0
        for match in matches:
            assert 0.0 <= match["score"] <= 100.0
            assert match["role_id"]  # never a blank/corrupted entry


def test_matching_provider_di_override_still_bypasses_the_shared_singleton(client: TestClient):
    """Milestone 10B requirement 3: an explicit get_matching_provider
    override must still completely replace the dependency, never
    touching the shared HussainMatchingProvider singleton at all."""
    class StubMatchingProvider:
        def match(self, profile, roles, scenario, signals):
            from app.schemas.matching import RoleMatch as _RoleMatch
            from app.schemas.matching import ScoreBreakdown

            return [
                _RoleMatch(
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


def test_all_eight_roles_match_without_crashing_in_hussain_mode(monkeypatch):
    """Step 4: all 8 roles, MATCHING_MODE=hussain, no RunPod. Bypasses
    MatchRequest.limit<=6 by calling the provider directly, the same way
    MatchingService.match() does before truncating.

    Milestone 10A: RunPod env vars are explicitly cleared (not just
    assumed absent from the ambient environment) so this test's "no
    RunPod" premise is deterministic now that get_matching_provider() no
    longer forces a no-similarity override."""
    import urllib.request

    from app.api.v1.endpoints.careers import get_matching_provider, get_role_catalog
    from app.core.config import Settings

    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    monkeypatch.delenv("RUNPOD_ENDPOINT_ID", raising=False)

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
    """Milestone 10C: Hussain's latest matcher fixed a real bug — a role
    with no prerequisites previously got free 100/100 credit for a
    dimension it never actually assessed. It now reports 0 (the contract
    requires a number) and says so explicitly in the explanation, rather
    than inventing a score for something that was never checked."""
    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 4})
    finally:
        _clear_override()

    assert response.status_code == 200
    for match in response.json()["data"]["matches"]:
        assert match["score_breakdown"]["prerequisites"] == 0.0
        assert "prerequisites not assessed" in match["explanation"]


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
    """mechanical_design_engineer (our fixture-only role_id, outside
    Jawad's canonical set entirely — unlike mechanical_engineer, which
    now has real cached projects as of Milestone 6D-2D) must get an
    honest empty result, never a fabricated project."""
    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post(
            "/api/v1/projects/recommend",
            json={"profile": EMPTY_PROFILE, "role_id": "mechanical_design_engineer"},
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


@pytest.mark.parametrize("runpod_configured", [False, True])
def test_matching_mode_warning_never_falsely_claims_semantic_matching_is_disabled(
    client: TestClient, monkeypatch, runpod_configured: bool
):
    """Milestone 10A requirement 4: matching_mode_warning() must describe
    RunPod as conditionally possible, never as unconditionally disabled —
    checked under both the unconfigured and the configured-but-mocked-
    failing case, since the warning text is computed before matching
    runs and can't know in advance whether this specific request will
    actually reach RunPod."""
    if runpod_configured:
        import urllib.request

        monkeypatch.setenv("RUNPOD_API_KEY", "fake_key_never_sent_to_a_real_endpoint")
        monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "fake_endpoint")
        monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: (_ for _ in ()).throw(OSError("simulated")))
    else:
        monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
        monkeypatch.delenv("RUNPOD_ENDPOINT_ID", raising=False)

    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": SQL_PROFILE, "limit": 4})
    finally:
        _clear_override()

    warnings_text = " ".join(response.json()["warnings"]).lower()
    assert "explicitly disabled" not in warnings_text
    assert "runpod" in warnings_text
    assert "may use" in warnings_text or "fall" in warnings_text  # describes the possibility, not a certainty


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


def test_careers_match_without_a_scenario_is_unaffected_by_real_trend_signals(client: TestClient):
    """Milestone 10C: CATALOG_MODE=cached now feeds MatchingService real
    cached trend signals (CachedTrendSignalProvider, not NullTrendProvider
    — see test_cached_trend_signals_produce_a_real_explainable_scenario_
    change below for scenario_id-driven change). Every one of the 8
    cached roles has at least one covered, moving skill (checked
    directly), so "pick an uncovered skill" can no longer demonstrate a
    same-score guarantee at the role level — the real, still-true
    invariant is that plain /careers/match (scenario_id=None, unlike
    /scenarios/simulate) must score identically whether real trend
    signals are available or not, proven end to end via the real route
    by swapping in a dramatically different signal set through the
    existing get_trend_provider DI override."""
    class _ExtremeSignalProvider:
        def latest(self, role_id=None):
            return [{"skill_id": "python", "direction": "rising", "signal_type": "developer_activity"}]

    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    profile = {"interests": [], "skills": [{"skill_id": "python", "name": "Python"}], "projects": []}
    try:
        with_real_signals = client.post("/api/v1/careers/match", json={"profile": profile, "limit": 6})

        app.dependency_overrides[get_trend_provider] = lambda: _ExtremeSignalProvider()
        try:
            with_extreme_signals = client.post("/api/v1/careers/match", json={"profile": profile, "limit": 6})
        finally:
            app.dependency_overrides.pop(get_trend_provider, None)
    finally:
        _clear_override()

    assert with_real_signals.status_code == 200 and with_extreme_signals.status_code == 200
    scores_a = {m["role_id"]: m["score"] for m in with_real_signals.json()["data"]["matches"]}
    scores_b = {m["role_id"]: m["score"] for m in with_extreme_signals.json()["data"]["matches"]}
    assert scores_a == scores_b
    assert "software_developer" in scores_a


def test_cached_trend_signals_produce_a_real_explainable_scenario_change(client: TestClient):
    """Milestone 10C acceptance (Part B): moderate/fast scenarios must
    produce a meaningful, explainable change when a suitable trend
    signal is actually available — proven against Jawad's real cached
    data (cad_software/matlab/python are all 'rising' in
    app/data/cached/trend_snapshots), not a hardcoded or invented
    difference. The skills sub-score must differ (and the caveat must
    name the adjusted skills), demonstrating the mechanism is genuinely
    signal-driven end to end, not just unit-tested in isolation."""
    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    profile = {
        "interests": [],
        "skills": [
            {"skill_id": "cad_software", "name": "CAD"},
            {"skill_id": "matlab", "name": "MATLAB"},
            {"skill_id": "python", "name": "Python"},
        ],
        "projects": [],
    }
    try:
        moderate = client.post(
            "/api/v1/scenarios/simulate", json={"profile": profile, "scenario_id": "moderate"}
        )
        fast = client.post("/api/v1/scenarios/simulate", json={"profile": profile, "scenario_id": "fast"})
    finally:
        _clear_override()

    assert moderate.status_code == 200 and fast.status_code == 200
    moderate_match = next(
        m for m in moderate.json()["data"]["matches"] if m["role_id"] == "mechanical_engineer"
    )
    fast_match = next(m for m in fast.json()["data"]["matches"] if m["role_id"] == "mechanical_engineer")

    # Fast (25% multiplier) must move further than moderate (10%) for a genuinely rising signal.
    assert fast_match["score_breakdown"]["skills"] > moderate_match["score_breakdown"]["skills"]
    assert any(
        "Scenario adjusted the weight of" in c and "job demand" in c.lower() for c in fast_match["caveats"]
    )
