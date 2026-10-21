"""Tests for scripts/smoke_test.py, run in-process against the fixture app
via the same TestClient fixture every other test in this suite uses — no
live server or real network call needed. (An httpx.ASGITransport-based
sync client was tried first, but this installed httpx version only
implements the async ASGI transport; TestClient already provides the
exact .get()/.post() interface the smoke-test functions need.)"""
import pytest
from fastapi.testclient import TestClient

import scripts.smoke_test as smoke_test_module
from app.core.config import Settings, get_settings
from app.main import app
from scripts.smoke_test import (
    EXIT_FAILURE,
    EXIT_OK,
    EXIT_WARNING,
    SmokeTestFailure,
    _check_careers_match,
    _check_health,
    run,
)


def test_check_health_passes_against_fixture_app(client: TestClient):
    assert _check_health(client) == "ok"


def test_check_careers_match_passes_against_fixture_app(client: TestClient):
    assert _check_careers_match(client) == "ok"


def test_check_careers_match_returns_warn_on_disclosed_provider_unavailable(client: TestClient):
    """A 503 PROVIDER_UNAVAILABLE is a correctly-functioning, disclosed
    state (Milestone 6A) — the smoke check must report it as a warning,
    not raise and not report a clean "ok"."""
    app.dependency_overrides[get_settings] = lambda: Settings(ENABLE_FIXTURES=False, _env_file=None)
    try:
        assert _check_careers_match(client) == "warn"
    finally:
        del app.dependency_overrides[get_settings]


def test_check_health_raises_smoke_test_failure_on_unexpected_status(client: TestClient, monkeypatch):
    class FakeResponse:
        status_code = 500

        def json(self):
            return {}

    monkeypatch.setattr(client, "get", lambda path: FakeResponse())
    with pytest.raises(SmokeTestFailure):
        _check_health(client)


def test_smoke_test_never_calls_profile_analyze():
    """Static guard: the smoke test must stay read-only/non-destructive —
    it should never issue an HTTP call to the profile persistence write
    path. (Explanatory comments mentioning "profile/analyze" by name are
    fine and expected; an actual call to that path is not.)"""
    import inspect

    source = inspect.getsource(smoke_test_module)
    assert 'client.post("/api/v1/profile/analyze"' not in source
    assert '"profile_id":' not in source


# --- run()'s exit-code aggregation ------------------------------------------
# Patches module-level CHECKS with small fakes to test the aggregation logic
# in isolation (no network — httpx.Client(base_url=...) is constructed but
# never actually sends a request since the fakes ignore `client`).


def _patch_checks(monkeypatch, *fakes):
    monkeypatch.setattr(smoke_test_module, "CHECKS", tuple(fakes))


def test_run_returns_exit_ok_when_every_check_passes(monkeypatch):
    _patch_checks(monkeypatch, lambda client: "ok", lambda client: "ok")
    assert run("http://irrelevant.invalid") == EXIT_OK


def test_run_returns_exit_warning_when_a_check_warns_but_none_fail(monkeypatch):
    _patch_checks(monkeypatch, lambda client: "ok", lambda client: "warn")
    assert run("http://irrelevant.invalid") == EXIT_WARNING


def test_run_returns_exit_failure_when_any_check_fails(monkeypatch):
    def failing_check(client):
        raise SmokeTestFailure("boom")

    _patch_checks(monkeypatch, lambda client: "ok", failing_check)
    assert run("http://irrelevant.invalid") == EXIT_FAILURE


def test_run_failure_takes_precedence_over_warning(monkeypatch):
    def failing_check(client):
        raise SmokeTestFailure("boom")

    _patch_checks(monkeypatch, lambda client: "warn", failing_check)
    assert run("http://irrelevant.invalid") == EXIT_FAILURE


def test_run_end_to_end_returns_exit_warning_for_a_real_503(monkeypatch, client: TestClient):
    """End-to-end: the real _check_health/_check_careers_match functions,
    against the real fixture app, with ENABLE_FIXTURES=False triggering an
    actual 503 — proves run() surfaces this as exit code 2, not a false
    "All smoke checks passed"."""
    app.dependency_overrides[get_settings] = lambda: Settings(ENABLE_FIXTURES=False, _env_file=None)
    # run() builds its own httpx.Client(base_url=...); swap that
    # construction for the real in-process TestClient fixture so the
    # actual check functions hit the actual fixture app, no live server
    # or network needed.
    monkeypatch.setattr(smoke_test_module.httpx, "Client", lambda base_url, timeout: client)
    try:
        exit_code = run("http://irrelevant.invalid")
    finally:
        del app.dependency_overrides[get_settings]

    assert exit_code == EXIT_WARNING
