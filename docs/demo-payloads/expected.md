# Demo payloads and expected results (for Rehan)

Demo student: Python, JavaScript, "Database Querying"; interest "web development"; no projects; Computer Science, undergraduate, semester 5.
Request bodies match the release-candidate schemas (`origin/feature/13b-release-candidate` @ `61eb394`: `backend/app/schemas/{profile,matching,scenarios,projects}.py`).

| File | Endpoint | Body |
|---|---|---|
| `careers-match.json` | `POST /api/v1/careers/match` | `MatchRequest` (`profile`, `limit` 6, no scenario) |
| `scenarios-moderate.json` | `POST /api/v1/scenarios/simulate` | `ScenarioRequest` (`profile`, `scenario_id: moderate`) |
| `scenarios-fast.json` | `POST /api/v1/scenarios/simulate` | `ScenarioRequest` (`scenario_id: fast`) |
| `projects-simulate.json` | `POST /api/v1/projects/simulate` | `ProjectSimulationRequest` (`role_id: software_developer`, `project_id: sd_wdi_web_dashboard`) |

## Send them (no key is needed for the API itself)
Run from `docs/demo-payloads/`. `BASE_URL` is where the backend listens, for example `http://127.0.0.1:8000`.
```
curl -s -X POST "$BASE_URL/api/v1/careers/match"       -H "Content-Type: application/json" -d @careers-match.json
curl -s -X POST "$BASE_URL/api/v1/scenarios/simulate"  -H "Content-Type: application/json" -d @scenarios-moderate.json
curl -s -X POST "$BASE_URL/api/v1/scenarios/simulate"  -H "Content-Type: application/json" -d @scenarios-fast.json
curl -s -X POST "$BASE_URL/api/v1/projects/simulate"   -H "Content-Type: application/json" -d @projects-simulate.json
```
Server settings for these results: `MATCHING_MODE=hussain`, `CATALOG_MODE=cached` (this also turns on Jawad's cached trend signals, which the scenarios need).
For the RunPod results, `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` must be exported in the shell that starts the server; for the "RunPod off" results leave them unset.
The first RunPod request after idle is slow (17 s in my run, cold start); the following ones take about a second.

## Why the free-text skill has a made-up `skill_id`
`SkillRef` requires `skill_id` and `name`. "Database Querying" is not in the catalogue, so the payload sends the slug `database_querying` with the raw name.
The matcher uses a `skill_id` only if it exists in the catalogue; otherwise it resolves **by name**: catalogue name or alias, then a known skill inside the text, then (RunPod) the closest catalogue skill.
So the backend must not reject or rewrite a `skill_id` that is not in the catalogue. `python` and `javascript` are real catalogue ids and resolve directly.

## What was used
- Data: Jawad's `origin/feat/jawad-30-roles` @ **`8cd1166`** (30 roles, 20 skills, 12 `not_equivalent` pairs, 12 cached trend signals). The release candidate's `backend/app/data/cached/{roles,skills,projects,skill_not_equivalent}.json` are byte-identical to it.
- Matcher: `services/matching` on `feature/hussain-matching` (current, including the ambiguity rule and the "Not recognised" caveat). Embeddings: all-MiniLM-L6-v2 on RunPod, threshold 0.60, related/interpreted credit 0.5.
- Two RunPod states: **on** (both env vars set, endpoint reachable) and **off** (env vars unset).
- Cross-check: I also posted the four files to the release-candidate app itself (`61eb394`, in-process test client, `MATCHING_MODE=hussain`, `CATALOG_MODE=cached`), once with RunPod and once without. All four returned 200. See "Differences" below.

## Normalisation (RunPod on or off)
| Typed (`skill_id` / `name`) | Resolved to | How |
|---|---|---|
| `python` / Python | `python` | catalogue id |
| `javascript` / JavaScript | `javascript` | catalogue id |
| `database_querying` / Database Querying | `sql` **only with RunPod** | not in the catalogue; embeddings: SQL **0.71** (next best: Programming 0.30, GIS 0.28), half credit, "please confirm". Live check: cosine 0.7061 |
| (catalogue skills) Python ~ Programming | related credit | similarity 0.62, half credit, shown as `Python counted as related to Programming (similarity 0.62); partial credit only.` (RunPod only) |

Without RunPod "Database Querying" is dropped and listed in a caveat (see below). The student then has two skills, not three.

## 1. `careers-match.json`, RunPod ON
Matched skills for the top role: `python`, `javascript`, `sql`. Missing: `programming`, `critical_thinking`, `systems_analysis`, `complex_problem_solving`, `git`. Evidence: `onet_15_1252_00`. `catalog_coverage`: 30 verified of 30; `methodology_version` v1.

| # | role_id | score | skills | experience | prerequisites | transferable |
|---|---|---|---|---|---|---|
| 1 | software_developer | **23** | 32 | 0 | 0 | 0 |
| 2 | web_developer | **22** | 31 | 0 | 0 | 0 |
| 3 | public_health_analyst | 15 | 21 | 0 | 0 | 0 |
| 4 | data_scientist | 14 | 20 | 0 | 0 | 0 |
| 5 | database_administrator | 12 | 17 | 0 | 0 | 0 |
| 6 | computer_systems_analyst | 10 | 15 | 0 | 0 | 0 |

Top role explanation: `You have 2 of 8 core skills for Software Developer (plus 1 interpreted from your wording, partial credit). Skill coverage 32/100, experience 0/100, prerequisites not assessed. This is an estimated profile alignment, not a hiring prediction.`
Caveats on `software_developer` (and `web_developer`, same three):
1. `Interpreted "Database Querying" as SQL (similarity 0.71), partial credit; please confirm.`
2. `Python counted as related to Programming (similarity 0.62); partial credit only.`
3. `No project mentions a skill this role needs.`

Prerequisites show 0 because the roles list none: the weight is shared out ("prerequisites not assessed").

## 2. `careers-match.json`, RunPod OFF
Matched skills for the top role: `python`, `javascript`. Missing adds `sql`.

| # | role_id | score | skills |
|---|---|---|---|
| 1 | software_developer | **15** | 21 |
| 2 | web_developer | **13** | 18 |
| 3 | public_health_analyst | 10 | 14 |
| 4 | data_scientist | 7 | 10 |
| 5 | data_analyst | 6 | 9 |
| 6 | financial_risk_specialist | 4 | 6 |

(experience, prerequisites, transferable: 0 in every row.) Explanation: `You have 2 of 8 core skills for Software Developer. Skill coverage 21/100, ...`.
Caveats on every match, in my matcher: `No project mentions a skill this role needs.`, `Not recognised and not used: "Database Querying". Try a skill from the list.`, `Semantic matching unavailable; exact skill matching only (degraded)`.

## 3. `scenarios-moderate.json` and `scenarios-fast.json`
The scenario scales the weight of rising or falling skills (moderate 1.10 / 0.90, fast 1.25 / 0.75). For this student the signals touch Git, JavaScript and Python (all rising; developer-activity data, not job demand). Each adjusted match gets
`Scenario adjusted the weight of: Git, JavaScript, Python (based on dated GitHub developer-activity (not job demand) signals; an assumption, not a forecast).` after the caveats above.

| Role | baseline | moderate | fast | | baseline (off) | moderate (off) | fast (off) |
|---|---|---|---|---|---|---|---|
| software_developer | 23 | 24 | **25** | | 15 | 16 | 17 |
| web_developer | 22 | 23 | 23 | | 13 | 13 | 15 |
| public_health_analyst | 15 | 16 | 17 | | 10 | 11 | 12 |
| data_scientist | 14 | 15 | 16 | | 7 | 8 | 8 |
| database_administrator | 12 | 12 | 13 | | not top 6 | not top 6 | not top 6 |
| computer_systems_analyst | 10 | 11 | 11 | | not top 6 | not top 6 | not top 6 |

With RunPod off the top 6 also contains `data_analyst` (6, 7, 7), `financial_risk_specialist` (4, not listed, 5) and, in moderate only, `information_security_analyst` (5). The response `data` also carries `assumptions` (two illustrative sentences) and `uncertainty_note` (not a labour-market forecast), written by the backend.

## 4. `projects-simulate.json`
`software_developer` with `sd_wdi_web_dashboard` (skills: JavaScript, Git, Programming, Complex Problem Solving). The student already has JavaScript, so `assumed_skill_ids` = `git`, `programming`, `complex_problem_solving`.

| | baseline_score | simulated_score |
|---|---|---|
| RunPod ON | **23** | **40** |
| RunPod OFF | 15 | 37 |

**How these numbers were obtained (two independent ways, same result):**
- *Emulated by my matcher* (not `/projects/simulate`): I added the three missing skills to the profile and re-matched `software_developer`: 23 to 40 (on), 15 to 37 (off). This is what the pitch calls "emulated".
- *Release-candidate `/projects/simulate`* (`61eb394`, run in-process on 2026-10-24 with the same data): `baseline_score 23.0`, `simulated_score 40.0` (on); `15.0` and `37.0` (off). The disclaimer text starts "Hypothetical simulation only...". This was a test client against the code, not a deployed server, so re-run the curl above against the real server before recording.

## Differences between my matcher and the release candidate's vendored copy
I compared the RC app's responses with my matcher's, role by role (score, breakdown, matched skills, explanation, caveats), for the three match-type requests, both RunPod states:
- **RunPod on: no difference at all.**
- **RunPod off: scores identical; the only difference is the caveat** `Not recognised and not used: "Database Querying". Try a skill from the list.` My matcher adds it to every match; the RC does not, because `backend/app/services/hussain_matching` is an older copy (it has neither this caveat nor the ambiguity rule, "did you mean X or Y"). To get them, Rehan must re-sync that folder from `services/matching` (`normalizer.py`, `matcher.py`, `embeddings.py`).
- The RC reports `data_mode: "fixture"` on every response, even with cached roles (its own wording in `warnings`). The `warnings` list is long and backend-written; it is not part of the scoring.
