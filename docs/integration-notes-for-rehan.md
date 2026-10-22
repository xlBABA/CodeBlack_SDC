# Integration notes for Rehan: swapping in `services/matching`

From Hussain, 2026-10-23. Based on a read-only trial: `origin/feature/rehan-backend-foundation` @ `a7e3911` checked out in a
separate git worktree, with this repo's `services/` copied in. Nothing was pushed to your branch.

## What I found
Your branch already runs a **vendored, older copy** of my matcher (`backend/app/services/hussain_matching`, taken from my `61373a5`,
plus your 6C-2A/6C-2B fixes in `backend_adapter.py`) behind `MATCHING_MODE=hussain`, with RunPod deliberately switched off
(`similarity=_NO_SIMILARITY`). The trial replaced that copy with the current `services/matching` and turned RunPod back on.
`MATCHING_MODE=fixture` (the default) is unaffected: `FixtureMatchingProvider` and its 50/25/15/10 numbers are untouched.

What changed in my matcher since `61373a5`, all in the new copy:
- skills that are not in the catalogue are interpreted through RunPod embeddings (partial credit, caveat, warning);
- a role with no prerequisites is no longer given 100/100: Q is "not assessed" and its weight is redistributed;
- the scenario caveat names the signal type (GitHub developer activity, not job demand);
- a `not_equivalent` pair with an unknown skill_id is logged instead of silently dropped.

## Recommendation: keep ONE copy of the matcher
Two copies of the same algorithm will drift (they already have: the vendored one is missing the interpretation, prerequisites and warning changes above).
Pick one, your choice:
- **A. Import `services/matching` directly** (what the trial did). One copy, always current. Needs the repo root on `sys.path` (step 1 below), and `services/` must be in the repo you deploy.
- **B. Re-vendor from my latest commit on `feature/hussain-matching`** into `backend/app/services/hussain_matching`, replacing the whole folder (not a partial merge), and change nothing else in the folder.
  Self-contained for deployment, but every later change of mine needs another re-vendor.

Either way, do not hand-edit the matcher on your side. If you need a fix, tell me and I will make it in `services/matching`. The three compatibility fixes you made in 6C-2A/6C-2B are already in my latest commit (next section), so you no longer need to carry them.
The steps below assume option A. For option B, skip step 1 and keep the old import path in step 2.

## Code changes needed on your side (4 small edits)
1. **Make the repo root importable.** `services/` sits next to `backend/`, not inside it. `backend/app/__init__.py` (currently empty):
   ```python
   import sys
   from pathlib import Path

   _REPO_ROOT = str(Path(__file__).resolve().parents[2])   # repo root = parent of backend/
   if _REPO_ROOT not in sys.path:
       sys.path.insert(0, _REPO_ROOT)
   ```
   (Alternatives: `PYTHONPATH=<repo root>` in your run command, or move `services/matching` under `backend/`. The second is the cleaner long-term choice if the Replit run command is `cd backend`.)
2. **`backend/app/api/v1/endpoints/careers.py`: import and construct the real provider.**
   ```python
   - from app.services.hussain_matching.backend_adapter import HussainMatchingProvider
   + from services.matching.backend_adapter import HussainMatchingProvider
   ...
   -        return HussainMatchingProvider(result_model=RoleMatch, similarity=_NO_SIMILARITY)
   +        return HussainMatchingProvider(result_model=RoleMatch)
   ```
   Without `similarity=`, the adapter uses RunPod when `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` are both set, and otherwise
   falls back to exact matching and adds `Semantic matching unavailable; exact skill matching only (degraded)` to every match. It never raises
   because of RunPod. `_NO_SIMILARITY` can then be deleted. The gate `MATCHING_MODE == "hussain"` can stay as it is.
3. **Fix two warning texts in `careers.py` that are now false.** `matching_mode_warning()` and `catalog_provenance_warnings()` say
   "running fully offline (no RunPod contacted)". Suggested wording is in the trial diff: "RunPod embeddings when RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID are set,
   otherwise exact skill matching only".
4. **Option A only: delete `backend/app/services/hussain_matching/`** (and its tests) once the swap works, so there is one copy. Do not delete it
   before step 2 is in, because `tests/test_hussain_matching_adapter.py` and `tests/test_catalog_mode.py` still import it.

## Your three compatibility fixes are now in my code
Your vendored `backend_adapter.py` carried three fixes that `services/matching/backend_adapter.py` lacked. I have ported them, with tests, to `feature/hussain-matching`:
- `role_to_matcher_format` keeps `RoleRequirement.required` (default `True` when the field is absent) instead of forcing `True`.
- `role_to_matcher_format` no longer defaults `data_mode` to `"fixture"` (the key is `None` when the role has none), so "Fixture role for testing" no longer fires for cached roles.
- `match()` removes unmatched optional skills from `missing_skills` (the skills score is unchanged: optional skills still count at half weight).

Take `services/` from the latest commit on `feature/hussain-matching`; do not apply these three by hand.

## Your tests: what to update
Three tests fail and need updating, and one passes but must be rewritten.
Trial result with the swap and the three fixes above (the trial applied them to the copied `services/` before I committed them): baseline before any change **598 passed, 12 skipped**; after the swap **595 passed, 3 failed, 12 skipped**.
No test that asserts the 50/25/15/10 numbers fails, because they test `FixtureMatchingProvider`.

| Test | Result | Why | Change |
|---|---|---|---|
| `test_matching_mode.py::test_get_matching_provider_hussain_mode_uses_explicit_no_similarity` | **fails** | `isinstance` against the vendored class; RunPod is no longer disabled by an explicit no-op similarity | Import `HussainMatchingProvider` from `services.matching.backend_adapter`; assert `provider.similarity is None` (RunPod chosen by env) instead of `similarity("a","b") == 0.0` |
| `test_matching_mode.py::test_min_semester_none_does_not_crash_via_api_in_hussain_mode` | **fails** | Asserts `prerequisites == 100.0` for roles with no prerequisites. That was the bug: free points | Assert `prerequisites == 0.0` (contract needs a number; 0 means "not assessed") and that the explanation contains "prerequisites not assessed" |
| `test_matching_mode.py::test_hussain_mode_warnings_disclose_offline_operation_not_runpod_or_hiring` | **fails** | Requires the word "offline" in the warnings | Update to the new warning wording (RunPod/degraded), keep the "not a validated model" and "not a hiring probability" checks |
| `test_matching_mode.py::test_runpod_is_never_contacted_even_with_credentials_present` | **passes but is now meaningless** | It forbids `urlopen` with fake credentials set. The adapter catches the resulting `AssertionError` and degrades, so the test cannot fail | Rewrite as two tests: with credentials and a fake `opener`/monkeypatched provider, RunPod is used; without credentials, no `urlopen` call and the degraded caveat is present |
| Any test that runs `MATCHING_MODE=hussain` | **environment-dependent** | With real `RUNPOD_*` variables in the shell, they would call the real endpoint (cold start about 20 s, costs money) | Add an autouse fixture to `backend/tests/conftest.py` that does `monkeypatch.delenv("RUNPOD_API_KEY")` and `("RUNPOD_ENDPOINT_ID")`, as `services/matching/tests/conftest.py` does |

Also still referencing the vendored copy (they pass, but delete or repoint them in step 4): `test_hussain_matching_adapter.py`, `test_catalog_mode.py`,
`app/services/hussain_matching/tests/`.

## Live API trial (RunPod on, `MATCHING_MODE=hussain CATALOG_MODE=cached`)
Synthetic student: semester 5, Python, Excel, "Database Querying", "Charts and graphs". All calls returned 200.

| Call | Status | Time | Result |
|---|---|---|---|
| `POST /careers/match` (limit 6) | 200 | 16.7 s (cold start) | public_health_analyst 20, financial_analyst 18, software_developer 16, accountant 13, data_analyst 7. Caveat: `Interpreted "Database Querying" as SQL (similarity 0.71), partial credit; please confirm.` |
| `POST /scenarios/simulate` moderate | 200 | 2.4 s | Same scores as baseline |
| `POST /scenarios/simulate` fast | 200 | 2.3 s | Same scores as baseline |
| `POST /projects/simulate` (data_analyst, da_bank_campaign_analysis) | 200 | 2.4 s | baseline 7.0 to simulated 40.0 |

"Charts and graphs" was **not** interpreted: against Jawad's catalogue it scores 0.60 for Data Visualization, just under the threshold (checked with and without aliases; aliases make no difference).

## Open items that are not part of the swap but you will hit
- **Scenarios do nothing until real signals reach the matcher.** `get_trend_provider()` in `careers.py` returns `NullTrendProvider`, so `MatchingService` passes no signals and
  `moderate`/`fast` give the same scores as the baseline ("No dated trend signals were available..."). Replace it with a provider whose `latest()` returns Jawad's signals:
  the list under `get_trends()["signals"]` from his `services.trends.ingest` (cached snapshot, no `GITHUB_TOKEN` needed). Each signal is a dict with `skill_id`, `direction`
  (`rising`/`falling`/`stable`/`unknown`), `signal_type` (`developer_activity`), `source_id`; the matcher uses only `rising`/`falling`.
  Your `trend_provider_cached.py` only validates raw snapshot files, it does not produce signals. His `get_trends()` has a `base_dir` argument, so it can read your `app/data/cached/trend_snapshots`.
  With his 12 cached signals I checked this against his own data outside your backend (scores move 1 to 2 points; the caveat says "GitHub developer-activity (not job demand)"). I have **not** wired or run it inside your backend.
- **Two warning texts are stale.** `scenario_service.py:97` says scores are identical to the baseline; `project_service.py:154` says "fixture matching logic". Both become wrong once signals and the real matcher are in.
- **Pass the skill catalogue with aliases** if you want alias matching ("Structured Query Language" and similar): `HussainMatchingProvider(result_model=RoleMatch, skills_catalogue=<Jawad's skills.json "skills">)`.
  Without it the adapter builds a name-only catalogue from the roles. I did not test this in the trial.
- **`not_equivalent`:** pass `not_equivalent=[[id, id], ...]` for Jawad's real skill_ids. My fixture's list references skills that do not exist in his catalogue and is logged and ignored.
  I have not yet worked out which of his 20 skills are confusable.
- **Environment.** `RUNPOD_API_KEY` is already a `SecretStr` in your settings, but the adapter reads `os.environ` directly, not your `Settings` object. A key in `backend/.env` only is not seen. Export it or load `.env` into the environment.
- RunPod cold start is about 20 to 25 s; warm calls are about 1 s. The first `/careers/match` after idle is slow. The adapter's own timeout is 60 s per call, with one retry.
