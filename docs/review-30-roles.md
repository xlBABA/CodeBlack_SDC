# Review: Jawad's 30-role dataset against the matcher

Date: 2026-10-24. Dataset: `origin/feat/jawad-30-roles` @ `8cd1166` (read-only worktree, nothing changed there).
Matcher: `feature/hussain-matching` @ `08f87ea` plus the uncommitted changes listed under "Fixed on my branch".
Compared with the 8-role data of PR #1 (`origin/feat/jawad-trends-data`).

**Important limit: this review is OFFLINE only.** `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` were not set in this session, so no RunPod/embedding behaviour
was run on the 30-role data (every match carries the "degraded" caveat in the outputs below, as intended). The earlier live RunPod results are in `docs/proof/runpod/live-run.md`.

## Summary
| Area | Result |
|---|---|
| Data integrity | Clean: 30 roles, 20 skills, no duplicate ids, every role skill resolves, importance 1 to 5, all 30 verified, all 12 `not_equivalent` pairs valid (no warning) |
| "Few skills inflate scores" | Not a problem: smallest role weighs 18, largest single skill is 28% of a role, a one-skill student never scores above 17 |
| Ranking plausibility | **3 problems** a judge would notice (below), all caused by the data shape (20 skills for 30 roles), not by arithmetic |
| Limited-coverage roles | 4 flagged in the data (not 3); the matcher did not tell the user. **Fixed** (caveat) |
| Empty / unrelated profile | Lists all 30 roles at 0, `accountant` first. Caveat added; response shape needs a decision by Rehan |
| Explanations and caveats | 300 of 300 consistent (core counts, optional skills, "prerequisites not assessed", no fixture caveat) |
| Scenarios with Jawad's signals | Work and are labelled correctly; effect is at most 3 points and never changes the top role |
| Accounting / "Python (pandas)" rules | Built and tested (below) |

## 1. Data checks (`data/roles.json`, `skills.json`, `skill_not_equivalent.json`)
- Roles 30 (`verified: true` for all), skills 20, `SkillNormalizer` builds (no ambiguous alias), no role lists a skill twice or has no required skill.
- Importance histogram: 1:3, 2:44, 3:73, 4:56, 5:84. Prerequisites and transferable skills are empty in **all 30** roles, so prerequisites are always "not assessed" and the 15% + 15% weights are always redistributed (score = skills 5/7 + experience 2/7).
- `not_equivalent`: 12 pairs, all ids exist, none repeated or self-paired; `HussainMatchingProvider` applied 12 of 12 and logged no warning. I did not check whether 12 is enough (needs RunPod to measure similarity between the 20 skills).
- **Limited coverage:** `skills_coverage: "limited"` is set on **4** roles: `financial_analyst`, `information_security_analyst`, `financial_risk_specialist`, `logistician`.
  `docs/source-register.md` names three of them and calls `financial_analyst` "the same case", so the count in the docs and in the data should be made consistent.

### Do roles with few skills get inflated scores?
No. Role size: 6 to 11 skills, total weight 18.0 (`public_health_analyst`) to 35.0. The biggest single skill is `critical_thinking` in `public_health_analyst` at 28%.
One-skill students (each of the 20 skills alone): best score 17 (`critical_thinking` or `mathematics` alone, both on `public_health_analyst`); 16 of the 20 score 13 or lower.
So "1 matched of 2 = 50%" cannot happen with this data. The inflation that does exist is milder and different (see issue 1).

## 2. Ten synthetic students (offline, no scenario, top 3 of 6 shown)
Profiles (fictional, semester 5, skills typed by name): exact lists in the "Reproduce" block.

| # | Student | Top 3 | Verdict |
|---|---|---|---|
| 1 | CS/data (Python, SQL, Excel, Data Visualization, Mathematics; 1 project) | public_health_analyst 44, data_analyst 36, financial_analyst 29 | **Implausible**: health above data |
| 2 | Software (Python, JavaScript, Git, Programming, SQL) | web_developer 37, software_developer 35, data_scientist 23 | Plausible |
| 3 | Accounting (Excel, Accounting Software, Attention to Detail) | accountant 29, financial_analyst 26, financial_risk_specialist 26 | Plausible |
| 4 | Finance (Excel, Financial Analysis Software, VBA, SQL, Mathematics) | financial_risk_specialist 37, financial_analyst 36, public_health_analyst 32 | **Implausible**: health analyst third |
| 5 | Mechanical/civil (CAD Software, MATLAB, Mathematics, Complex Problem Solving) | mechanical_engineer 44, electrical_engineer 36, aerospace_engineer 32 | Plausible (`civil_engineer` only 6th, 29) |
| 6 | Environmental (GIS, Science, Data Visualization, Python) | hydrologist 19, environmental_scientist 18, data_analyst 16 | Plausible, low scores |
| 7 | Health (Science, Excel, Analytical/Statistical Software, Critical Thinking) | market_research_analyst 35, environmental_scientist 29, logistician 28 | **Implausible**: `public_health_analyst` is 8th (22) |
| 8 | Empty profile | 30 roles, all 0, `accountant` first | **Poor**: arbitrary order |
| 9 | Unrelated (Cooking, Gardening, Painting) | same as 8 | **Poor** |
| 10 | Mixed (Python, Excel, CAD Software, Critical Thinking, Teamwork) | industrial_engineer 32, public_health_analyst 32, mechanical_engineer 29 | Mild: a tie broken alphabetically |

## 3. Reproducible issues
All use: `HussainMatchingProvider(skills_catalogue=skills.json["skills"], not_equivalent=skill_not_equivalent.json["not_equivalent"]).match(profile, roles.json, None, [])`,
profile `{"semester": 5, "interests": [], "projects": [], "skills": [{"name": "<each name below>"}]}`.

**Issue 1: `public_health_analyst` is the default top role for generic skills (Jawad: data; me: none).**
- Skills `Python, SQL, Excel, Data Visualization, Mathematics` (+ project "Sales dashboard exercise", interest "data analytics"): `public_health_analyst` 44 (skills 61), `data_analyst` 36 (skills 50).
- Skills `Critical Thinking` alone: `public_health_analyst` 17. `Mathematics` alone: same, 17. `Python` alone: `public_health_analyst` 10.
- Cause: it has the lowest total weight (18.0) and its heavy skills (critical thinking, mathematics, SQL, Python) are the most common ones. A role that asks for less is easier to "cover" because the score is weighted coverage with no penalty for the domain knowledge the catalogue cannot express. `data_analyst` additionally needs complex problem solving and systems analysis, which this student did not list.
- Fix needed (Jawad): the 20-skill catalogue has no health, statistics or domain skills; add them, and review the weights of `public_health_analyst` (Python is `required: true` there).
  The matcher is doing what the formula says; I do not recommend changing the formula before the catalogue grows.

**Issue 2: a student from the right field does not get their field's role first (Jawad, same cause).**
- Skills `Science, Excel, Analytical/Statistical Software, Critical Thinking`: `market_research_analyst` 35, `environmental_scientist` 29, `logistician` 28; `public_health_analyst` 22 (8th: matched critical thinking, excel; missing mathematics, SQL, Python).
- Skills `Excel, Financial Analysis Software, VBA, SQL, Mathematics`: `financial_risk_specialist` 37 (a limited-coverage role) above `financial_analyst` 36, with `public_health_analyst` 32 third.

**Issue 3: empty or unrelated profile returns 30 zero scores (Rehan decision; I added a caveat).**
- Skills `[]`, or `Cooking, Gardening, Painting`: 30 matches, all `score 0`, ordered by `role_id`, so `accountant` is "#1". Explanation: "You have 0 of 6 core skills for Accountant."
- The matcher's warning "No recognised skills in the profile" is not returned by the adapter, so before this review the user saw nothing explaining the zeros. Each match now carries `No recognised skills in the profile; skill coverage is 0.`
- Still needed (Rehan/UI): show a message and an empty list, or at least do not present a ranked list, when no skill was recognised.

**Issue 4: limited-coverage roles said nothing (fixed).** 40 of 300 matches (4 roles x 10 students) had no hint that the score covers only part of the role. Now: `Limited skills coverage: part of what this role asks for is not in our skill catalogue, so this score reflects only the skills we can assess.` Rehan must carry `skills_coverage` through his `RoleFixture`/cached loader, otherwise the field never reaches the matcher in the app.

## 4. Old 8-role data vs the 30-role data (offline)
Both catalogues have the same 20 skill ids (aliases differ). Of the original 8 roles, only `data_analyst` changed: Jawad made `python` a required skill (its score moved +3 to +5 for the students who have Python and -2 for those who do not, because its total weight rose).
All other changes are new roles entering the top 6:

| Student | Top role, 8 roles | Top role, 30 roles | Why |
|---|---|---|---|
| CS/data | public_health_analyst 44 | public_health_analyst 44 | unchanged; `financial_risk_specialist` 28 and `data_scientist` 25 join the top 6 |
| Software | software_developer 35 | web_developer 37 | `web_developer` has lighter requirements (total weight 24 vs 33) |
| Accounting | accountant 29 | accountant 29 | `financial_risk_specialist`, `budget_analyst`, `actuary` join |
| Finance | financial_analyst 36 | financial_risk_specialist 37 | new limited-coverage role scores higher on the same tools |
| Mech/civil | mechanical_engineer 44 | mechanical_engineer 44 | four engineering roles join; `civil_engineer` drops from 2nd to 6th |
| Environmental | environmental_scientist 18 | hydrologist 19 | new `hydrologist` scores 19 on the same GIS / Science / Python profile |
| Health | environmental_scientist 29 | market_research_analyst 35 | **worse**: a business role overtakes; `public_health_analyst` drops from 2nd to 8th |
| Mixed | public_health_analyst 32 | industrial_engineer 32 | tie, broken alphabetically |

More roles dilute the specific ones; with 20 skills several roles overlap heavily, so the top changes for 5 of 8 students.

## 5. Skill-name rules (built, tested)
Offline results on Jawad's 30-role `skills.json`:

| Typed | Result |
|---|---|
| `Accounting` | Not mapped. Warning: `Skill 'Accounting' is not in the supported catalogue and was not used for matching. Please check the spelling or pick a listed skill. Did you mean Accounting Software?` No credit. (With RunPod it would previously have been auto-mapped at similarity 0.77; the rule now runs before the embedding step.) |
| `Python (pandas)` | Mapped to Python: `Interpreted "Python (pandas)" as Python (it contains "Python"), partial credit; please confirm.` Half credit; caveat only on roles that use Python. |
| `Advanced Excel` | Jawad's `skills.json` already lists it as an alias of Excel, so it maps exactly, no caveat. Without that alias the same rule gives `Interpreted "Advanced Excel" as Excel (it contains "Excel")...`. |
| `Database Querying` | Needs RunPod. Offline: dropped with the usual warning. Last live result: SQL at 0.71, half credit (the demo here used a stand-in returning that value, not a live call). |
| `Cooking`, `Software`, `Python and SQL` | Dropped with the usual warning (`Software` is in 4 skill names, too vague; two skills in one text are not guessed) |

Design choices to confirm: text containing a known skill gets the **same half credit** as an embedding match (it is still an unconfirmed reading); at most 3 "Did you mean" suggestions; whole words only ("Excellence" is not Excel, "JSON" is not JS).
Not done: splitting "Python and SQL" into two skills.

## 6. Explanations and caveats (300 matches: 10 students x 30 roles)
Checked automatically; all passed: "N of M core skills" equals required skills matched / required skills in the role; the role title is right; prerequisites always read "prerequisites not assessed" (never 100/100);
no optional skill appears under `missing_skills`; no "Fixture role for testing" caveat on real roles; no duplicate caveats; every explanation ends with "not a hiring prediction".
Wording notes (not bugs): `matched_skills` includes optional skills but the count says "4 of 7 core skills", so a reader may see 5 matched skills next to "4 of 7"; "No project mentions a skill this role needs." appears on all 300 matches, including students who listed no project at all.

## 7. Scenarios with Jawad's real signals (`get_trends()`, cached, 12 signals)
- All 12 are `signal_type: developer_activity`; 9 rising, 3 stable, none falling. Only 12 of the 20 skills have a signal, and none is a cognitive skill (critical thinking, mathematics and so on), so scenarios mostly favour roles heavy in tools.
- Caveat reads: `Scenario adjusted the weight of: Accounting Software, Excel, VBA (based on dated GitHub developer-activity (not job demand) signals; an assumption, not a forecast).` It names only skills the role requires (checked on 300 matches).
- Effect over the 10 students x 30 roles x 2 scenarios: 199 of 600 scores changed; change of -1 to +3 points, largest +3 (`logistician` for the accounting student, fast); the top-1 role was unchanged in 20 of 20 runs.
- Not shown to the user: the snapshot date (`Cached snapshot retrieved 2026-10-21`). Rehan must pass these signals into matching, otherwise scenarios change nothing.

## 8. Fixed on my branch (uncommitted) vs for others
**Fixed (in `services/matching`, tests: 170 passed, 13 skipped):**
- Normalizer: "part of a longer name" suggestion rule and "contains one known skill" rule (`normalizer.py`, 13 tests in `tests/test_partial_names.py`).
- Matcher/adapter: `Limited skills coverage` caveat and the `skills_coverage` field passed through; `No recognised skills` caveat on every match (3 tests in `tests/test_matcher.py`).
- README section updated.

**Jawad:**
- Add domain skills to the catalogue and review `public_health_analyst` weights (issues 1 and 2); several roles have nothing in the catalogue for their real tools (hence the 4 limited roles).
- Make the number of limited-coverage roles consistent between `source-register.md` (3 named) and the data (4).
- Consider whether `limited` roles should sit in the top ranks (`financial_risk_specialist` above `financial_analyst`).
- Check whether 12 `not_equivalent` pairs are enough for 20 skills.

**Rehan:**
- Carry `skills_coverage` from the cached role data through `RoleFixture` to the matcher.
- Decide what the app shows when no skill was recognised (issue 3).
- Pass Jawad's `get_trends()` signals into matching (see `docs/integration-notes-for-rehan.md`).
- Keep the three compatibility fixes already ported (`required`, `data_mode`, optional skills not in `missing_skills`).

**Me, next, if you want them:** run this review again with RunPod on; split "A and B" skills; show the snapshot date in the scenario caveat; make ties break by something more meaningful than `role_id`.

## Reproduce
Profiles used (all fictional, semester 5): 1 `Python, SQL, Excel, Data Visualization, Mathematics` (project "Sales dashboard exercise", interest "data analytics"); 2 `Python, JavaScript, Git, Programming, SQL`;
3 `Excel, Accounting Software, Attention to Detail`; 4 `Excel, Financial Analysis Software, VBA, SQL, Mathematics`; 5 `CAD Software, MATLAB, Mathematics, Complex Problem Solving`;
6 `GIS, Science, Data Visualization, Python`; 7 `Science, Excel, Analytical/Statistical Software, Critical Thinking`; 8 no skills; 9 `Cooking, Gardening, Painting`; 10 `Python, Excel, CAD Software, Critical Thinking, Teamwork`.
Worktree: `git worktree add --detach <dir> origin/feat/jawad-30-roles`. Tests: `python -m pytest services/matching runpod-worker -q`.
