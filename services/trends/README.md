# services/trends (owner: Jawad)

Dated, updatable skill signals from the GitHub Search API. Pure Python 3.11+,
standard library only. Output matches `contracts/API_CONTRACT.md`'s
`TrendSignal` and the `/trends` response shape.

## Method
Metric: **number of repositories CREATED in the last 30 days, tagged with a
skill's GitHub topic** (`topic:<x> created:<start>..<end>`), compared to the
*previous* 30-day window - never an all-time total, which only ever goes up.

- `direction = "rising"` if the change is **more than +15%**, `"falling"` if
  **more than -15%**, else `"stable"`.
- `direction = "unknown"` if either window's fetch failed, or GitHub itself
  flagged the search `incomplete_results: true` (its search timed out before
  finishing - the count can't be trusted).
- One `TrendSignal` per skill per refresh.

## Skill coverage

Every topic below was checked live against the real GitHub Search API on
2026-10-21 (30-day window 2026-09-21..2026-10-21) before being added - no
topic here is guessed.

| skill_id | GitHub query | verified 30-day count (2026-10-21) |
|---|---|---|
| `sql` | `topic:sql` | 3,639 |
| `python` | `topic:python` | 53,660 |
| `matlab` | `topic:matlab` | 471 |
| `data_visualization` | `topic:data-visualization` | 3,225 |
| `excel` | `topic:excel` | 1,533 |
| `vba` | `topic:vba` | 102 |
| `cad_software` | `topic:cad` | 609 |
| `financial_analysis_software` | `topic:financial-analysis` | 321 |

**Not covered (no signal is emitted for these - never guessed):**

| skill_id | why |
|---|---|
| `critical_thinking` | Cognitive/soft skill; no GitHub topic represents "use of critical thinking" the way a topic can represent tool adoption. |
| `mathematics` | A `mathematics` topic exists (~613 new repos/30d) but tags repos about math content/algorithms, not use of mathematics as a workplace skill - too indirect, so left unscored. |
| `complex_problem_solving` | Cognitive/soft skill; no topic correlate. |
| `systems_analysis` | Cognitive/soft skill; no topic correlate. |
| `attention_to_detail` | An O*NET Work Style, not a tool; no topic correlate. |
| `analytical_scientific_software` | Covers SPSS/SAS/Stata collectively; each has its own topic but very low volume (spss 24, stata 30, sas 33 new repos/30d) and no single topic represents all three without arbitrarily picking one. |

`services/trends/queries.py` is the source of truth for this table
(`COVERED_SKILLS`, `NOT_COVERED_SKILLS`); `tests/test_queries.py` checks every
skill_id in `data/skills.json` appears in exactly one of the two.

## Files
| File | Purpose |
|---|---|
| `queries.py` | The skill -> GitHub topic map, and the documented non-coverage list. |
| `github_client.py` | `GitHubTrendClient.fetch_window_count(topic, start, end)` - one HTTP call, real transport is injectable (`transport=`) so tests run offline. Throttles to stay under the Search API's rate limit (~10/min unauthenticated, ~30/min with `GITHUB_TOKEN`). |
| `aggregate.py` | `compute_direction(prev, cur)` (the >15% rule) and `build_trend_signal(...)` (the contract-shaped dict, with an honest `confidence_note`). |
| `snapshot.py` | Save/load one JSON snapshot per skill under `data/trend_snapshots/<skill_id>.json` (current + previous window + their own `retrieved_at`). |
| `ingest.py` | `refresh_all()` - the orchestrator. Per skill: reuse a same-day cached "previous" window to save a call, fetch "current", save a new snapshot. On failure, fall back to the last saved snapshot (`source_status: "cached"`), or `"unavailable"` if none exists yet. **Never returns "live" on a failed fetch.** |
| `tests/` | Offline only - a fake `transport`/`sleep_fn`/`clock` is injected, no network, no real delays. |

## Rate limiting and secrets
`GITHUB_TOKEN` (optional) goes in a root `.env` (see `.env.example` here for
the variable name) - never committed, never logged. Without it, calls are
throttled to ~9/min; with it, ~28/min. A full `refresh_all()` normally makes
8 calls (one "current" fetch per covered skill) once a "previous" window is
cached for the day, or 16 calls the first time that day.

## How to show a real refresh in the demo
Click refresh -> `refresh_all()` re-fetches each skill's *current* 30-day
count live, compares it to the cached previous-window count, and returns a
fresh `retrieved_at` and (if the change crossed 15%) a changed `direction`.
If GitHub is unreachable or rate-limited, the UI should show the last saved
snapshot's data with `source_status: "cached"` and its real (older)
`retrieved_at` - never a fabricated "live" result.

## Run tests
```
python -m services.trends.tests  # or: pytest services/trends -q (if pytest is installed)
```
No internet connection or API token required - every test injects a fake
transport.

## Known limitations
- GitHub topic tagging is voluntary; true activity for a technology can be
  undercounted if maintainers don't tag their repo with that topic.
- This is a **developer/tech-ecosystem activity signal**, not hiring demand
  (`CLAUDE.md`: "Research/GitHub activity != verified hiring demand"). Every
  `TrendSignal.confidence_note` says so explicitly.
- The "previous window" cache is keyed to the calendar day; it is refetched
  (one extra call per skill) the first time `refresh_all()` runs on a new day.
