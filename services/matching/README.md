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
| `fixtures/` | 4 FIXTURE roles and a skills catalogue. Illustrative only, not verified data. Replace with Jawad's `data/roles.json` and `data/skills.json`. |
| `backend_adapter.py` | Plugs this matcher into Rehan's FastAPI backend (see below). |
| `tests/` | 37 pytest tests (1 skips when `backend/` is not in the checkout). |

## Methodology v1
`R = 0.50*S + 0.20*E + 0.15*Q + 0.15*T`, each component 0 to 100.

- **S, skills:** weighted coverage of role skills. Weight = importance (1 to 5), halved for optional skills, times the scenario multiplier. Credit = proficiency factor (beginner 0.60, intermediate 0.85, advanced 1.00, unspecified 0.85). A semantically similar skill (embedding similarity of at least 0.75) gets 0.5 credit and the gap stays listed.
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

## Run tests
```
python -m pytest services/matching -q
```

## Known limitations
- Experience detection is keyword based (catalogue names and aliases only).
- `transferable` is reported as 0 in the breakdown when a role defines no transferable skills.
- The embedding similarity hook (`similarity=fn`) exists but no model is connected yet (next step: RunPod worker).
