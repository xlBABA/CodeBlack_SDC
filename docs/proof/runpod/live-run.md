# RunPod live run: client, adapter and fallback (after API key update)

Date: 2026-10-23 MYT. Endpoint `f0phohhegtydji` (`CodeBlack_SDC`), the same one described in `README.md` in this folder.
This closes the first two items of that file's "Not covered by this proof". Everything below was run from the repo with
`RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` set in the shell after the key was replaced. No key value was printed, logged or saved;
only response metadata was kept.

## Step 1: raw `/runsync` call (curl)
Input `{"input": {"texts": ["SQL", "Database Querying"]}}`, four calls in a row (calls 1 and 2 only had wall-clock time recorded,
because the first attempt to parse their output failed on a path error; calls 3 and 4 were fully recorded).

| Call | HTTP | Wall-clock | Status | delayTime | executionTime | Worker | Model / dim |
|---|---|---|---|---|---|---|---|
| 1 (cold) | 200 | 19.34 s | not recorded | not recorded | not recorded | not recorded | not recorded |
| 2 (warm) | 200 | 0.88 s | not recorded | not recorded | not recorded | not recorded | not recorded |
| 3 (cold) | 200 | 25.42 s | COMPLETED | 24739 ms | 347 ms | `65xatnz80a1yyd` | `sentence-transformers/all-MiniLM-L6-v2`, 384, 2 vectors |
| 4 (warm) | 200 | 1.04 s | COMPLETED | 492 ms | 199 ms | `65xatnz80a1yyd` | `sentence-transformers/all-MiniLM-L6-v2`, 384, 2 vectors |

Request IDs for calls 3 and 4: `sync-909cc985-62e3-4be5-9a6b-c119cba52465-e2`, `sync-008a876e-6c6b-482c-b361-c85044207a8a-e2`.
Result: the new key is accepted, and the model name and dimension are visible in the response body (the console screenshot
in `README.md` did not show the model name). Cold start is about 20 to 25 s; warm calls take about 1 s wall-clock
(0.5 s queue/network, 0.2 s execution). That fills the "no warm-start timing" gap from `README.md`.

## Step 2: matcher's own client, live
`RunPodEmbeddingProvider.from_skills(<22 skills in services/matching/fixtures/skills_fixture.json>).precompute()` against the live endpoint:
completed without error in 30.3 s (the worker had scaled to zero, so this includes a cold start). This is the first run of
`services/matching/runpod_client.py` against the real endpoint; its response validation (model name, equal-length finite vectors,
dimension) accepted the real response. Spot check of the provider: `similarity("python", "sql")` = 0.30.

Unit tests (all HTTP mocked): `python -m pytest services/matching runpod-worker -q` gives 121 passed, 13 skipped.

## Step 3: backend adapter end to end
`HussainMatchingProvider(skills_catalogue=<fixture skills>).match(profile, <4 fixture roles>, "moderate", [])`:

| Case | Time | Degraded caveat on roles | Scores (top 3) |
|---|---|---|---|
| Live (key and endpoint set) | 2.8 s (warm; the first run took 29.3 s, cold) | 0 of 4 | 18, 15, 8 |
| Invalid key (HTTP 401) | 0.2 s | 4 of 4 | 18, 15, 8 |
| Endpoint variables unset | 0.0 s | 4 of 4 | 18, 15, 8 |

- The live path produced no "Semantic matching unavailable" caveat.
- With a bad key the adapter logged `Semantic matching unavailable (RunPodError): authentication failed (HTTP 401); check RUNPOD_API_KEY`
  (key not included) and every match carried `Semantic matching unavailable; exact skill matching only (degraded)`.
  This is the first test of the fallback against a real failure instead of a mock.
- With the variables unset the same caveat appears immediately with no network call.

## Not shown by this run
- **Scores were identical live and degraded** for both test profiles tried (first profile: 30, 17, 15; second: 18, 15, 8). This run therefore proves
  the live call works and the fallback is signalled, but does **not** show semantic matching changing a ranking. Not investigated: I did not check
  whether those profile skills ever reached the similarity hook or fell below the 0.60 threshold.
- The invalid-key test used a placeholder string, not an expired real key; it shows how a 401 is handled, not how the old key failed.
- No screenshots were taken for this run. The console request log for these calls can be screenshotted if the evidence needs to be visual.
- Timings are single samples from one machine.
