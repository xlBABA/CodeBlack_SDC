"""Minimal smoke test against a running deployment (local or Replit).

Usage:
    backend\\.venv\\Scripts\\python.exe -m scripts.smoke_test
    SMOKE_TEST_BASE_URL=https://your-repl-url backend\\.venv\\Scripts\\python.exe -m scripts.smoke_test

Defaults to http://127.0.0.1:8000 if SMOKE_TEST_BASE_URL is unset. Hits
only read-safe, contract-defined endpoints with synthetic inline data —
never a real CV, never a profile_id (so it never touches the database
write path, and makes no destructive or persistent change). Reports
pass/warn/fail per check against the actual response; never prints a
passing result without one.

Exit codes:
    0  every check passed cleanly — no warnings.
    1  at least one check failed (takes precedence over any warning).
    2  no failures, but at least one check completed with a warning
       (e.g. a disclosed 503 PROVIDER_UNAVAILABLE) — not a clean pass.
"""
from __future__ import annotations

import os
import sys

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8000"

# Synthetic, fictional profile — same shape as app/fixtures/sample_profiles.py.
# No real personal data; never persisted (no profile_id, /profile/analyze
# is not called).
SYNTHETIC_PROFILE = {
    "interests": ["analytics"],
    "skills": [{"skill_id": "sql", "name": "SQL"}, {"skill_id": "python", "name": "Python"}],
    "projects": [],
}


class SmokeTestFailure(Exception):
    pass


# A check returns "ok" or "warn" (and prints its own [ok]/[warn] line), or
# raises SmokeTestFailure. run() turns these into exit codes: 0 only for an
# all-"ok" run, 2 if there's a warning but no failure, 1 if there's any
# failure at all (failure always takes precedence over warning).


def _check_health(client: httpx.Client) -> str:
    response = client.get("/api/v1/health")
    if response.status_code != 200:
        raise SmokeTestFailure(f"GET /api/v1/health -> {response.status_code}")
    body = response.json()
    if body.get("status") != "ok":
        raise SmokeTestFailure(f"GET /api/v1/health status={body.get('status')!r}, expected 'ok'")
    print(f"[ok] GET /api/v1/health -> status=ok, version={body.get('version')}")
    return "ok"


def _check_careers_match(client: httpx.Client) -> str:
    response = client.post("/api/v1/careers/match", json={"profile": SYNTHETIC_PROFILE})

    if response.status_code == 503:
        # Honest, contract-compatible "real mode requested, no real
        # provider implemented yet" state (app/core/integration_errors.py)
        # — a correctly-functioning refusal, not a smoke-test failure, but
        # also not a clean pass: it means the deployment can't currently
        # serve matching at all, which the overall exit code must reflect.
        print(
            "[warn] POST /api/v1/careers/match -> 503 PROVIDER_UNAVAILABLE "
            "(ENABLE_FIXTURES=false and no real provider is implemented yet)"
        )
        return "warn"

    if response.status_code != 200:
        raise SmokeTestFailure(f"POST /api/v1/careers/match -> {response.status_code}: {response.text}")

    body = response.json()
    data_mode = body.get("data_mode")
    if data_mode not in ("fixture", "live", "cached"):
        raise SmokeTestFailure(f"POST /api/v1/careers/match -> unexpected data_mode {data_mode!r}")

    label = "FIXTURE — synthetic, not a real match" if data_mode == "fixture" else data_mode.upper()
    match_count = len(body.get("data", {}).get("matches", []))
    print(f"[ok] POST /api/v1/careers/match -> data_mode={data_mode} [{label}], {match_count} match(es)")
    return "ok"


CHECKS = (_check_health, _check_careers_match)

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_WARNING = 2


def run(base_url: str) -> int:
    print(f"Smoke-testing {base_url} ...")
    failures: list[str] = []
    warnings: list[str] = []

    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        for check in CHECKS:
            try:
                result = check(client)
            except SmokeTestFailure as exc:
                failures.append(str(exc))
                print(f"[FAIL] {exc}")
                continue
            except httpx.HTTPError as exc:
                failures.append(f"{check.__name__}: {exc}")
                print(f"[FAIL] {check.__name__}: could not reach {base_url} ({exc})")
                continue

            if result == "warn":
                warnings.append(check.__name__)

    if failures:
        print(f"\n{len(failures)} check(s) failed.")
        return EXIT_FAILURE

    if warnings:
        print(f"\n{len(warnings)} check(s) completed with a warning — not a clean pass.")
        return EXIT_WARNING

    print("\nAll smoke checks passed.")
    return EXIT_OK


def main() -> int:
    base_url = os.environ.get("SMOKE_TEST_BASE_URL", DEFAULT_BASE_URL)
    return run(base_url)


if __name__ == "__main__":
    sys.exit(main())
