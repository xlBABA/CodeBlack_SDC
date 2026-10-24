# CV extraction timeout diagnosis — 2026-10-24

## Controlled read-timeout mitigation — local implementation only

The subsequently approved experimental setting
`RUNPOD_GLM_READ_TIMEOUT_SECONDS` defaults to **30** when absent and accepts
finite positive numbers **up to 40**. Empty/text/zero/negative/non-finite values
and values above 40 fail configuration validation; they never silently fall back.
The actual API extraction pipeline passes it to an explicit `httpx.Timeout`:
connect=30, read=configured, write=30, pool=30. Request-level timeouts also apply
to injected clients without closing or changing those clients' defaults.
There remains exactly one provider attempt, and owned clients close on success
and failure. Timeout diagnostics name each phase separately, not a total deadline.

Production evidence establishes ReadTimeout near 30 seconds, **not its root
cause**. Queue/cold-start/execution telemetry was inaccessible and the platform
HTTP deadline remains unverified. This is not a proven fix or a hard sub-60-second
deadline. The historical investigation below predates this approved mitigation.

No model, prompt, 12,000-character input bound, 1,200-token output bound, extraction
schema, offline suggestions, confirmation/no-save behavior, manual-review envelope,
or frontend 60-second upload deadline changed. The frontend edit is comment-only.
No environment override was activated outside isolated test processes, no paid
requests were made, and no commit, merge, push, production change or republish
was performed as part of implementation.

### Current validation

From `backend/`, prefix both commands below with:
`env -u RUNPOD_API_KEY -u RUNPOD_ENDPOINT_ID -u RUNPOD_GLM_READ_TIMEOUT_SECONDS DATABASE_URL=sqlite:// CATALOG_MODE=fixture MATCHING_MODE=fixture ENABLE_FIXTURES=true`

```sh
python -m pytest tests/test_config.py tests/test_cv_parse.py tests/test_cv_timeout_diagnostics.py -q
python -m pytest -q
```

- Focused: **79 passed**, 0 failed, 0 skipped, 1 existing deprecation warning.
- Full backend: **840 passed, 13 skipped**, 0 failed, 11 existing deprecation
  warnings (Starlette/httpx and HTTP 422 naming). Existing skips remain disabled.
- From `frontend/`: `npm run build` and `npm run lint` both passed.
- Isolated in-memory databases, stripped provider credentials, mocked provider
  responses and existing outbound HTTP transport guards were used. No inference
  smoke test was run. The development backend workflow was restarted only.
- Synthetic PDF API tests exercise default/40-second read settings, all four
  timeout categories, unchanged payloads, safe logs, owned cleanup, unselected
  offline skills and no profile persistence. Separate tests cover injected-client
  ownership. Existing no-text, malformed-output and frontend deadline assertions
  pass. These do not simulate a real 40-second provider wait or browser interaction.

Exact changed files for this mitigation:
`backend/app/core/config.py`, `backend/app/services/glm_client.py`,
`backend/app/services/cv_extraction_service.py`, `backend/tests/conftest.py`,
`backend/tests/test_config.py`, `backend/tests/test_cv_timeout_diagnostics.py`,
`frontend/src/lib/api.ts` (comment only), `backend/CV_TIMEOUT_DIAGNOSIS.md`,
and `.agents/memory/cv-timeout-evidence.md`.

### Future activation and rollback — separate approval required

Before any separately approved 40-second trial, consider the actual platform
deadline and headroom for upload, PDF extraction, connect/write/pool and response
handling. Read timeout is an inactivity limit, not a cap on total duration;
trickling responses and multiple phases can exceed it. The browser still gives
the entire upload 60 seconds. Do not infer safety from 40 being less than 60.

If manual review persists, a browser/platform timeout occurs, or total duration
reaches **50 seconds**, stop the trial and restore **30** or remove the override
through the approved deployment process. Settings are cached and running processes
must restart (or be republished through that process) to pick up changes.
Neither production activation nor production restart/republish is authorized here.

## Conclusion

The confirmed production failure mechanism is an upstream HTTP client timeout,
followed by the existing safe manual-review response (HTTP 200). The underlying
reason the upstream request exceeded a timeout is **not established**.

The evidence-supported local defect fixed here is synchronous PDF extraction and
HTTP work running on the async request event loop. Both now run in Starlette's
bounded worker pool. This preserves contracts and makes unrelated requests
responsive during one slow extraction; it does **not** prove RunPod will answer
faster or eliminate production timeouts.

No deployment, production setting change, paid probe, or manual Git commit was
performed. No real resumes were used.

## Evidence and confidence

- Read-only deployment metadata reports a public, successful Autoscale deployment.
  `.replit` calls the target `cloudrun`. Those are observations, not proof of a
  particular Cloud Run service's request-timeout setting.
- The production telemetry investigation found four timeout logs on October 24
  (UTC), not just the two in the initial brief:

  | Revision | Timeout timestamps | Following HTTP 200 |
  | --- | --- | --- |
  | `00769ffb-be09-44b4-af90-3b7ad61b417b` | 15:27:56.237, 15:28:39.977 | 15:27:56.239, 15:28:39.978 |
  | `69c89def-b4ad-4df1-b135-001dbb129d98` | 16:41:22.102, 16:47:28.561 | 16:41:22.121, 16:47:28.565 |

  The current-revision log snapshot also explicitly contains
  `CV extraction fell back to manual review` for both of its events. Response
  bodies were not inspected. HTTP 200 alone is not extraction success.
- The investigation reported five parse requests, mean latency **30,625.8 ms**,
  zero HTTP 4xx/5xx, for the queried day. This aggregate cannot assign duration
  to PDF extraction or distinguish HTTP timeout categories.
- A successful intermediate revision (`71fe06cb-5b46-4aa6-bc60-6e0856cb6ee5`)
  had no GLM matches in the query. Absence of logs is not evidence of successful
  parsing, nor a regression boundary.
- The safe environment inventory for development and production reports a RunPod
  key present, with no GLM URL/model overrides returned. The source defaults are
  `https://api.runpod.ai/v2/b1dd8hy2hqo1nb/openai/v1` and `glm-5.3`.
  This inventory does **not** prove the running published revision's effective
  settings, key validity, provider health, or source parity with this checkout.
- Short and 11,000-character successful Shell experiments remain user-reported:
  exact prompts, model options, endpoint, response lengths, timing, and runtime
  parity were unavailable. Character count alone does not make payloads equivalent.
- Replit's official documentation search for Autoscale HTTP duration limits
  returned no documented maximum request duration. Its cited troubleshooting page
  (<https://docs.replit.com/build/troubleshooting>) describes a startup health-check
  limit, which is not an HTTP upload request limit. The actual platform limit
  remains **unverified**; no generic Google Cloud default is assumed.

Cold starts/queueing, networking, model/prompt complexity, credentials/settings
drift and provider generation latency remain hypotheses. No paid comparison was
authorized or needed to establish the local event-loop defect.

## Changes

- `app/api/v1/endpoints/cv.py`: offload PDF parsing and the existing complete
  extraction pipeline with `run_in_threadpool`; close uploads after bounded
  reading (including rejection); monotonic PDF and pipeline timings, status and
  non-content counts. Fallback summary is WARNING so default logging includes
  PDF timing even when INFO messages are suppressed.
- `app/services/glm_client.py`: log actual elapsed milliseconds and timeout class
  (`ConnectTimeout`, `ReadTimeout`, `WriteTimeout`, `PoolTimeout`), safe HTTP
  statuses and bounded input count. Retain single attempt and owned-client cleanup.
- `tests/conftest.py`: deny real httpx transports, clear cached settings before/after
  tests so credentials cached during app import cannot bypass the existing
  environment-stripping fixture.
- `tests/test_cv_timeout_diagnostics.py`: synthetic short/11k/15k PDF inputs through
  actual request construction and mocked HTTP transport; all four timeout classes,
  payload bounds/options, cleanup, safe logs, empty selected skills, no profile
  persistence, and health responsiveness during slow PDF/provider phases.
  Source assertions protect unchanged frontend confirmation gating.
- `../frontend/src/lib/api.ts`: correct a misleading comment only.
- This report, links in `DEPLOYMENT.md`/`CV_UPLOAD_INTEGRATION.md`, and project
  memory describing the conservative timeout decision.

No schema, extraction prompt, seven-field provider output contract, response
envelope, validation status, no-text behavior, mapping, offline suggestion
selection or student confirmation behavior changed. Parsing never saves a profile.

## Timeout semantics and limits

The existing **30 seconds per httpx phase** is unchanged. It is not a 30-second
wall-clock deadline: connection plus reads can take longer; a response trickling
data can repeatedly avoid an inactivity timeout. Frontend upload timeout remains
**60 seconds overall**, without upload retries. No new timeout configuration was
added because platform and workload budgets are not verified.

Tests prove timely fallback for injected upstream failures, not a hard 60-second
backend deadline. Thread offloading does not forcibly cancel work when a browser
disconnects. Many simultaneous slow requests can exhaust the shared worker pool,
and pathological PDF processing is not wall-clock-bounded by this change.
Address those separately if measured traffic warrants it, rather than claiming
this minimal fix is a job queue or a universal deadline solution.

Diagnostics introduced here contain no credentials, URLs, filenames, CV text,
prompts, response bodies, or exception messages. INFO success diagnostics require
application logger INFO level; default WARNING fallback logs contain both PDF
and pipeline durations, with upstream category/duration in the GLM warning.

## Validation

Commands run from `backend/`, with
`DATABASE_URL=sqlite:// CATALOG_MODE=fixture MATCHING_MODE=fixture ENABLE_FIXTURES=true`:

```sh
python -m pytest tests/test_cv_parse.py tests/test_cv_timeout_diagnostics.py tests/test_config.py -q
python -m pytest -q
```

- Focused: **51 passed** in 0.63 s.
- Full backend: **812 passed, 13 skipped** in 7.84 s.
- No remaining test failures. Existing Starlette/httpx and HTTP 422 deprecation
  warnings remain (11 in the full run); skipped tests were not enabled.
- Per-test in-memory databases and a transport guard prevent production data
  access and real httpx provider calls. Mock timeout fallback asserts under 2 s;
  concurrency tests hold a worker until an unrelated health response arrives
  within 0.5 s. Synthetic PDFs are built in memory, not stored.
- `frontend/`: `npm run build` and `npm run lint` both passed.
- Backend workflow restarted cleanly on port 8000. Preview screenshot reached the
  animated landing splash; this is not a browser interaction test of upload/review.
  Confirmation coverage is source-level plus backend draft-safety tests.
- Initial local checks were blocked by missing installed pypdf/multipart packages;
  installing the already-pinned dependencies resolved that setup issue. No
  dependency versions or project configuration changes are part of this patch.

## User-controlled production verification (not performed)

1. Review/merge the patch and approve publishing separately. Record the resulting
   serving revision; do not treat the workspace environment as production evidence.
2. Verify effective non-secret GLM URL/model and key presence for that revision
   without printing credentials. Obtain the platform's actual request deadline
   from authoritative service configuration/support before tuning timeouts.
3. Approve a specific paid budget before any GLM-backed upload. Suggested first
   budget: **one synthetic PDF upload**, no retry. Never use a personal resume.
4. Capture client elapsed time and `data.status` (not just HTTP status), and the
   corresponding PDF/pipeline/GLM timings and timeout category. Check a health
   request remains responsive while the upload runs. Do not log document bodies.
5. If one upload is inconclusive, seek separate approval for at most **two**
   additional calls comparing identical `_build_payload` inputs/options in Shell
   and the application runtime. Use the same synthetic extracted text, model,
   endpoint and output bound; record timing/category only. Stop at the agreed cap.
6. On success, inspect all seven extraction sections and the review screen. On
   failure, verify manual review, unselected offline suggestions and the explicit
   confirmation checkbox; do not confirm/save the synthetic profile.
7. Only then decide whether measured evidence supports a GLM-specific deadline,
   configuration correction, or provider-side investigation. Do not automatically
   raise timeout values or introduce retries.
