from fastapi.testclient import TestClient

from app.api.v1.endpoints.trends import get_trend_provider
from app.main import app
from app.services.trend_provider import FixtureTrendProvider, TrendResult


def test_openapi_includes_trends():
    schema = app.openapi()
    assert "/api/v1/trends" in schema["paths"]
    assert "get" in schema["paths"]["/api/v1/trends"]


def test_trends_default_returns_contract_envelope(client: TestClient):
    response = client.get("/api/v1/trends")
    assert response.status_code == 200

    body = response.json()
    assert body["data_mode"] == "fixture"
    assert isinstance(body["warnings"], list) and body["warnings"]

    payload = body["data"]
    assert payload["source_status"] in ("ok", "stale", "unavailable")
    assert payload["last_successful_refresh_at"] is None
    assert isinstance(payload["signals"], list)


def test_trends_signal_has_required_provenance_fields(client: TestClient):
    response = client.get("/api/v1/trends")
    signals = response.json()["data"]["signals"]
    assert signals  # default fixture set is non-empty

    signal = signals[0]
    for field in (
        "signal_id",
        "skill_id",
        "source_id",
        "signal_type",
        "metric_name",
        "observed_at",
        "retrieved_at",
        "direction",
        "confidence_note",
        "role_ids",
    ):
        assert field in signal

    # Dates are UTC ISO-8601 with trailing Z, and distinct fields.
    assert signal["observed_at"].endswith("Z")
    assert signal["retrieved_at"].endswith("Z")
    assert "synthetic" in signal["confidence_note"].lower()


def test_trends_filters_by_known_role_id(client: TestClient):
    response = client.get("/api/v1/trends", params={"role_id": "data_analyst"})
    payload = response.json()["data"]

    assert payload["source_status"] == "stale"
    assert all("data_analyst" in s["role_ids"] for s in payload["signals"])
    assert len(payload["signals"]) >= 1


def test_trends_unknown_role_id_returns_honest_unavailable_state(client: TestClient):
    response = client.get("/api/v1/trends", params={"role_id": "no_such_role"})
    assert response.status_code == 200

    payload = response.json()["data"]
    assert payload["signals"] == []
    assert payload["source_status"] == "unavailable"


def test_trends_limit_truncates_results(client: TestClient):
    response = client.get("/api/v1/trends", params={"limit": 1})
    assert len(response.json()["data"]["signals"]) == 1


def test_trend_provider_dependency_is_overridable(client: TestClient):
    class StubTrendProvider:
        def latest(self, role_id=None):
            return TrendResult(signals=[], last_successful_refresh_at=None, source_status="ok")

    app.dependency_overrides[get_trend_provider] = lambda: StubTrendProvider()
    try:
        response = client.get("/api/v1/trends")
    finally:
        del app.dependency_overrides[get_trend_provider]

    assert response.json()["data"]["source_status"] == "ok"


def test_fixture_trend_provider_requires_no_settings_or_credentials(monkeypatch):
    for var in ("LLM_API_KEY", "RUNPOD_API_KEY", "TREND_SOURCE_API_KEY"):
        monkeypatch.delenv(var, raising=False)

    result = FixtureTrendProvider().latest()
    assert isinstance(result, TrendResult)
