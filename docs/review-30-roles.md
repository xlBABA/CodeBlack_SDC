# Review: Jawad's 30-role dataset against the matcher

Date: 2026-10-24. Dataset: `origin/feat/jawad-30-roles` @ `8cd1166` (read-only worktree, nothing changed there).
Matcher: `feature/hussain-matching` @ `08f87ea` plus the uncommitted changes listed under "Fixed on my branch".
Compared with the 8-role data of PR #1 (`origin/feat/jawad-trends-data`).

**Sections 1 to 8 are OFFLINE** (`RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` were not set when they were written, so every match there would carry the "degraded" caveat).
**Section 9 repeats the run with RunPod live** and corrects the offline picture where it differs. The earlier live results on the 8-role data are in `docs/proof/runpod/live-run.md`.

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

## 9. With RunPod live (2026-10-24, same data `8cd1166`, same 10 students)
**Live check:** embedding "SQL" and "Database Querying" through the endpoint gives cosine **0.7061** (384 dimensions). First call 17.0 s (cold start), second 1.1 s.
Full 10-student run (offline + RunPod, 30 roles each): 46 s. No match carried the "degraded" caveat.

### 9.1 The 10 students, offline vs RunPod
All ten typed exact catalogue names, so **no skill was interpreted** (no "Interpreted ..." caveat anywhere). The differences below come from the other RunPod feature: two *different* catalogue skills
with similarity of at least 0.60 give half credit for each other (`X counted as related to Y`).

| # | Top 3 offline | Top 3 RunPod | Change |
|---|---|---|---|
| 1 cs_data | public_health_analyst 44, data_analyst 36, financial_analyst 29 | public_health_analyst 44, data_analyst 36, **data_scientist 29** | 3rd place changes (better); 7 scores up by 1 to 5 |
| 2 software | web_developer 37, software_developer 35, data_scientist 23 | same | top 3 same; 6 low roles rise (see Git/GIS below) |
| 3 accounting | accountant 29, financial_analyst 26, financial_risk_specialist 26 | same | none |
| 4 finance | financial_risk_specialist 37, financial_analyst 36, public_health_analyst 32 | financial_risk_specialist **39**, financial_analyst **38**, public_health_analyst 32 | same order; 10 scores up |
| 5 mech_civil | mechanical_engineer 44, electrical_engineer 36, aerospace_engineer 32 | same | none |
| 6 environmental | hydrologist 19, environmental_scientist 18, data_analyst 16 | same | top 3 same; `software_developer` 7 to 16, `web_developer` 3 to 14, `data_scientist` 10 to 15 |
| 7 health | market_research_analyst 35, environmental_scientist 29, logistician 28 | same | 4 finance roles rise 2 to 8: `financial_analyst` 17 to 25 (rank 19 to 5); `public_health_analyst` falls from 8th to **11th** |
| 8 empty, 9 unrelated | all 0, `accountant` first | same | none |
| 10 mixed | industrial_engineer 32, public_health_analyst 32, mechanical_engineer 29 | same | top 3 same; tech roles rise 1 to 7 |

Top-1 role unchanged for all 10; top 3 changes for 1 of 10; scores change for 7 of 10 (4 unchanged: 3, 5, 8, 9).

**Every "related" credit that occurred (10 students x 30 roles):**
| Pair (similarity) | Matches | Students | Verdict |
|---|---|---|---|
| Python ~ Programming (0.62) | 21 | 1, 6, 10 | Reasonable |
| Financial Analysis Software ~ Analytical/Statistical Software (0.67) | 14 | 4, 7 | **Wrong, not blocked.** Two different tools; student 7 has no financial software and gains 8 points on `financial_analyst`. Makes issue 2 worse |
| Git ~ GIS (0.74) | 12 | 2, 6 | **Wrong, not blocked.** Look-alike names ("Gi*"); a software student gets `urban_regional_planner` 0 to 8, `surveyor` 0 to 5, `civil_engineer` 0 to 3 |

`skill_not_equivalent.json` (12 pairs) is **not enough**: the two wrong pairs above are missing. Of its 12 pairs only two are above the 0.60 threshold and block anything today (Accounting Software ~ Financial Analysis Software 0.72, Excel ~ VBA 0.64); Mathematics ~ Science (0.59) and Excel ~ Accounting Software (0.51) are near it, the other eight are below 0.50.
Proposed additions for Jawad: `["git", "gis"]` and `["financial_analysis_software", "analytical_scientific_software"]`. I did not change his data.

### 9.2 Free-text skills (one skill per profile)
| Typed | Raw top 3 (similarity) | Result | Judgement |
|---|---|---|---|
| Database Querying | SQL 0.71, Programming 0.30, GIS 0.28 | SQL 0.71, half credit, "please confirm" | Correct |
| Visual data presentation | Data Visualization 0.78, VBA 0.54, Excel 0.40 | Data Visualization 0.78 | Correct |
| Analysing statistics | Analytical/Statistical Software 0.59, Data Visualization 0.46 | **Not mapped** (0.59 is below 0.60) | Reasonable miss; "Analytical/Statistical Software" is a tool, "statistics" is a topic |
| Working in a team | Programming 0.33, Complex Problem Solving 0.32 | Not mapped | Correct (no teamwork skill in the catalogue) |
| Accounting | Accounting Software 0.77 | Not mapped by the name rule; "Did you mean Accounting Software?" | Correct to block (the rule runs before RunPod) |
| Cooking | Science 0.38 | Not mapped | Correct |
| Java | Programming 0.61, GIS 0.46, Python 0.45 | Programming 0.61, half credit, "please confirm" | Acceptable (Java is programming; it did not map to JavaScript); only 0.01 above the threshold |
| Bookkeeping | Accounting Software 0.44 | Not mapped | Correct (a miss a human would want, but 0.44 is far below) |
| Data analysis | Data Visualization 0.62, Systems Analysis 0.61, Analytical/Statistical Software 0.49 | **Data Visualization 0.62**, half credit | **Questionable and not blocked.** Analysis is not visualization, and Systems Analysis is 0.01 behind. `not_equivalent` cannot help: it only rejects a text when its two best candidates are a *listed pair*, and `data_visualization ~ systems_analysis` is not listed |

Also checked: "Charts and graphs" scores 0.597 for Data Visualization, just **below** the threshold, so it is not mapped (the pitch doc says 0.60; it is a miss either way). "Version control" is an exact alias of Git (1.0).
So the only mapping I would call wrong and that nothing blocks is **"Data analysis" to Data Visualization**, plus the two catalogue pairs in 9.1.

**New gap found (not fixed): dropped skills are silent.** "Skill 'Analysing statistics' is not in the supported catalogue ... Did you mean ..." is in the matcher's `warnings`, but `HussainMatchingProvider` returns only the matches.
A student with `Python` and `Analysing statistics` sees no caveat about the dropped skill (checked). Only a profile with no recognised skill at all gets the "No recognised skills" caveat. Needs either a per-match caveat from the adapter or Rehan returning `warnings` to the UI.

### 9.3 The pitch demo student on the 30 roles
Profile from `docs/pitch-hussain.md`: Python, Excel, "Database Querying", "Charts and graphs"; project "Synthetic sales dashboard exercise"; interest "data analytics".
- **The numbers in the pitch are for the 8-role data and are now wrong.** With RunPod on 30 roles: `financial_risk_specialist` 21, `public_health_analyst` 20, `financial_analyst` 17, `software_developer` 16, `computer_systems_analyst` 15, `data_scientist` 14; `data_analyst` is **9th at 12** (offline: 10th at 9).
- The top role is a limited-coverage finance role for a CS/data student: not a sensible demo result. Interpretation is visible (SQL 0.71) but "Charts and graphs" is not interpreted (0.597).
- Fast scenario: 21 to 23 on the top role, `public_health_analyst` 20 to 23 (tie), so it is visible, but the story is poor.
- Project step: adding `da_bank_campaign_analysis` skills to this student takes `data_analyst` from 12 to 42 (my emulation by adding the project's four skills as exact skills; the backend's own simulation may differ by a point or two). The "seven to forty" in the script must change.

### 9.4 Suggested demo student (replaces the one in the pitch)
**Software student: Python, JavaScript, "Database Querying", "Java"**; semester 5, Computer Science; interest "web development"; project "Course project web app".
| What the video shows | Result |
|---|---|
| Ranking (RunPod, no scenario) | `software_developer` 22, `web_developer` 21, `public_health_analyst` 15, `data_scientist` 14 (offline: 15, 13, 10, 7). Top two are sensible; no tie, no Git/GIS credit |
| RunPod interpretation (caveats) | `Interpreted "Database Querying" as SQL (similarity 0.71)` and `Interpreted "Java" as Programming (similarity 0.61)`, both "partial credit; please confirm" |
| Fast scenario (Jawad's cached signals) | `software_developer` 22 to **24**, `web_developer` 21 to 22, `public_health_analyst` 15 to 17; moderate gives 23. Caveat: `Scenario adjusted the weight of: Git, JavaScript, Python (based on dated GitHub developer-activity (not job demand) signals; ...)` |
| Project simulation | `software_developer` with `sd_wdi_web_dashboard`: **22 to 40** (`sd_python_sales_report_cli`: 22 to 35) |
| Fallback (no RunPod) | 15, 13, both interpretation caveats gone, degraded caveat on every match |

Caveats about this choice: "Java" sits at 0.61, one hundredth above the threshold, so it is the fragile line (if the video must not risk it, drop Java and keep "Database Querying", whose 0.71 is steady; the ranking then shifts a little, so rerun the numbers).
Alternative with a more dramatic scenario step: add Git (`JavaScript, Git, "Database Querying", "Java", Python`). Baseline is a 28/28 tie between `software_developer` and `web_developer` (alphabetical), and fast makes `web_developer` 31 pass `software_developer` 30. It shows the scenario changing the order, but that rests on a tie, so I do not recommend it; Git also brings the Git ~ GIS credit onto lower roles.
Not run: the project simulation through Rehan's backend, only my emulation. Re-check the numbers on the real app before recording, and update the numbers in `docs/pitch-hussain.md` (not edited here).

### 9.5 Fixed after this run (uncommitted)
- **Ambiguity rule:** if the two best candidates that pass 0.60 are within 0.03, the text is not mapped and the warning gets `Ambiguous: did you mean X or Y?`. "Data analysis" (Data Visualization 0.62, Systems Analysis 0.61) is now not mapped: `... Ambiguous: did you mean Data Visualization or Systems Analysis?`. "Database Querying", "Visual data presentation" and "Java" still map.
- **Dropped skills are visible:** every match carries `Not recognised and not used: "Analysing statistics". Try a skill from the list.` (all dropped names in one caveat). The hints are inside that caveat, so they reach the app through the adapter: `Not recognised and not used: "Accounting" (did you mean Accounting Software?), "Data analysis" (ambiguous: Data Visualization or Systems Analysis?). Try a skill from the list.`
- Tests: 178 passed, 13 skipped (8 new, in `tests/test_interpretation.py`).

## Reproduce
Profiles used (all fictional, semester 5): 1 `Python, SQL, Excel, Data Visualization, Mathematics` (project "Sales dashboard exercise", interest "data analytics"); 2 `Python, JavaScript, Git, Programming, SQL`;
3 `Excel, Accounting Software, Attention to Detail`; 4 `Excel, Financial Analysis Software, VBA, SQL, Mathematics`; 5 `CAD Software, MATLAB, Mathematics, Complex Problem Solving`;
6 `GIS, Science, Data Visualization, Python`; 7 `Science, Excel, Analytical/Statistical Software, Critical Thinking`; 8 no skills; 9 `Cooking, Gardening, Painting`; 10 `Python, Excel, CAD Software, Critical Thinking, Teamwork`.
Worktree: `git worktree add --detach <dir> origin/feat/jawad-30-roles`. Tests: `python -m pytest services/matching runpod-worker -q`.
