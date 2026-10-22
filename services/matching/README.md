# services/matching (owner: Hussain)

Deterministic career matching for FuturePath AI. Pure Python 3.11+, no external
dependencies (pytest for tests). Output follows `contracts/API_CONTRACT.md`.

## Files
| File | Purpose |
|---|---|
| `normalizer.py` | Maps raw skill text to canonical `skill_id` via catalogue names and aliases. Reports unknown skills instead of guessing. |
| `scoring.py` | The four score components and all weights (one place to review and tune). |
| `scenarios.py` | Moderate and fast AI adoption scenarios; turns dated trend signals into bounded skill weight changes. |
| `matcher.py` | `Matcher.match_roles(...)` returns the `/careers/match` response data. `match(...)` is the `MatchingProvider` adapter. |
| `embeddings.py` | `EmbeddingProvider`: skill name and alias embeddings (all-MiniLM-L6-v2) for the `similarity` hook. Optional; needs `sentence-transformers`. |
| `runpod_client.py` | `RunPodEmbeddingProvider`: the same provider, with embeddings computed by the RunPod endpoint in `runpod-worker/`. |
| `calibration_pairs.json`, `calibrate_threshold.py` | 52 labelled skill-name pairs (20 synonyms, 20 unrelated, 12 hard negatives) and a script that scores them with the real model and reports how candidate thresholds perform. |
| `fixtures/` | 4 FIXTURE roles and a skills catalogue. Illustrative only, not verified data. Replace with Jawad's `data/roles.json` and `data/skills.json`. |
| `backend_adapter.py` | Plugs this matcher into Rehan's FastAPI backend (see below). |
| `tests/` | pytest tests (1 skips when `backend/` is not in the checkout; the real-model embedding tests skip without `sentence-transformers`). |

## Methodology v1
`R = 0.50*S + 0.20*E + 0.15*Q + 0.15*T`, each component 0 to 100.

- **S, skills:** weighted coverage of role skills. Weight = importance (1 to 5), halved for optional skills, times the scenario multiplier. Credit = proficiency factor (beginner 0.60, intermediate 0.85, advanced 1.00, unspecified 0.85). A semantically similar skill (embedding similarity of at least 0.60, see Embedding similarity below) gets 0.5 credit and the gap stays listed.
- **E, experience:** 35 points per project that mentions a role skill (maximum 70), plus 30 if the experience summary mentions one.
- **Q, prerequisites:** share of prerequisites met. Missing information counts half and is shown as a caveat. An unmet hard prerequisite is shown as an explicit warning.
- **T, transferable:** share of the role's transferable skills the student has. If a role has none, the weight is redistributed.

All weights are initial team choices, not research results. The score is an
estimated profile alignment (`score_type: profile_alignment_estimate`), never a
hiring probability. No personal attributes (age, gender, nationality) are used.

## Scenarios and trend signals
With `scenario_id` set, each `TrendSignal` with direction `rising` or `falling`
scales that skill's weight: moderate 1.10 / 0.90, fast 1.25 / 0.75.
Stable or unknown signals are ignored; conflicting signals for one skill are ignored and noted.
No signals means no change, plus a caveat. Signal `source_id`s are added to `evidence_ids`.

## Data expected from Jawad
Skill: `{skill_id, name, aliases[]}`.
Role: `{role_id, role_title, verified, required_skills:[{skill_id, importance, required}], transferable_skills:[skill_id], transferable_interests:[keyword], prerequisites:[{prereq_id, type: education_level|degree_field|min_semester, allowed[] or value, hard, description}], evidence_ids[]}`. Rehan's `RoleFixture` shape is also accepted and converted.
Only `verified: true` roles are ranked.

## For Rehan (backend)
`backend_adapter.HussainMatchingProvider` satisfies `app.services.interfaces.MatchingProvider`.
It accepts your Pydantic `StudentProfile`, `RoleFixture` dataclasses and `TrendSignal`
models, and returns your `RoleMatch` models. It returns every role (your
`MatchingService` does the top-6 cut, and `match_role()` needs single roles).

In `backend/app/api/v1/endpoints/careers.py` (the repo root must be on `sys.path`,
for example run uvicorn from the root with `--app-dir backend`, or add it in `main.py`):
```python
from services.matching.backend_adapter import HussainMatchingProvider
from app.schemas.matching import RoleMatch

def get_matching_provider() -> MatchingProvider:
    return HussainMatchingProvider(result_model=RoleMatch)
```
Tested against `feature/rehan-backend-foundation`: `/careers/match`, `/scenarios/simulate`,
`/roadmaps/generate` and `/projects/recommend` all return 200, and the backend's own 115 tests
still pass (they test the fixture provider, which is untouched).

To make scenarios actually change scores, `MatchingService` must receive real signals:
`get_trend_provider()` currently returns `NullTrendProvider` (always empty). Passing
`FixtureTrendProvider().latest().signals` (later Jawad's real provider) turns it on. The
warning text in `scenario_service.py` ("scores are identical to the baseline") must then be updated.

Weights note: the fixture provider uses 50/25/15/10; this matcher uses 50/20/15/15 from `CLAUDE.md`.

Direct use without the backend:
```python
from services.matching import Matcher, SkillNormalizer
data = Matcher(SkillNormalizer(skills)).match_roles(profile, roles, scenario_id, signals, limit=6)
# {matches, catalog_coverage, methodology_version, warnings}
```
Raises `ValueError` for an unknown scenario or duplicate role IDs (map to a 400 error).

## Embedding similarity (optional)
```python
import json
from services.matching.embeddings import EmbeddingProvider
catalogue = json.load(open("skills.json"))   # {"skills": [...], "not_equivalent": [[id, id], ...]}
provider = EmbeddingProvider.from_catalogue(catalogue, cache_path=".cache/skill_emb.json")
Matcher(normalizer, similarity=provider)
```
Needs `pip install sentence-transformers` (model `all-MiniLM-L6-v2`). Without it the matcher works as before.

**How similarity is computed.** The name and each alias of a skill are embedded separately (one batch on first use, cached in memory and in the JSON file; a skill is re-embedded only when its model, name or aliases change). The similarity of two skills is the highest cosine over all their text pairs. Two skills that share an identical alias would score 1.0; the normalizer already rejects that in a catalogue.

**`not_equivalent` (optional catalogue key).** A list of `[skill_id, skill_id]` pairs that are close but different (the fixture has Customer Service/Customer Research, Sales/Marketing, Java/JavaScript). The provider returns 0 for them in both orders. Unknown ids or malformed entries raise `ValueError`.

### RunPod (hosted embeddings)
Deploy `runpod-worker/` (see its README), then set `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` (names in `.env.example`; never commit values).
`RunPodEmbeddingProvider` is an `EmbeddingProvider` whose model calls `POST https://api.runpod.ai/v2/<endpoint>/runsync`
(timeout 60 s, one retry on timeout, network error, HTTP 429/5xx or job still queued; no retry on bad responses or auth errors).
The key is only sent in the `Authorization` header and is never logged.

`HussainMatchingProvider` (backend adapter) uses it automatically when both variables are set. If they are missing, or the call
fails, matching continues with exact skills only and every match gets the caveat
`Semantic matching unavailable; exact skill matching only (degraded)`. After a failure it does not try RunPod again for 60 s
(`retry_after_seconds`), so a down endpoint does not slow every request. An explicit `similarity=` argument overrides all of this.
Pass `not_equivalent=[[id, id], ...]` to the adapter to apply the exclusion list.

### Interpreting unknown skills
A profile skill that is not in the catalogue (e.g. "Charts and graphs") is no longer simply dropped when the similarity provider can embed free text
(`EmbeddingProvider.interpret()`, inherited by `RunPodEmbeddingProvider`). Its text is embedded once per request (one batch, cached in memory) and compared with every
catalogue skill (max cosine over name and aliases). If the best score is >= `SIMILARITY_THRESHOLD` (0.60) the skill is treated as held, but at `RELATED_CREDIT` (0.5) of normal credit,
in both the skills and transferable components, because it is an interpretation and not a confirmed skill. Exact catalogue matches always win.

- Every match whose role uses the skill gets the caveat `Interpreted "Charts and graphs" as Data Visualization (similarity 0.61), partial credit; please confirm.`, and the same text is returned in `warnings`.
- `not_equivalent`: free text has no skill_id, so the list is applied to the candidates. If the best skill and another skill above the threshold are a `not_equivalent` pair, the text is ambiguous and is not mapped.
- Without a provider, with a plain similarity function, or if the embedding call fails, behaviour is unchanged: the skill is dropped with the usual "not in the supported catalogue" warning.
- The explanation counts only confirmed skills ("2 of 4 core skills (plus 1 interpreted ...)").

### Threshold calibration
Method: `python -m services.matching.calibrate_threshold` scores every pair in `calibration_pairs.json` (fictional, skill names only) with the real model. Pairs are labelled `synonyms` (should match), `unrelated` (clearly different) or `hard_negatives` (close but different skills that must not match). It prints each score and how candidate thresholds perform. It only reports; it never edits `scoring.py`. It scores raw similarity, before `not_equivalent` is applied.

Score ranges (min / median / max): synonyms 0.32 / 0.67 / 0.99, unrelated -0.07 / 0.16 / 0.31, hard negatives 0.35 / 0.57 / 0.65.

| Threshold | Synonyms kept | Unrelated rejected | Hard negatives rejected |
|---|---|---|---|
| 0.75 (old) | 6/20 | 20/20 | 12/12 |
| 0.45 | 18/20 | 20/20 | 5/12 |
| 0.50 | 15/20 | 20/20 | 6/12 |
| 0.55 | 14/20 | 20/20 | 6/12 |
| **0.60 (chosen)** | 12/20 | 20/20 | 10/12 |

**Why 0.60.** At 0.75 only 6 of 20 true synonyms earn credit, so the hook rarely helps. Below 0.60 the hard negatives start passing (only 5 to 6 of 12 rejected). 0.60 is the lowest tested value that keeps 12 of 20 synonyms and rejects 10 of 12 hard negatives. No threshold on names alone rejects every hard negative and keeps 12 synonyms (the worst hard negative scores 0.652, only 11 synonyms score above it). A false match is limited to half credit (0.5) and the skill stays listed as missing, so a wrong match costs less than a missed one. The two hard negatives that still pass at 0.60 (Customer Service/Customer Research 0.65, Sales/Marketing 0.65) are blocked with `not_equivalent`.

## Run tests
```
python -m pytest services/matching -q
```

## Known limitations
- Experience detection is keyword based (catalogue names and aliases only).
- `transferable` is reported as 0 in the breakdown when a role defines no transferable skills.
- Embedding similarity compares skill names and aliases only, and names alone cannot reliably separate close skills (hard negatives score 0.35 to 0.65, overlapping many true synonyms). The `not_equivalent` list only covers pairs someone has already listed; unlisted close pairs can still get half credit at 0.60. Review it whenever the catalogue grows.
- The threshold is calibrated on 52 fictional pairs and is a team choice, not a validated value. Re-run the calibration script (and add hard negatives) when the catalogue or model changes.
