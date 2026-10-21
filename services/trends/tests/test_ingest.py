import shutil
import tempfile
from datetime import date
from pathlib import Path

from services.trends import ingest
from services.trends.github_client import GitHubTrendClient
from services.trends.tests.fakes import FakeClock, ScriptedTransport, github_response, http_error, no_sleep

TODAY = date(2026, 10, 21)


def _tmp_dir() -> Path:
    return Path(tempfile.mkdtemp())


def _client(transport: ScriptedTransport, n_timestamps: int = 10) -> GitHubTrendClient:
    return GitHubTrendClient(
        transport=transport, sleep_fn=no_sleep,
        clock=FakeClock(["2026-10-21T12:00:00Z"] * n_timestamps),
    )


def test_first_ever_refresh_fetches_both_windows_and_saves_a_snapshot():
    tmp = _tmp_dir()
    try:
        transport = ScriptedTransport([github_response(100), github_response(130)])
        client = _client(transport)
        signal, status = ingest.refresh_skill(
            "sql", "sql", client, role_ids=["data_analyst"], base_dir=tmp, today=TODAY
        )
        assert status == "live"
        assert len(transport.calls) == 2  # previous window, then current window
        assert signal["direction"] == "rising"  # 100 -> 130 is +30%
        assert signal["metric_value"] == 130
        assert (tmp / "sql.json").exists()
    finally:
        shutil.rmtree(tmp)


def test_second_refresh_same_day_reuses_cached_previous_window():
    tmp = _tmp_dir()
    try:
        transport = ScriptedTransport([
            github_response(100),  # 1st refresh: previous
            github_response(130),  # 1st refresh: current
            github_response(140),  # 2nd refresh: current only
        ])
        client = _client(transport)
        ingest.refresh_skill("sql", "sql", client, role_ids=[], base_dir=tmp, today=TODAY)
        signal, status = ingest.refresh_skill("sql", "sql", client, role_ids=[], base_dir=tmp, today=TODAY)
        assert status == "live"
        assert len(transport.calls) == 3  # not 4: previous window was reused
        assert signal["metric_value"] == 140
    finally:
        shutil.rmtree(tmp)


def test_fetch_failure_with_no_snapshot_is_unavailable_not_fake_live():
    tmp = _tmp_dir()
    try:
        transport = ScriptedTransport([http_error("HTTP 403: rate limited")])
        client = _client(transport)
        signal, status = ingest.refresh_skill("sql", "sql", client, role_ids=[], base_dir=tmp, today=TODAY)
        assert status == "unavailable"
        assert signal["direction"] == "unknown"
        assert signal["metric_value"] is None
        assert "UNAVAILABLE" in signal["confidence_note"]
        assert not (tmp / "sql.json").exists()
    finally:
        shutil.rmtree(tmp)


def test_fetch_failure_with_existing_snapshot_falls_back_to_cached_not_live():
    tmp = _tmp_dir()
    try:
        transport = ScriptedTransport([
            github_response(100),  # successful refresh: previous
            github_response(130),  # successful refresh: current
            http_error("HTTP 503"),  # next refresh: previous window fetch fails
        ])
        client = _client(transport)
        ingest.refresh_skill("sql", "sql", client, role_ids=[], base_dir=tmp, today=TODAY)
        # a later day, so the cached "previous" window no longer matches -> must refetch -> fails
        later = date(2026, 11, 21)
        signal, status = ingest.refresh_skill("sql", "sql", client, role_ids=[], base_dir=tmp, today=later)
        assert status == "cached"
        assert signal["metric_value"] == 130  # the stale, previously-saved count
        assert "STALE (cached snapshot)" in signal["confidence_note"]
    finally:
        shutil.rmtree(tmp)


def test_refresh_all_overall_status_is_cached_when_any_skill_falls_back():
    tmp = _tmp_dir()
    original_covered = dict(ingest.COVERED_SKILLS)
    try:
        ingest.COVERED_SKILLS = {"sql": "sql", "python": "python"}
        transport = ScriptedTransport([
            github_response(100), github_response(130),  # sql: live
            http_error("HTTP 403"),                        # python: fails, no snapshot -> unavailable
        ])
        client = _client(transport)
        result = ingest.refresh_all(client, base_dir=tmp, today=TODAY)
        assert len(result["signals"]) == 2
        assert result["source_status"] == "cached"  # mixed live + unavailable, not claimed fully "live"
        assert result["last_successful_refresh_at"] is not None
    finally:
        ingest.COVERED_SKILLS = original_covered
        shutil.rmtree(tmp)
