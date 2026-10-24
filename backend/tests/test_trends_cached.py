"""Milestone 12A: GET /trends under CATALOG_MODE=cached now returns the
same 12 real, dated, cached GitHub developer-activity signals that
MatchingService/scenarios already consume via CachedTrendSignalProvider
(app.services.trend_signal_provider) — fixing the discrepancy where
matching used real cached signals but this route still showed fixture
demo data.

Every test here is a pure read of the committed app/data/cached/
trend_snapshots/*.json files (or, for the failure-mode tests, a tmp_path
standing in for that directory) — never a live GitHub call.
"""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.api.v1.endpoints.trends import get_trend_provider
from app.core.config import Settings, get_settings
from app.main import app
from app.services.trend_provider import CachedGithubTrendProvider
from app.services.trend_signal_provider import CachedTrendSignalProvider

COVERED_SKILL_IDS = {
    "sql", "python", "matlab", "data_visualization", "excel", "vba", "cad_software",
    "financial_analysis_software", "javascript", "git", "accounting_software", "gis",
}


def _override_settings(**overrides):
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, **overrides)


def _clear_override():
    app.dependency_overrides.pop(get_settings, None)


# --- Cached mode returns the real 12 signals, not fixture demo data --------


def test_trends_cached_mode_returns_all_twelve_real_signals(client: TestClient):
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.get("/api/v1/trends", params={"limit": 50})
    finally:
        _clear_override()

    assert response.status_code == 200
    body = response.json()
    assert body["data_mode"] == "cached"
    signals = body["data"]["signals"]
    assert len(signals) == 12
    assert {s["skill_id"] for s in signals} == COVERED_SKILL_IDS
    # Never the fixture demo signal ids/skills.
    assert {s["skill_id"] for s in signals}.isdisjoint({"financial_modeling", "cad"})


def test_trends_cached_mode_matches_the_same_signals_matching_uses(client: TestClient):
    """Requirement 2: GET /trends must show the identical underlying cached
    signals that MatchingService/scenarios already use via
    CachedTrendSignalProvider — not a second, independently-sourced copy."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.get("/api/v1/trends", params={"limit": 50})
    finally:
        _clear_override()

    via_trends_endpoint = {s["skill_id"]: s["metric_value"] for s in response.json()["data"]["signals"]}
    via_matching_provider = {s["skill_id"]: s["metric_value"] for s in CachedTrendSignalProvider().latest()}
    assert via_trends_endpoint == via_matching_provider


def test_trends_cached_mode_source_status_and_data_mode(client: TestClient):
    """Requirement 7: cached snapshots map to data_mode='cached' and the
    public contract's source_status='stale' (never Jawad's own internal
    'cached' value, which isn't a member of the public SourceStatus enum)."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.get("/api/v1/trends")
    finally:
        _clear_override()

    body = response.json()
    assert body["data_mode"] == "cached"
    assert body["data"]["source_status"] == "stale"
    assert body["data"]["last_successful_refresh_at"] is not None


def test_trends_cached_mode_signals_are_labeled_developer_activity_not_hiring_demand(client: TestClient):
    """Requirement 5: never presented as hiring demand/vacancies."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.get("/api/v1/trends", params={"limit": 50})
    finally:
        _clear_override()

    body = response.json()
    assert any("not verified hiring demand" in w.lower() or "hiring demand" in w.lower() for w in body["warnings"])
    for signal in body["data"]["signals"]:
        assert signal["signal_type"] == "developer_activity"
        note = signal["confidence_note"].lower()
        assert "not verified hiring demand" in note or "developer" in note


def test_trends_cached_mode_signals_carry_dates_and_source_attribution(client: TestClient):
    """Requirement 6: observation/retrieval dates, source attribution, and
    confidence notes are all present."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.get("/api/v1/trends", params={"limit": 50})
    finally:
        _clear_override()

    for signal in response.json()["data"]["signals"]:
        assert signal["observed_at"]
        assert signal["retrieved_at"]
        assert signal["source_id"] == "github_search_repos"
        assert signal["confidence_note"]


# --- role_id filtering uses real role IDs -----------------------------------


def test_trends_cached_mode_filters_by_a_real_role_id(client: TestClient):
    """Requirement 8: role filtering must work against the actual
    app/data/cached/roles.json role IDs, not fixture role ids."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.get("/api/v1/trends", params={"role_id": "data_analyst", "limit": 50})
    finally:
        _clear_override()

    body = response.json()
    signals = body["data"]["signals"]
    assert signals
    assert all("data_analyst" in s["role_ids"] for s in signals)
    # Milestone 13B-8: Jawad added "python" as a required data_analyst
    # skill (roles.json), so its trend signal now carries this role_id too.
    assert {s["skill_id"] for s in signals} <= {"sql", "data_visualization", "excel", "python"}
    assert body["data"]["source_status"] == "stale"


def test_trends_cached_mode_unknown_role_id_is_honestly_unavailable(client: TestClient):
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.get("/api/v1/trends", params={"role_id": "no_such_role"})
    finally:
        _clear_override()

    body = response.json()
    assert body["data"]["signals"] == []
    assert body["data"]["source_status"] == "unavailable"
    assert any("no saved trend signal" in w.lower() for w in body["warnings"])


def test_trends_cached_mode_limit_still_truncates(client: TestClient):
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.get("/api/v1/trends", params={"limit": 3})
    finally:
        _clear_override()

    assert len(response.json()["data"]["signals"]) == 3


# --- Missing/corrupted snapshots degrade gracefully, never fixture data ----


def test_trends_cached_mode_missing_snapshot_directory_degrades_gracefully(client: TestClient, tmp_path: Path):
    _override_settings(CATALOG_MODE="cached")
    app.dependency_overrides[get_trend_provider] = lambda: CachedGithubTrendProvider(
        base_dir=tmp_path / "does-not-exist"
    )
    try:
        response = client.get("/api/v1/trends")
    finally:
        del app.dependency_overrides[get_trend_provider]
        _clear_override()

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["signals"] == []
    assert body["data"]["source_status"] == "unavailable"
    # Never silently fixture data in its place, even though the snapshot
    # directory is unreadable — CATALOG_MODE=cached still means "cached",
    # just with an honest empty result.
    assert body["data_mode"] == "cached"


def test_trends_cached_mode_corrupt_snapshot_file_degrades_gracefully(client: TestClient, tmp_path: Path):
    bad_dir = tmp_path / "trend_snapshots"
    bad_dir.mkdir()
    (bad_dir / "sql.json").write_text("{not valid json", encoding="utf-8")

    _override_settings(CATALOG_MODE="cached")
    app.dependency_overrides[get_trend_provider] = lambda: CachedGithubTrendProvider(base_dir=bad_dir)
    try:
        response = client.get("/api/v1/trends")
    finally:
        del app.dependency_overrides[get_trend_provider]
        _clear_override()

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["signals"] == []
    assert body["data"]["source_status"] == "unavailable"


def test_cached_github_trend_provider_never_opens_a_real_socket(monkeypatch):
    """Direct provider-level check that get_trends() is a pure snapshot
    read — no live GitHub call, ever (requirement 10)."""
    import urllib.request

    def _forbidden(*a, **k):
        raise AssertionError("a real network call was made")

    monkeypatch.setattr(urllib.request, "urlopen", _forbidden)

    result = CachedGithubTrendProvider().latest()
    assert len(result.signals) == 12


# --- Fixture mode is unchanged ----------------------------------------------


def test_trends_fixture_mode_still_returns_fixture_demo_signals_unchanged(client: TestClient):
    """Requirement 3: CATALOG_MODE=fixture (explicit or default) must keep
    behaving exactly as before Milestone 12A."""
    _override_settings(CATALOG_MODE="fixture")
    try:
        response = client.get("/api/v1/trends")
    finally:
        _clear_override()

    body = response.json()
    assert body["data_mode"] == "fixture"
    assert body["data"]["last_successful_refresh_at"] is None
    signals = body["data"]["signals"]
    assert signals
    assert all("synthetic" in s["confidence_note"].lower() for s in signals)
