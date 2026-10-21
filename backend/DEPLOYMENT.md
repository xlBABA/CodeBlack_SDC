# Backend deployment readiness (Mustaqbal AI, formerly FuturePath AI)

This covers local development and preparation for a future Replit
deployment. **No deployment has been performed from here** — this is
configuration and tooling readiness only.

## Environment variables

All have safe defaults; nothing is required to start the app locally.

| Variable | Required? | Default | Purpose |
|---|---|---|---|
| `APP_NAME` | No | `FuturePath AI Backend` | Display name in `/api/v1/health` and OpenAPI. |
| `APP_VERSION` | No | `0.1.0` | Returned by `/api/v1/health`. |
| `ENVIRONMENT` | No | `development` (app display only) | `start.py` enables reload **only** when this is set to exactly `development` — unset, empty, or any other value (including a typo) disables reload. Unlike most settings here, there is no implicit "assume development" fallback for this specific behavior: developers who want reload through `start.py` must set `ENVIRONMENT=development` explicitly (e.g. in `.env`). |
| `API_V1_PREFIX` | No | `/api/v1` | Must match the frozen contract — do not change. |
| `DATABASE_URL` | No | `sqlite:///./futurepath.db` | See "Database" below before relying on this across restarts. |
| `CORS_ORIGINS` | No | `http://localhost:5173` | Comma-separated list of exact trusted origins. `*` is rejected at startup (the app always sends `allow_credentials=True`, and wildcard + credentials is both browser-rejected and unsafe). |
| `ENABLE_FIXTURES` | No | `true` | `false` makes every matching-dependent route (`careers/match`, `scenarios/simulate`, `roadmaps/generate`, `projects/recommend`, `projects/simulate`) return `503 PROVIDER_UNAVAILABLE` instead of fixture output — there is no real provider to switch to yet. Keep `true` until Hussain's real matcher exists. |
| `PROVIDER_TIMEOUT_SECONDS` | No | `5.0` | Reserved for a future real provider's own HTTP client. Nothing enforces this yet. |
| `PORT` | No (platform-set) | `8000` | Read by `start.py` only. Not a `Settings` field — it controls which port uvicorn binds, not app behavior. |
| `LLM_PROVIDER`, `LLM_API_KEY`, `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT_ID`, `TREND_SOURCE_API_KEY` | No | unset | Placeholders for future integrations (Hussain/Rehan). Leave blank — no real values exist, and none are invented here. The three `*_API_KEY` fields are `SecretStr`, masked in logs/`repr()`. |

Copy `.env.example` to `.env` locally and fill in only what you actually have — never commit `.env` (already git-ignored).

## Local development (Windows) — unchanged

```
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
Still works exactly as before. `start.py` (below) is an *additional* optional entry point, not a replacement.

## Optional launcher (`start.py`)

```
backend\.venv\Scripts\python.exe start.py
```
Binds `0.0.0.0` and reads `PORT` (default `8000`, must be `1`-`65535` — anything else is rejected with a clear error before uvicorn ever starts). Preserves `app.main:app` as the ASGI target.

**Reload is opt-in, not a default.** `start.py` enables reload *only* when `ENVIRONMENT` is set to exactly `development` — not when it's unset, empty, or anything else (including `production`, a typo, or a forgotten variable). If you want reload while running `start.py` locally, set `ENVIRONMENT=development` explicitly in your `.env`. This is deliberately different from the `ENVIRONMENT` default used for display purposes elsewhere — a deployment context must never get reload by accident just because nobody set the variable. The existing manual `uvicorn app.main:app --reload` command is unaffected either way; it keeps working exactly as before, regardless of `ENVIRONMENT`.

## Future Replit use (not configured or deployed yet)

No `.replit`/`replit.nix` file has been created — the team hasn't decided how backend and Mohammad's eventual frontend coexist in one Repl, and getting that wrong is worse than leaving it undecided for now. When ready, the run command would be:
```
cd backend && python start.py
```
Verify on the actual Replit platform first:
- Python version/module availability (this project targets Python 3.12, per the existing `.venv`).
- That `PORT` is actually set by Replit's runtime before relying on it.
- SQLite persistence (see below) — do not assume it without checking the specific deployment type.

## Database — SQLite persistence is **not verified**

`DATABASE_URL` defaults to a local SQLite file. Whether that file survives a restart/redeploy depends entirely on the specific Replit deployment type (e.g. reserved-VM-style deployments typically keep local disk; autoscale/serverless-style ones may not guarantee it across scale events). **This has not been tested against the real Replit platform from here.** Do not treat demo data in SQLite as durable until that's confirmed; `DATABASE_URL` is already designed to swap to a Postgres DSN with no code change if persistence turns out to matter.

## CORS

`CORS_ORIGINS` must be a comma-separated list of exact origins (scheme + host + port) — not a wildcard. Empirically verified behavior (see `tests/test_cors.py`):
- Allowed origin → response carries `Access-Control-Allow-Origin`; preflight `OPTIONS` → `200`.
- Disallowed origin → response omits the header (request still returns `200` to a non-browser client, but a browser blocks reading it); preflight `OPTIONS` → `400`.
- `CORS_ORIGINS=*` (or `*` among other origins) → rejected at `Settings` construction time with a clear validation error.

Mohammad's production frontend domain is **not known or invented here** — add it to `CORS_ORIGINS` when it exists.

## Health / readiness

`GET /api/v1/health` is the **only** health-related route authorized by the frozen contract (`contracts/openapi.yaml`) — no separate `/ready` endpoint exists, and none was added here; the contract doesn't permit a new public endpoint, and the health route itself was not modified.

**What it actually checks — and what it doesn't.** Its `dependencies` field currently reflects **database connectivity only** (`{"database": "ok" | "unavailable"}`). It does **not** check matching-provider availability. Concretely: a deployment with `ENABLE_FIXTURES=false` and no real provider implemented — which makes every matching-dependent route (`careers/match`, `scenarios/simulate`, `roadmaps/generate`, `projects/recommend`, `projects/simulate`) return `503 PROVIDER_UNAVAILABLE` — will still report `GET /api/v1/health` → `status: "ok"`. A passing health check is evidence the process is up and the database is reachable; **it is not proof the AI-facing application is actually ready to serve its core features.**

Because of that gap, treat a health check as necessary but not sufficient: any real deployment verification should **also** run the synthetic API smoke test (below), which actually exercises a matching-dependent route and will surface a `503`/misconfiguration that `/health` alone cannot see.

## Smoke testing

```
backend\.venv\Scripts\python.exe -m scripts.smoke_test
SMOKE_TEST_BASE_URL=https://your-deployment-url backend\.venv\Scripts\python.exe -m scripts.smoke_test
```
Hits `GET /api/v1/health` and `POST /api/v1/careers/match` with a synthetic inline profile (no `profile_id`, so it never touches the database write path). Reports each check's actual result — `[ok]`, `[warn]` (e.g. a disclosed `503 PROVIDER_UNAVAILABLE` when `ENABLE_FIXTURES=false`), or `[FAIL]`. Exit code distinguishes all three outcomes, never collapsing a warning into a false "clean pass":

| Exit code | Meaning |
|---|---|
| `0` | Every check passed cleanly — no warnings. |
| `1` | At least one check failed (always takes precedence over a warning). |
| `2` | No failures, but at least one warning (e.g. a disclosed `503`) — not a clean pass. |

Never prints "All smoke checks passed" unless the exit code is `0`.
