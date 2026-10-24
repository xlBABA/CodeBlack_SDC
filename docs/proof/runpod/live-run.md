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
- **Scores were identical live and degraded in steps 1 to 3**, because those profiles used only exact catalogue skills, so semantic matching had nothing to do. Step 4 below adds the interpretation of unknown skills and does change scores.
- The invalid-key test used a placeholder string, not an expired real key; it shows how a 401 is handled, not how the old key failed.
- No screenshots were taken for this run. The console request log for these calls can be screenshotted if the evidence needs to be visual.
- Timings are single samples from one machine.

## Step 4: interpreting skills that are not in the catalogue (live)
Feature: a profile skill that is neither a name nor an alias in the catalogue is embedded through RunPod and mapped to the closest
catalogue skill if the similarity is at least 0.60 and it is not ambiguous because of `not_equivalent`; it then counts as held at half credit
and every match that uses it gets a caveat (see `services/matching/README.md`). Run with the same endpoint, `skills_fixture.json`
(22 skills, 3 `not_equivalent` pairs) and the four fixture roles.

### Phrases (none is a catalogue name or alias; similarity is the max cosine over name and aliases)
| Phrase | Mapped to | Similarity |
|---|---|---|
| Database Querying | SQL | 0.71 |
| Visual data presentation | Data Visualization | 0.78 |
| Analysing statistics | Statistics | 0.82 |
| Working in a team | Teamwork | 0.72 |

They were picked from about 30 candidates tried live. Others scored lower and were not used: "Charts and graphs" 0.61, "Querying databases" 0.61,
"Making charts" 0.60, "Group work" 0.64, "Working well with others" 0.57 (below threshold), "Infographics" 0.55 (below threshold).
"Presenting to clients" mapped to nothing because Customer Service and Customer Research, a `not_equivalent` pair, both passed the threshold.

### Phrases that must not map
| Phrase | Result |
|---|---|
| Cooking | Not mapped (best match was Communication at 0.35). Dropped with the usual "not in the supported catalogue" warning; no caveat, no credit. |
| Java | Not interpreted: "Java" is an exact catalogue name, so it resolves to the Java skill as a confirmed skill before any embedding is used (no caveat, no warning). It was not confused with JavaScript. No fixture role requires Java, so it changes no score. |

### Demo student
Fictional: semester 5, skills `Python` (exact) plus the four phrases above, no projects or interests.

| Role | With RunPod: score (skills) | Without: score (skills) | Difference |
|---|---|---|---|
| data_analyst | **33** (50) | 18 (20) | +15 |
| junior_software_developer | **18** (12) | 10 (5) | +8 |
| business_analyst | **15** (9) | 8 (0) | +7 |
| sustainability_analyst | **15** (7) | 10 (5) | +5 |

- With RunPod, `data_analyst` matches SQL, Python, Data Visualization and Statistics (only Excel is missing); without it only Python is matched.
- Every caveat of the form `Interpreted "<phrase>" as <skill> (similarity 0.xx), partial credit; please confirm.` appears only on roles that use that skill
  (for example "Analysing statistics" appears on `data_analyst` only). "Working in a team" counts through the roles' transferable skills.
- Without RunPod, all four roles carry `Semantic matching unavailable; exact skill matching only (degraded)`.
- If the interpretation call alone fails (catalogue embedded, phrase lookup fails), matching continues with the phrases dropped and the same degraded caveat is added;
  covered by unit tests with mocked failures, not by a live test.

Limits: one run on one machine; the demo phrases were chosen after seeing their scores, so they show that the feature works, not how often free text maps correctly.
