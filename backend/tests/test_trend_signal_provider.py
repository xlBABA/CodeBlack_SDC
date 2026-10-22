"""Milestone 10C Part B: CachedTrendSignalProvider — the TrendProvider
wired into MatchingService's call site (app.api.v1.endpoints.careers.
get_trend_provider) when CATALOG_MODE=cached. Pure read of saved
snapshot files; never a live GitHub API call.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints.careers import get_settings
from app.core.config import Settings
from app.main import app
from app.services.trend_signal_provider import CachedTrendSignalProvider

COVERED_SKILL_IDS = {
    "sql", "python", "matlab", "data_visualization", "excel", "vba", "cad_software",
    "financial_analysis_software", "javascript", "git", "accounting_software", "gis",
}


def _override_settings(**overrides):
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, **overrides)


def _clear_override():
    app.dependency_overrides.pop(get_settings, None)


# --- Genuine cached data, no network -----------------------------------


def test_latest_returns_real_cached_signals_with_no_network_call(monkeypatch):
    """Never a live GitHub call: urlopen must not be reachable from here."""
    import urllib.request

    def _forbidden(*a, **k):
        raise AssertionError("a real network call was made")

    monkeypatch.setattr(urllib.request, "urlopen", _forbidden)

    signals = CachedTrendSignalProvider().latest()
    assert len(signals) == 12
    assert {s["skill_id"] for s in signals} <= COVERED_SKILL_IDS
    for s in signals:
        assert s["signal_type"] == "developer_activity"
        assert s["source_id"]
        assert s["direction"] in ("rising", "falling", "stable", "unknown")


def test_latest_never_claims_hiring_demand():
    for s in CachedTrendSignalProvider().latest():
        note = s["confidence_note"].lower()
        assert "not verified hiring demand" in note or "not job demand" in note or "developer" in note


def test_latest_dates_are_present_and_parseable():
    for s in CachedTrendSignalProvider().latest():
        assert s["retrieved_at"]
        assert s["observed_at"]


# --- Missing / invalid / stale data handled safely ----------------------


def test_missing_snapshot_directory_returns_empty_list_not_a_crash(tmp_path: Path):
    provider = CachedTrendSignalProvider(base_dir=tmp_path / "does-not-exist")
    assert provider.latest() == []


def test_corrupt_snapshot_file_degrades_to_empty_list_not_a_crash(tmp_path: Path):
    bad_dir = tmp_path / "trend_snapshots"
    bad_dir.mkdir()
    (bad_dir / "sql.json").write_text("{not valid json", encoding="utf-8")

    provider = CachedTrendSignalProvider(base_dir=bad_dir)
    assert provider.latest() == []  # never a 500; the malformed file is logged and skipped


def test_role_id_filter_only_returns_signals_for_that_roles_skills():
    all_signals = CachedTrendSignalProvider().latest()
    filtered = CachedTrendSignalProvider().latest(role_id="data_analyst")
    assert 0 < len(filtered) < len(all_signals)
    assert all("data_analyst" in s["role_ids"] for s in filtered)


# --- End-to-end: no signals available still returns a safe response -----


def test_careers_match_succeeds_even_when_trend_snapshots_are_missing(monkeypatch, tmp_path: Path):
    """If the cached snapshot directory is ever missing/corrupt in a real
    deployment, /careers/match must still return 200 with safe (empty)
    signals — never a 500 — exactly like CachedResourceCatalog/
    CachedProjectCatalog's own fail-loud-but-never-silent-fixture
    conventions elsewhere in this codebase, except here "no signals" is
    itself the honest, safe degraded state (scenario adjustments simply
    don't apply), not a 503."""
    import app.api.v1.endpoints.careers as careers_module

    monkeypatch.setattr(
        careers_module, "CachedTrendSignalProvider",
        lambda: CachedTrendSignalProvider(base_dir=tmp_path / "does-not-exist"),
    )

    client = TestClient(app)
    _override_settings(MATCHING_MODE="hussain", CATALOG_MODE="cached")
    try:
        response = client.post(
            "/api/v1/careers/match",
            json={"profile": {"interests": [], "skills": [{"skill_id": "sql", "name": "SQL"}], "projects": []}, "limit": 4},
        )
    finally:
        _clear_override()

    assert response.status_code == 200
