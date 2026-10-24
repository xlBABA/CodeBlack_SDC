# PRD inputs — data (Jawad)

**This is a supporting input document, not the official submitted PRD.** Ready-to-paste text for the data sections of the Mustaqbal AI PRD — the final PRD must use the official competition template; copy from here into it, don't submit this file as-is.

**Where this comes from:** `docs/source-register.md` and the files in `data/` on branch `feat/jawad-30-roles` (stacked on `feat/jawad-data-fixes`, PR #5, which is stacked on PR #2 and PR #1). Those files are not on `main` yet. Dates are when we checked each source; all are in 2026.

**What the data contains** (counted from the files on `feat/jawad-30-roles`):

| Item | Count |
|---|---|
| Career roles | 30 |
| Skills | 20 |
| Learning resources | 16 |
| Portfolio projects | 17 |
| Trend snapshots (cached) | 12 |
| Role-to-SDG links / skill-to-SDG links | 39 / 20 |

**Status of the 30-role dataset: in the deployed app.** The deployed app showed **30 roles** when checked on **2026-10-24 at 19:50 UTC (2026-10-25 03:50 MYT)**: `GET /api/v1/sdgs/{role_id}` returned role SDG mappings (`data_mode: "cached"`) for all 30 role IDs. A few minutes earlier (19:43 UTC), one `POST /api/v1/careers/match` with an invented profile returned `catalog_coverage` 30 of 30 (Jawad's site test report). The data is validated: all 8 of Jawad's test suites pass, and Rehan's cached-data validators accept it. Rehan's cached copy on `feature/13b-release-candidate` @ `5dcde64` equals our files on `feat/jawad-ph-fix` (which adds the Public Health Analyst rebuild and 14 not_equivalent pairs), except for one note sentence in `resources.json`. Which backend commit is deployed is not confirmed: `/api/v1/health` shows no commit. The app lists at most 6 roles per profile.

## What is shown in the deployed app today

Checked against the deployed backend API, https://mustaqbal-ai.replit.app, with **GET requests** on 2026-10-24 between 19:50:54Z and 19:50:58Z (UTC); the trends response's `generated_at` was 2026-10-24T19:50:57Z. The API's OpenAPI document lists 3 GET endpoints: `/api/v1/health`, `/api/v1/trends` and `/api/v1/sdgs/{role_id}`. The POST results below come from one earlier test with invented profiles at about 19:43 UTC the same day (no CV uploaded).

| Feature | Status in the deployed API | Evidence |
|---|---|---|
| SDG mappings for all 30 roles and their skills | **IMPLEMENTED, uses our cached data** | `GET /api/v1/sdgs/{role_id}` returned role mappings with `data_mode: "cached"` for all 30 role IDs. |
| Trend signals | **Our cached data in the app** | `GET /api/v1/trends` returns `data_mode: "cached"`, `source_status: "stale"`, `last_successful_refresh_at` 2026-10-22T12:42:45Z and 12 signals. Their values and retrieval times equal our 12 GitHub snapshots (12 of 12 checked). Observed 2026-10-21 and 2026-10-22; retrieved 2026-10-21T17:38:40Z to 2026-10-22T12:42:45Z. The word "live" does not appear. This is GitHub developer activity, **NOT live and NOT job demand**. 8 of our 20 skills have no trend signal: critical_thinking, mathematics, complex_problem_solving, systems_analysis, attention_to_detail, analytical_scientific_software, programming, science. |
| Career matching, scenarios, roadmap, project recommendations | **In the app; checked once with invented profiles** | POST endpoints (`/careers/match`, `/scenarios/simulate`, `/roadmaps/generate`, `/projects/recommend`). Their responses carry `data_mode: "fixture"`, and the UI shows a "Demo data" badge; this label is being fixed. The real source is our cached catalog (roles, skills, resources, projects), scored by Hussain's formula. Semantic (RunPod) matching was off during this one test: every match was labelled "exact skill matching only (degraded)" — not confirmed as the deployment's permanent state, only this one check. |
| Role list, skill importances | **Not exposed by any GET endpoint** | The frontend has the 20 skills hard-coded, the same as `data/skills.json`. Roles appear only through the match results. |

**Where the numbers come from:**
- **"API" numbers** come from the GET responses above.
- **"Standalone" numbers** come from Jawad's Python services (`services/catalog`, `services/roadmaps`, `services/trends`) run on the `feat/jawad-30-roles` data. They have not been confirmed in the app.

---

## (a) Data sources

"Who checked": "Jawad, manually in browser" wherever `docs/source-register.md` says so. Every other source was checked by an automated fetch run by Claude Code (see `docs/jawad-ai-usage.md`).

**Role and skill requirements (O*NET OnLine, US Department of Labor)**

O*NET licence: each O*NET OnLine page footer says its content "is licensed under a Creative Commons Attribution 4.0 International License" (read on 2026-10-23), so O*NET-derived data must credit O*NET and the U.S. Department of Labor, Employment and Training Administration.

Attribution line (use wherever O*NET-derived data is shown): "Source: O*NET OnLine by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA), licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)."

Jawad checked the titles and codes of the 22 newer O*NET pages in a browser on 2026-10-24 (MYT); all matched. He also spot-checked 3 mathematics scores on their Details pages (Statistician 97, Data Scientist 85, Actuary 85). Their other skill scores and tool lists were fetched automatically by Claude Code and not checked by hand.

| Source | What we use it for | Licence | Source's own update date / when we checked | Who checked |
|---|---|---|---|---|
| O*NET — Business Intelligence Analysts (15-2051.01) | Skills and tools for the Data Analyst role | CC BY 4.0, attribution required (U.S. Department of Labor, Employment and Training Administration) | Updated 2026-10-06 / checked 2026-10-21 | Automated fetch (Claude Code) |
| O*NET — Financial and Investment Analysts (13-2051.00) | Tools and work styles for the Financial Analyst role (O*NET says its other sections are still being collected) | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-21 | Automated fetch (Claude Code) |
| O*NET — Mechanical Engineers (17-2141.00) | Skills and tools for the Mechanical Engineer role; read-only re-checked 2026-10-24 against the 22-newer-roles rule (found missing systems_analysis and science, two team-raised scores, and python's importance below the newer roles' floor) — Rehan decided to leave the record unchanged for release stability; see the known-limitation note below | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-21 (re-checked 2026-10-24) | Automated fetch (Claude Code) |
| O*NET — Epidemiologists (19-1041.00) | Skills and tools for the Public Health Analyst role (closest O*NET match); re-fetched 2026-10-24 for the approved "Option C" rebuild (`origin/feat/jawad-ph-fix` @ `1cf9b74`), which added 3 missing cognitive skills and marked the role limited coverage. Finalized 2026-10-24 (`@ b2c158a`, approved by Rehan): `onet_19_1041_00` added to the `source_ids` of `science`, `analytical_scientific_software` and `gis` in `data/skills.json`, since O*NET lists them for this occupation — no other skill field changed | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-21 (re-fetched 2026-10-24) | Automated fetch (Claude Code) |
| O*NET — Software Developers (15-1252.00) | Skills and tools for the Software Developer role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-22 | Automated fetch (Claude Code) |
| O*NET — Accountants and Auditors (13-2011.00) | Skills, work styles and tools for the Accountant role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-22 | Automated fetch (Claude Code) |
| O*NET — Civil Engineers (17-2051.00) | Skills and tools for the Civil Engineer role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-22 | Automated fetch (Claude Code) |
| O*NET — Environmental Scientists and Specialists, Including Health (19-2041.00) | Skills and tools for the Environmental Scientist role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-22 | Automated fetch (Claude Code) |
| O*NET — Data Scientists (15-2051.00) | Skills and tools for the Data Scientist role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title, code and mathematics score checked by Jawad in a browser, 2026-10-24 |
| O*NET — Statisticians (15-2041.00) | Skills and tools for the Statistician role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title, code and mathematics score checked by Jawad in a browser, 2026-10-24 |
| O*NET — Operations Research Analysts (15-2031.00) | Skills and tools for the Operations Research Analyst role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Web Developers (15-1254.00) | Skills and tools for the Web Developer role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Database Administrators (15-1242.00) | Skills and tools for the Database Administrator role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Information Security Analysts (15-1212.00) | Skills and tools for the Information Security Analyst role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Computer Systems Analysts (15-1211.00) | Skills and tools for the Computer Systems Analyst role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Electrical Engineers (17-2071.00) | Skills and tools for the Electrical Engineer role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Industrial Engineers (17-2112.00) | Skills and tools for the Industrial Engineer role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Chemical Engineers (17-2041.00) | Skills and tools for the Chemical Engineer role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Aerospace Engineers (17-2011.00) | Skills and tools for the Aerospace Engineer role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Surveyors (17-1022.00) | Skills and tools for the Surveyor role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Environmental Engineers (17-2081.00) | Skills and tools for the Environmental Engineer role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Bioengineers and Biomedical Engineers (17-2031.00) | Skills and tools for the Biomedical Engineer role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Urban and Regional Planners (19-3051.00) | Skills and tools for the Urban and Regional Planner role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Hydrologists (19-2043.00) | Skills and tools for the Hydrologist role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Management Analysts (13-1111.00) | Skills and tools for the Management Analyst role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Budget Analysts (13-2031.00) | Skills and tools for the Budget Analyst role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Financial Risk Specialists (13-2054.00) | Skills and tools for the Financial Risk Specialist role (O*NET says its other sections are still being collected) | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Actuaries (15-2011.00) | Skills and tools for the Actuary role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title, code and mathematics score checked by Jawad in a browser, 2026-10-24 |
| O*NET — Market Research Analysts and Marketing Specialists (13-1161.00) | Skills and tools for the Market Research Analyst role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |
| O*NET — Logisticians (13-1081.00) | Skills and tools for the Logistician role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-24 | Automated fetch (Claude Code); title and code checked by Jawad in a browser, 2026-10-24 |

**Trend signal**

| Source | What we use it for | Licence | When the data was retrieved | Who checked |
|---|---|---|---|---|
| GitHub REST API — Search Repositories | Counts new repositories per skill topic (last 30 days vs the previous 30) as a developer-activity signal | Public API; GitHub Terms of Service apply | 12 saved snapshots: 8 skills retrieved 2026-10-21, 4 skills retrieved 2026-10-22. The demo uses only these saved snapshots and makes no live GitHub request. | Automated (our code) |

**Learning resources** (all free to access; checked 2026-10-22)

| Source | What we use it for | Price / licence | Checked | Who checked |
|---|---|---|---|---|
| Microsoft Learn — Query and modify data with Transact-SQL | SQL | Free (no charge observed) | 2026-10-22 | Automated fetch (Claude Code) |
| Microsoft Learn — Get Started with Python Programming: Part 1 | Python | Free (no charge observed) | 2026-10-22 | Automated fetch (Claude Code) |
| Microsoft Learn — Prepare and visualize data with Power BI | Data visualization | Free (no charge observed) | 2026-10-22 | Automated fetch (Claude Code) |
| Microsoft Learn — Getting started with VBA in Office | VBA | Free (no charge observed) | 2026-10-22 | Automated fetch (Claude Code) |
| MathWorks — MATLAB Onramp | MATLAB | Price not stated | 2026-10-22 | Automated fetch (Claude Code) |
| freeCodeCamp.org — Statistics - A Full University Course on Data Science Basics (YouTube, https://youtu.be/xxpc-HPKN28; 8.25 h, video length shown on YouTube; instructor Monika Wahi, confirmed in the YouTube description, checked by Jawad on 2026-10-22) | Mathematics | Free (stated) | 2026-10-22 | Jawad, manually in browser |
| MIT OpenCourseWare — 18.05 Probability and Statistics | Mathematics (backup) | Free (stated) | 2026-10-22 | Automated fetch (Claude Code) |
| SAS — SAS Programming 1: Essentials | Analytical/scientific software | Free (stated) | 2026-10-22 | Automated fetch (Claude Code) |
| freeCodeCamp.org — Microsoft Excel Tutorial for Beginners - Full Course (YouTube, https://youtu.be/Vl0H-qTclOg; 2.44 h, video length shown on YouTube) | Excel | Free (stated) | 2026-10-22 | Jawad, manually in browser |
| Alison — Thinking Critically | Critical thinking | Free (stated) | 2026-10-22 | Jawad, manually in browser |
| Onshape — CAD Basics (Learning Pathway) | CAD software | Free (stated; sign-in needed); Onshape's own terms of use, so we link only | 2026-10-22 | Jawad, manually in browser |
| Microsoft Learn — Introduction to Git | Git | Free (no charge observed) | 2026-10-22 | Jawad, manually in browser |
| MDN Web Docs — Dynamic scripting with JavaScript | JavaScript | Free (no charge observed) | 2026-10-22 | Jawad, manually in browser |
| Harvard — CS50x 2026 | Programming | Free (stated); licence CC BY-NC-SA 4.0, so we link only and never copy or redistribute it; Week 0 to Week 10 = 11 weeks; no hours stated, so 110 h is a team estimate | 2026-10-22 | Jawad, manually in browser |
| GnuCash — Tutorial and Concepts Guide | Accounting software | Free (stated) | 2026-10-22 | Jawad, manually in browser |
| QGIS — Training Manual | GIS | Free (stated); no licence named on the page (footer: "© Copyright 2002-now, QGIS project"), so we link only and do not copy it | 2026-10-22 | Jawad, manually in browser |

**Project datasets and tutorials** (linked, never copied into the app)

| Source | What we use it for | Licence (as stated on its page) | Checked | Who checked |
|---|---|---|---|---|
| UCI — Online Retail II | Data Analyst project | CC BY 4.0 | 2026-10-22 | Automated fetch (Claude Code) |
| UCI — Bank Marketing | Data Analyst project | CC BY 4.0 | 2026-10-22 | Automated fetch (Claude Code) |
| UCI — Default of Credit Card Clients | Financial Analyst project | CC BY 4.0 | 2026-10-22 | Automated fetch (Claude Code) |
| World Bank — World Development Indicators | Financial Analyst and Public Health Analyst projects | Creative Commons Attribution 4.0 | 2026-10-22 | Automated fetch (Claude Code) |
| UCI — AI4I 2020 Predictive Maintenance | Mechanical Engineer project | CC BY 4.0 | 2026-10-22 | Automated fetch (Claude Code) |
| UCI — Combined Cycle Power Plant | Mechanical Engineer project | CC BY 4.0 | 2026-10-22 | Automated fetch (Claude Code) |
| Onshape — CAD Basics (tutorial) | Mechanical Engineer project | Onshape's own terms of use; we link only | 2026-10-22 | Jawad, manually in browser |
| UCI — Diabetes 130-US Hospitals (de-identified) | Public Health Analyst project | CC BY 4.0 | 2026-10-22 | Automated fetch (Claude Code) |
| UCI — Concrete Compressive Strength | Civil Engineer project | CC BY 4.0 | 2026-10-22 | Jawad, manually in browser |
| UCI — Beijing Multi-Site Air Quality | Environmental Scientist project | CC BY 4.0 | 2026-10-22 | Automated fetch (Claude Code) |
| GnuCash Tutorial and Concepts Guide (tutorial) | Accountant project | GNU Free Documentation License (appendix in the guide) | 2026-10-22 | Jawad, manually in browser |
| QGIS Training Manual (tutorial) | Civil Engineer and Environmental Scientist projects | No licence named on the page (footer: "© Copyright 2002-now, QGIS project"); we link only and do not copy it | 2026-10-22 | Jawad, manually in browser |

Checked and **not used**: UCI Air Quality (its page says research use only), Natural Earth, SEC Financial Statement Data Sets, Our World in Data COVID-19 repository and WHO Global Health Observatory (we could not read a licence for these). Every URL is re-checked by `services/catalog/check_links.py`. On 2026-10-23 (UTC), all 85 URLs returned OK (`docs/link-check-report.md` on `feat/jawad-30-roles`).

---

## (b) How the data is produced

**Role catalog** (in our data; the app's SDG endpoint returned all 30 role IDs on 2026-10-24 at 19:50 UTC). We have 30 roles: 9 in Technology & AI, 8 in Business & Finance, 7 in Engineering & Manufacturing and 6 in Healthcare & Sustainability. Each role is linked to one real O*NET occupation, and the skills come from that occupation's O*NET page. We do not invent roles or skills. Every role lists its evidence (`evidence_ids`), so each role can be traced back to its source.

**Skill importance (1 to 5).**
- For thinking skills (like critical thinking or mathematics), O*NET gives a score from 0 to 100. We turn it into 1 to 5: 70 or more = 5, 60s = 4, 50s = 3, 40s = 2, below 40 = 1. In 4 cases (all in the first 8 roles) we raised mathematics or problem solving by one step, and we mark those as team estimates. The 22 newer roles use the rule exactly.
- For tools (like Excel, SQL or GIS), O*NET only says the tool is used, not how important it is. So every tool importance is a team estimate.
- Whether a skill is "required" or "optional" is also our own choice.
- **Team estimates, not source data:** tool importances, required/optional flags, the inclusion rules (which O*NET skills a role gets: thinking skills only with an O*NET score of 50 or more, Attention to Detail only with a Work Style score of 100) and the SDG links and reasons.

**Limited coverage** (fewer of our 20 skills fit these roles): `financial_analyst` and `financial_risk_specialist` (O*NET has not yet published their skills data); `information_security_analyst` and `logistician` (our 20 skills lack their main tools); `public_health_analyst` (added 2026-10-24 with the approved "Option C" rebuild — our 20-skill catalog cannot represent its epidemiology-specific knowledge or software, e.g. Biology, Medicine and Dentistry, CDC Epi Info). The deployed app labels all 5 of these roles with a "Limited skills coverage" caveat (confirmed 2026-10-24).

**Trend signals.**
- **How a signal is made:** for 12 of our 20 skills there is a clear GitHub topic. For each one, we count the new GitHub repositories with that topic in the last 30 days and compare them with the 30 days before. More than 15% up is "rising", more than 15% down is "falling", anything else is "stable". If a request fails, the result is "unknown". Each result is saved as a dated snapshot. This measures developer/tech-ecosystem activity on GitHub only — never describe it as hiring demand or job-market growth.
- **What exists:** 12 saved snapshots (data, standalone service, and the deployed `/api/v1/trends`). In them, 9 skills are rising and 3 are stable. 8 of our 20 skills have no snapshot: critical_thinking, mathematics, complex_problem_solving, systems_analysis, attention_to_detail, analytical_scientific_software, programming, science.
- **What the demo shows:** the app's trend section shows these 12 saved snapshots, labelled `cached` with `source_status: "stale"` (confirmed live 2026-10-24). The standalone `get_trends()` in `services/trends` reads the same snapshots and reports `source_status: "cached"` with the date of the last successful refresh. Neither calls a cached or failed result "live". The demo makes no live GitHub request.
- **Scenarios:** when signals are passed to Hussain's two future scenarios (moderate and fast AI adoption), only rising or falling signals change a skill's weight, a little up or down. In the one app test on 2026-10-24, both scenarios returned their assumptions and an uncertainty note, and changed the scores slightly; semantic (RunPod) matching was off during that test (every match labelled "degraded"), so this does not confirm RunPod's state generally — see "Close-but-different skill pairs" below and `runpod/README.md` for what remains unverified about the live RunPod configuration.

**Close-but-different skill pairs (`data/skill_not_equivalent.json`).** Hussain's matcher gives these pairs a similarity of 0, so one skill never earns semantic credit for the other. 14 pairs total, team judgments, not measured by us: the original 12 plus 2 approved 2026-10-24 — `git`/`gis` (look-alike names; Hussain measured an embedding similarity of 0.74, above his 0.60 threshold) and `financial_analysis_software`/`analytical_scientific_software` (separate O*NET tool categories even within one occupation; Hussain measured 0.67). Side effect of the second pair: `financial_analyst`, `financial_risk_specialist` and `actuary` all require both skills, so in those roles a student with only one of the two gets no partial credit for the other.

**SDG mapping.** Every role and every skill is linked to at least one UN Sustainable Development Goal, with a one-sentence reason. For example, the Civil Engineer role is linked to SDG 9 (infrastructure) and SDG 11 (sustainable cities), and SQL is linked to SDG 8 (decent work, target 8.6). These links are the team's own judgment. In our data that is 39 role links and 20 skill links. **IMPLEMENTED in the app for all 30 roles:** on 2026-10-24 at 19:50 UTC, the deployed `GET /api/v1/sdgs/{role_id}` returned role mappings for all 30 role IDs (`data_mode: "cached"`).

**Learning roadmap** (standalone `get_roadmap()` in `services/roadmaps`. The app's `POST /roadmaps/generate` uses Rehan's own roadmap code with our cached resources; it was checked once with an invented profile, so app hours can differ from the standalone figures below).
- For each missing skill, the roadmap picks one free learning resource we have checked.
- Required skills come first, ordered by importance, then optional skills.
- If a resource assumes another skill (for example, VBA assumes Excel), that skill comes first or a warning is shown.
- Each step has hours, either the provider's own number or a team estimate, and a label saying which.
- If we have no checked resource for a skill, the roadmap says so instead of guessing.

**Portfolio projects.** Each of the first 8 roles has 2 or 3 projects (the 22 newer roles have none yet; `get_projects()` returns an empty list for them) built on a real open dataset or an official tutorial. Each project has 4 to 6 steps and an hours number, which is the sum of our per-step estimates. Datasets are only linked, never copied into the app. (In our data and the standalone `get_projects()`. In the one app test, `POST /projects/recommend` returned 2 projects for Data Analyst and none for Statistician, one of the 22 newer roles — consistent with the backend's own student-facing coverage disclosure, see `backend/app/services/project_service.py`.)

**Status in the backend code** (read-only check of Rehan's branch `feature/13b-release-candidate` @ `5dcde64`, 2026-10-24):
- **Data served:** the backend serves our cached data for roles, skills, SDG mappings, trends, roadmap resources and projects when `CATALOG_MODE=cached`. The deployed SDG and trends endpoints return `cached`, so the deployment uses cached mode. Whether this exact commit is what's deployed is not confirmed.
- **Data version:** the branch's cached copy equals our files on `feat/jawad-ph-fix`, except for one note sentence in `resources.json`.
- **Data label:** the match, scenario, roadmap and project routes always return `data_mode: "fixture"` (Rehan's `catalog_data_mode()`), even with cached data. The UI shows this as "Demo data"; the label is being fixed.
- **Roadmap:** the backend has its own roadmap code. It orders steps by role weight and puts the hours note in the step's reason text, so its output may differ from the standalone `get_roadmap()`.

**Not done yet:**
- Portfolio projects for the 22 newer roles.
- Learning resources for 5 skills: complex_problem_solving, systems_analysis, attention_to_detail, financial_analysis_software, science (the roadmap says so instead of guessing).

---

## (c) Honest limitations

- **GitHub activity is not job demand.** The trend signal counts new GitHub repositories. It does not count job openings, and it is global, not Malaysia-specific.
- **One snapshot is not a trend.** Each skill has one 30-day vs 30-day comparison. GitHub topic tags are voluntary, so activity can be undercounted.
- **Cached, not live.** Our trend data is 12 saved snapshots from 2026-10-21 and 2026-10-22. The app labels them `cached` (`source_status: "stale"`); the standalone `services/trends` labels them "cached" with their dates. Nothing is refreshed live in the demo.
- **Trends cover 12 of 20 skills.** 8 skills have no trend signal: critical_thinking, mathematics, complex_problem_solving, systems_analysis, attention_to_detail, analytical_scientific_software, programming, science.
- **"Demo data" label.** The app's match, scenario, roadmap and project responses carry `data_mode: "fixture"`, and the UI shows a "Demo data" badge, although they use our cached catalog. The label is being fixed. Do not describe this output as fixture or live data.
- **App output checked once.** Matching, roadmap and project outputs come from POST endpoints, which we called once with invented profiles on 2026-10-24. Semantic (RunPod) matching was off during that one test, so exact skill matching was used — this is not confirmed as the deployment's permanent RunPod state, only this one check (see `runpod/README.md`). App roadmap hours can differ from our standalone figures.
- **30 roles in the app.** The deployed app showed 30 roles when checked on 2026-10-24 at 19:50 UTC. The 22 newer roles have no portfolio projects, and 5 skills have no learning resource yet (the roadmap says so).
- **O*NET is US-based.** It describes typical requirements in the US, not the needs of a specific employer or country.
- **Known limitation: `mechanical_engineer`.** Checked read-only against O*NET 17-2141.00 on 2026-10-24 using the 22-newer-roles rule: it is missing `systems_analysis` (O*NET 60) and `science` (O*NET 69); `mathematics` and `complex_problem_solving` are team-raised to 5 where the bucket rule gives 4; `python`'s importance (1) is below the newer roles' floor of 2; and O*NET lists `gis`, `sql`, `vba` and `financial_analysis_software` (cost estimating software) for this occupation, none of which the role includes. The record predates the 22-role rule and was intentionally left unchanged for release stability (Rehan, 2026-10-24) — its importances are not all bucket-derived.
- **14 `not_equivalent` pairs, not 12.** Finalized 2026-10-24: `git`/`gis` and `financial_analysis_software`/`analytical_scientific_software` were added (Hussain measured similarities of 0.74 and 0.67; Rehan approved). See "(b) How the data is produced" above for the full reasoning and the roles affected.
- **Limited coverage** (fewer of our 20 skills fit these roles; labelled live in the app, confirmed 2026-10-24): `financial_analyst` and `financial_risk_specialist` (O*NET has not yet published their skills data); `information_security_analyst` and `logistician` (our 20 skills lack their main tools); `public_health_analyst` (added 2026-10-24 with the approved "Option C" rebuild — our 20-skill catalog cannot represent its epidemiology-specific knowledge or software, e.g. Biology, Medicine and Dentistry, CDC Epi Info).
- **Team estimates.** These are our own choices, not source data: all tool importances, the required/optional split, the rules for which O*NET skills a role includes, 4 raised thinking-skill scores, learning hours where the provider gives none, all project hours, the SDG links and reasons, the 15% trend threshold, and the scenario multipliers (±10% moderate, ±25% fast).
- **Licences we only link to:**
  - CS50x is CC BY-NC-SA 4.0 (non-commercial). Jawad checked its Week 0 to Week 10 (11 weeks) in a browser on 2026-10-22. It states no hours, so its 110 h stays a team estimate.
  - The QGIS Training Manual's page footer names no licence ("© Copyright 2002-now, QGIS project").
  - Onshape's CAD course is under Onshape's own terms of use.
  - For all three, we link only and never copy the material.
- **Not checked by Jawad in a browser:** every source marked "Automated fetch" in the tables above, including the first 8 O*NET pages, the skill scores and tool lists of the 22 newer O*NET pages (only their titles, codes and 3 mathematics scores were checked by Jawad, on 2026-10-24), 7 learning resources and every project dataset except UCI Concrete. These were checked by automated fetches only.
- **No hiring prediction.** Scores are a skill-alignment estimate (`profile_alignment_estimate`), not a chance of getting hired.
