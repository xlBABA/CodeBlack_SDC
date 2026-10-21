"""Milestone 6A: integration-readiness infrastructure tests.

No real network calls anywhere here — provider-unavailable and timeout
conditions are exercised entirely through dependency overrides and fake
test-double providers, per the milestone's restriction against building
real RunPod/LLM/Hussain-matcher clients.
"""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.v1.endpoints.careers import get_matching_provider
from app.core.config import Settings, get_settings
from app.core.integration_errors import provider_timeout, provider_unavailable
from app.main import app

PROFILE_JSON = {"interests": [], "skills": [], "projects": []}


# --- 1. Existing fixture mode remains functional ---------------------------


def test_fixture_mode_careers_match_still_works(client: TestClient):
    response = client.post("/api/v1/careers/match", json={"profile": PROFILE_JSON})
    assert response.status_code == 200
    assert response.json()["data_mode"] == "fixture"


def test_fixture_mode_is_the_default_without_any_env_var(monkeypatch):
    monkeypatch.delenv("ENABLE_FIXTURES", raising=False)
    settings = Settings(_env_file=None)
    assert settings.ENABLE_FIXTURES is True


# --- 2. Missing credentials do not prevent fixture-mode startup ------------


def test_settings_without_credentials_still_serve_fixture_routes_via_di(client: TestClient):
    """Two things verified here, deliberately kept separate:

    (a) Settings() construction tolerates every credential being absent
        and doesn't raise — checked directly on the instance below.
    (b) That same no-credentials instance is wired in through
        app.dependency_overrides[get_settings] (the real FastAPI
        dependency-injection path, not just a standalone object), and the
        fixture-mode request path still works end to end.

    This does NOT test the module-level `app` object's own startup — that
    already happened at import time, before this test ever runs, and is
    unaffected by anything here. If that needs covering, it would require
    constructing a fresh FastAPI app/TestClient after clearing credentials,
    which this test does not do.
    """
    settings_without_credentials = Settings(
        LLM_API_KEY=None,
        RUNPOD_API_KEY=None,
        RUNPOD_ENDPOINT_ID=None,
        TREND_SOURCE_API_KEY=None,
        _env_file=None,
    )
    assert settings_without_credentials.LLM_API_KEY is None
    assert settings_without_credentials.RUNPOD_API_KEY is None

    app.dependency_overrides[get_settings] = lambda: settings_without_credentials
    try:
        assert client.get("/api/v1/health").status_code == 200
        assert client.post("/api/v1/careers/match", json={"profile": PROFILE_JSON}).status_code == 200
    finally:
        del app.dependency_overrides[get_settings]


# --- 3. Invalid provider configuration is rejected clearly ------------------


def test_invalid_enable_fixtures_value_is_rejected(monkeypatch):
    monkeypatch.setenv("ENABLE_FIXTURES", "not-a-boolean")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_non_positive_provider_timeout_is_rejected(monkeypatch):
    monkeypatch.setenv("PROVIDER_TIMEOUT_SECONDS", "0")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


# --- 4 & 5. Real mode cannot silently use fixture output; errors map to the
#            established contract envelope -----------------------------------


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("post", "/api/v1/careers/match", {"profile": PROFILE_JSON}),
        ("post", "/api/v1/scenarios/simulate", {"profile": PROFILE_JSON, "scenario_id": "moderate"}),
        ("post", "/api/v1/roadmaps/generate", {"profile": PROFILE_JSON, "role_id": "data_analyst"}),
        ("post", "/api/v1/projects/recommend", {"profile": PROFILE_JSON, "role_id": "data_analyst"}),
        (
            "post",
            "/api/v1/projects/simulate",
            {
                "profile": PROFILE_JSON,
                "role_id": "data_analyst",
                "project_id": "project_data_dashboard_001",
            },
        ),
    ],
)
def test_disabling_fixtures_fails_loudly_instead_of_serving_fixture_output(
    client: TestClient, method, path, body
):
    app.dependency_overrides[get_settings] = lambda: Settings(ENABLE_FIXTURES=False, _env_file=None)
    try:
        response = getattr(client, method)(path, json=body)
    finally:
        del app.dependency_overrides[get_settings]

    assert response.status_code == 503
    error = response.json()["error"]
    assert error["code"] == "PROVIDER_UNAVAILABLE"
    assert "request_id" in response.json()
    # The one thing that must never happen: fixture data served while
    # claiming the request succeeded.
    assert "matches" not in response.text and "catalog_coverage" not in response.text


def test_enable_fixtures_true_is_unaffected_control_case(client: TestClient):
    """Sanity check for the parametrized test above: the same routes work
    normally when ENABLE_FIXTURES stays true (the default)."""
    app.dependency_overrides[get_settings] = lambda: Settings(ENABLE_FIXTURES=True, _env_file=None)
    try:
        response = client.post("/api/v1/careers/match", json={"profile": PROFILE_JSON})
    finally:
        del app.dependency_overrides[get_settings]

    assert response.status_code == 200


# --- 6. Timeout and unavailable conditions handled by fake providers -------


def test_fake_provider_unavailable_maps_to_contract_error(client: TestClient):
    class AlwaysUnavailableProvider:
        def match(self, profile, roles, scenario, signals):
            raise provider_unavailable("MatchingProvider", "fake test double is down")

    app.dependency_overrides[get_matching_provider] = lambda: AlwaysUnavailableProvider()
    try:
        response = client.post("/api/v1/careers/match", json={"profile": PROFILE_JSON})
    finally:
        del app.dependency_overrides[get_matching_provider]

    assert response.status_code == 503
    error = response.json()["error"]
    assert error["code"] == "PROVIDER_UNAVAILABLE"
    assert "MatchingProvider" in error["message"]
    assert "fake test double is down" in error["message"]
    # Matches every other AppError in this codebase (PROFILE_NOT_FOUND,
    # ROLE_NOT_FOUND, PROJECT_NOT_FOUND, ...): details stays null outside
    # the validation-error handler.
    assert error["details"] is None


def test_fake_provider_timeout_maps_to_contract_error(client: TestClient):
    class AlwaysTimesOutProvider:
        def match(self, profile, roles, scenario, signals):
            raise provider_timeout("MatchingProvider", timeout_seconds=5.0)

    app.dependency_overrides[get_matching_provider] = lambda: AlwaysTimesOutProvider()
    try:
        response = client.post("/api/v1/careers/match", json={"profile": PROFILE_JSON})
    finally:
        del app.dependency_overrides[get_matching_provider]

    assert response.status_code == 504
    error = response.json()["error"]
    assert error["code"] == "PROVIDER_TIMEOUT"
    assert "MatchingProvider" in error["message"]
    assert "5.0" in error["message"]
    assert error["details"] is None


def test_provider_error_is_distinct_from_invalid_input_error(client: TestClient):
    """Provider-unavailable (503) and invalid student input (422) must use
    different, unambiguous status codes and error codes."""
    app.dependency_overrides[get_settings] = lambda: Settings(ENABLE_FIXTURES=False, _env_file=None)
    try:
        provider_error = client.post("/api/v1/careers/match", json={"profile": PROFILE_JSON})
    finally:
        del app.dependency_overrides[get_settings]

    invalid_input_error = client.post(
        "/api/v1/careers/match", json={"profile": {"interests": [], "projects": []}}  # missing "skills"
    )

    assert provider_error.status_code == 503
    assert invalid_input_error.status_code == 422
    assert provider_error.json()["error"]["code"] != invalid_input_error.json()["error"]["code"]


# --- 7. Secret values are not leaked into responses or logs ----------------


def test_secret_settings_are_masked_in_repr_and_str(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-super-secret-value")
    monkeypatch.setenv("RUNPOD_API_KEY", "rp-super-secret-value")
    monkeypatch.setenv("TREND_SOURCE_API_KEY", "ts-super-secret-value")
    settings = Settings(_env_file=None)

    dumped = repr(settings) + str(settings) + str(settings.model_dump())
    assert "sk-super-secret-value" not in dumped
    assert "rp-super-secret-value" not in dumped
    assert "ts-super-secret-value" not in dumped


def test_secret_settings_still_usable_via_explicit_get_secret_value(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-super-secret-value")
    settings = Settings(_env_file=None)
    assert settings.LLM_API_KEY.get_secret_value() == "sk-super-secret-value"


def test_health_endpoint_never_echoes_configured_secrets(monkeypatch, client: TestClient):
    """No current /health code reads any provider credential at all, so
    this can't fail today — it exists as a cheap, low-cost guard against
    a future change accidentally wiring a secret into this (or any
    similarly unrelated) response."""
    monkeypatch.setenv("LLM_API_KEY", "sk-super-secret-value")
    response = client.get("/api/v1/health")
    assert "sk-super-secret-value" not in response.text


# --- 8. Existing dependency overrides remain functional ---------------------


def test_matching_provider_override_still_takes_precedence_over_settings_gate(client: TestClient):
    """An explicit provider override must win even when ENABLE_FIXTURES is
    false — proves the two override mechanisms (settings-driven default vs.
    direct provider override) coexist without interference."""

    class StubProvider:
        def match(self, profile, roles, scenario, signals):
            return []

    app.dependency_overrides[get_settings] = lambda: Settings(ENABLE_FIXTURES=False, _env_file=None)
    app.dependency_overrides[get_matching_provider] = lambda: StubProvider()
    try:
        response = client.post("/api/v1/careers/match", json={"profile": PROFILE_JSON})
    finally:
        del app.dependency_overrides[get_settings]
        del app.dependency_overrides[get_matching_provider]

    assert response.status_code == 200
    assert response.json()["data"]["matches"] == []
