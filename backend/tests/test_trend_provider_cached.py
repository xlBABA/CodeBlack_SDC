"""Milestone 6D-2A: loading and validation only for Jawad's cached
trend_snapshots/*.json (app/data/cached/trend_snapshots/). Nothing here
wires a TrendProvider into GET /trends or MatchingService — see
trend_provider_cached.py's docstring. Validates against Jawad's own
source_status enum (live|cached|unavailable) only; the translation to
the public contract's ok|stale|unavailable is documented, not
implemented, here (see the module docstring and the 6D-2A report)."""
import json

import pytest

from app.services.role_catalog_cached import CachedCatalogError
from app.services.trend_provider_cached import (
    _validate_snapshot,
    _validate_window,
    load_cached_trend_snapshots,
)

EXPECTED_SNAPSHOT_COUNT = 12
CANONICAL_SKILL_IDS = {
    "critical_thinking", "mathematics", "complex_problem_solving", "systems_analysis",
    "attention_to_detail", "excel", "sql", "python", "data_visualization", "cad_software",
    "matlab", "financial_analysis_software", "analytical_scientific_software", "vba",
    "programming", "javascript", "git", "accounting_software", "gis", "science",
}

_BASE_WINDOW = {
    "topic": "sql", "start": "2026-09-22", "end": "2026-10-21", "total_count": 100,
    "incomplete": False, "retrieved_at": "2026-10-21T17:38:40Z",
}
_BASE_SNAPSHOT = {
    "skill_id": "sql", "source_status": "cached", "source_id": "github_search_repos",
    "current": _BASE_WINDOW,
    "previous": {**_BASE_WINDOW, "retrieved_at": "2026-09-21T17:38:38Z", "total_count": 90},
    "prior_snapshot": None,
}


def test_loads_exactly_the_expected_snapshot_count():
    assert len(load_cached_trend_snapshots()) == EXPECTED_SNAPSHOT_COUNT


def test_every_snapshot_skill_id_is_canonical():
    for snapshot in load_cached_trend_snapshots():
        assert snapshot["skill_id"] in CANONICAL_SKILL_IDS


def test_every_snapshot_skill_id_is_unique_across_files():
    skill_ids = [s["skill_id"] for s in load_cached_trend_snapshots()]
    assert len(skill_ids) == len(set(skill_ids))


def test_no_stored_snapshot_claims_source_status_live():
    """A stored file is, by definition, cached data to any later reader —
    none of the real snapshot files should claim 'live'."""
    for snapshot in load_cached_trend_snapshots():
        assert snapshot["source_status"] != "live"


def test_every_snapshot_source_status_is_one_of_jawads_own_enum():
    for snapshot in load_cached_trend_snapshots():
        assert snapshot["source_status"] in {"live", "cached", "unavailable"}


def test_every_snapshot_source_status_is_not_in_the_public_contract_enum_unchanged():
    """Documents the schema boundary (Step 4): Jawad's "cached" value is
    not a member of the public API's ok|stale|unavailable enum — a
    translation is required before this could ever reach TrendsPayload,
    which this module deliberately does not perform."""
    public_contract_statuses = {"ok", "stale", "unavailable"}
    for snapshot in load_cached_trend_snapshots():
        if snapshot["source_status"] == "cached":
            assert "cached" not in public_contract_statuses


def test_current_window_is_never_retrieved_before_previous_window():
    for snapshot in load_cached_trend_snapshots():
        assert snapshot["current"]["retrieved_at"] >= snapshot["previous"]["retrieved_at"]


def test_every_snapshot_has_a_real_source_id():
    for snapshot in load_cached_trend_snapshots():
        assert snapshot["source_id"] == "github_search_repos"


# --- Malformed input is rejected, not guessed around ----------------------


def test_rejects_missing_required_field():
    bad = dict(_BASE_SNAPSHOT)
    del bad["source_id"]
    with pytest.raises(CachedCatalogError, match="missing fields"):
        _validate_snapshot(bad, {"sql"}, "sql.json")


def test_rejects_unknown_skill_id():
    bad = {**_BASE_SNAPSHOT, "skill_id": "not_a_real_skill"}
    with pytest.raises(CachedCatalogError, match="unknown skill_id"):
        _validate_snapshot(bad, {"sql"}, "not_a_real_skill.json")


def test_rejects_skill_id_filename_mismatch():
    with pytest.raises(CachedCatalogError, match="does not match its own filename"):
        _validate_snapshot(_BASE_SNAPSHOT, {"sql", "python"}, "python.json")


@pytest.mark.parametrize("status", ["unknown", "ok", "stale", ""])
def test_rejects_source_status_outside_jawads_own_enum(status):
    bad = {**_BASE_SNAPSHOT, "source_status": status}
    with pytest.raises(CachedCatalogError, match="source_status"):
        _validate_snapshot(bad, {"sql"}, "sql.json")


def test_rejects_source_status_live_on_a_stored_file():
    bad = {**_BASE_SNAPSHOT, "source_status": "live"}
    with pytest.raises(CachedCatalogError, match="never claim source_status='live'"):
        _validate_snapshot(bad, {"sql"}, "sql.json")


def test_rejects_missing_source_id():
    bad = {**_BASE_SNAPSHOT, "source_id": ""}
    with pytest.raises(CachedCatalogError, match="no source_id"):
        _validate_snapshot(bad, {"sql"}, "sql.json")


def test_rejects_current_retrieved_before_previous():
    bad = {
        **_BASE_SNAPSHOT,
        "current": {**_BASE_WINDOW, "retrieved_at": "2026-01-01T00:00:00Z"},
        "previous": {**_BASE_WINDOW, "retrieved_at": "2026-10-21T17:38:38Z"},
    }
    with pytest.raises(CachedCatalogError, match="before"):
        _validate_snapshot(bad, {"sql"}, "sql.json")


@pytest.mark.parametrize("total_count", [-1, "100", True])
def test_rejects_malformed_total_count(total_count):
    bad_window = {**_BASE_WINDOW, "total_count": total_count}
    with pytest.raises(CachedCatalogError, match="total_count"):
        _validate_window(bad_window, "ctx")


def test_rejects_non_iso8601_timestamp():
    bad_window = {**_BASE_WINDOW, "retrieved_at": "not-a-date"}
    with pytest.raises(CachedCatalogError, match="ISO 8601"):
        _validate_window(bad_window, "ctx")


def test_rejects_timezone_naive_timestamp():
    bad_window = {**_BASE_WINDOW, "retrieved_at": "2026-10-21T17:38:40"}
    with pytest.raises(CachedCatalogError, match="timezone-aware"):
        _validate_window(bad_window, "ctx")


def test_rejects_malformed_window_missing_fields():
    bad_window = dict(_BASE_WINDOW)
    del bad_window["total_count"]
    with pytest.raises(CachedCatalogError, match="missing fields"):
        _validate_window(bad_window, "ctx")


# --- File-directory-level behavior, using real temporary fixtures --------


def test_missing_directory_fails_closed(monkeypatch, tmp_path):
    import app.services.trend_provider_cached as module

    monkeypatch.setattr(module, "_TREND_SNAPSHOTS_DIR", tmp_path / "does_not_exist")
    with pytest.raises(CachedCatalogError, match="does not exist"):
        module.load_cached_trend_snapshots()


def test_duplicate_skill_id_across_two_files_is_rejected(monkeypatch, tmp_path):
    import app.services.trend_provider_cached as module

    (tmp_path / "sql.json").write_text(json.dumps(_BASE_SNAPSHOT), encoding="utf-8")
    (tmp_path / "sql_dup.json").write_text(json.dumps(_BASE_SNAPSHOT), encoding="utf-8")
    monkeypatch.setattr(module, "_TREND_SNAPSHOTS_DIR", tmp_path)
    monkeypatch.setattr(module, "_validate_snapshot", lambda *a, **k: None)  # skip filename-match check
    with pytest.raises(CachedCatalogError, match="Duplicate skill_id"):
        module.load_cached_trend_snapshots()


def test_malformed_json_in_one_file_fails_closed_not_silently_skipped(monkeypatch, tmp_path):
    import app.services.trend_provider_cached as module

    (tmp_path / "sql.json").write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(module, "_TREND_SNAPSHOTS_DIR", tmp_path)
    with pytest.raises(json.JSONDecodeError):
        module.load_cached_trend_snapshots()


def test_valid_data_still_loads_unchanged_after_validation_hardening():
    assert len(load_cached_trend_snapshots()) == EXPECTED_SNAPSHOT_COUNT
