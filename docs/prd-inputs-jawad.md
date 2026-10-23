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

**Status of the 30-role dataset: PREPARED, not live.** The 30 roles are on branch `feat/jawad-30-roles` (pushed, not merged). They are validated: all 8 of Jawad's test suites pass, and Rehan's cached-data validators accept them (checked read-only on his branches `feature/12b-team-integration` and `feature/13b-release-candidate`). The **deployed app still shows only the first 8 roles** until Rehan's integration testing and a Replit Republish. Do not claim that all 30 roles are live. The 20-skill catalog and the original 8 roles are unchanged.

## What is shown in the deployed app today

Checked against the deployed backend API, https://mustaqbal-ai.replit.app, using **GET requests only**. The responses' `generated_at` was 2026-10-22T18:34Z (UTC). The API's OpenAPI document lists 3 GET endpoints: `/api/v1/health`, `/api/v1/trends` and `/api/v1/sdgs/{role_id}`.

| Feature | Status in the deployed API | Evidence |
|---|---|---|
| SDG mappings for the 8 roles the app had on 2026-10-22, and their 20 skills | **IMPLEMENTED, uses our cached data** | `GET /api/v1/sdgs/{role_id}` returns `data_mode: "cached"` for those 8 roles, and every SDG and reason matched `data/sdg_mappings.json`. The 22 roles added on `feat/jawad-30-roles` are **not in the app yet**, so the app was not checked for them. |
| Trend signals | **NOT our data in the live deployed app.** The deployed app still shows labelled placeholders. | `GET /api/v1/trends` on the deployed app (https://mustaqbal-ai.replit.app) returns `data_mode: "fixture"`, `source_status: "stale"`, 3 synthetic signals (`metric_value: null`) and the warning "No real trend source is connected yet". **This is specifically about the live deployed app, which has not been republished with the 30-role release candidate.** On Rehan's backend release candidate (`feature/13b-release-candidate`), these 12 cached GitHub snapshots ARE wired into `GET /trends` under `CATALOG_MODE=cached` — verified (`data_mode: "cached"`, `source_status: "stale"`, correctly labelled GitHub developer-activity, never hiring demand or job-market growth) but not yet deployed. |
| Career matching, roadmap, project recommendations | **In the API, not checked by us** | These are POST endpoints (`/careers/match`, `/roadmaps/generate`, `/projects/recommend`). We sent no POST request, so their real output (including roadmap hours) is not verified here. |
| Role list, skill importances, learning resources | **Not exposed by any GET endpoint** | They exist in our data files and standalone Python services. Whether the app shows them depends on the POST endpoints and the frontend, which we have not checked. |

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
| O*NET — Mechanical Engineers (17-2141.00) | Skills and tools for the Mechanical Engineer role | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-21 | Automated fetch (Claude Code) |
| O*NET — Epidemiologists (19-1041.00) | Skills and tools for the Public Health Analyst role (closest O*NET match) | CC BY 4.0, attribution required | 2026-10-06 / 2026-10-21 | Automated fetch (Claude Code) |
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

**Role catalog** (in our data; the app's SDG endpoint confirmed the first 8 role IDs on 2026-10-22, before the other 22 were added). We have 30 roles: 9 in Technology & AI, 8 in Business & Finance, 7 in Engineering & Manufacturing and 6 in Healthcare & Sustainability. Each role is linked to one real O*NET occupation, and the skills come from that occupation's O*NET page. We do not invent roles or skills. Every role lists its evidence (`evidence_ids`), so each role can be traced back to its source.

**Skill importance (1 to 5).**
- For thinking skills (like critical thinking or mathematics), O*NET gives a score from 0 to 100. We turn it into 1 to 5: 70 or more = 5, 60s = 4, 50s = 3, 40s = 2, below 40 = 1. In 4 cases (all in the first 8 roles) we raised mathematics or problem solving by one step, and we mark those as team estimates. The 22 newer roles use the rule exactly.
- For tools (like Excel, SQL or GIS), O*NET only says the tool is used, not how important it is. So every tool importance is a team estimate.
- Whether a skill is "required" or "optional" is also our own choice.
- **Team estimates, not source data:** tool importances, required/optional flags, the inclusion rules (which O*NET skills a role gets: thinking skills only with an O*NET score of 50 or more, Attention to Detail only with a Work Style score of 100) and the SDG links and reasons.

**Limited coverage** (fewer of our 20 skills fit these roles): `financial_analyst` and `financial_risk_specialist` (O*NET has not yet published their skills data); `information_security_analyst` and `logistician` (our 20 skills lack their main tools).

**Trend signals.**
- **How a signal is made:** for 12 of our 20 skills there is a clear GitHub topic. For each one, we count the new GitHub repositories with that topic in the last 30 days and compare them with the 30 days before. More than 15% up is "rising", more than 15% down is "falling", anything else is "stable". If a request fails, the result is "unknown". Each result is saved as a dated snapshot. This measures developer/tech-ecosystem activity on GitHub only — never describe it as hiring demand or job-market growth.
- **What exists (data + standalone service):** 12 saved snapshots. In them, 9 skills are rising and 3 are stable.
- **What the demo shows (standalone):** `get_trends()` in `services/trends` reads only these saved snapshots. It reports `source_status: "cached"` with the date of the last successful refresh, and never calls a cached or failed result "live". The demo makes no live GitHub request.
- **Three states, not two — be precise about which one a claim refers to:**
  - *Standalone* (Jawad's own `services/trends`, run in a terminal): reports `source_status: "cached"`, as above.
  - *Backend release candidate* (`feature/13b-release-candidate`): `GET /api/v1/trends` under `CATALOG_MODE=cached` already serves these same 12 real cached snapshots (verified: `data_mode: "cached"`, `source_status: "stale"` — the public contract's name for the same cached-not-live state, with the GitHub-developer-activity-not-hiring-demand disclaimer intact). **Integrated and validated, not yet deployed.**
  - *Live deployed app* (https://mustaqbal-ai.replit.app): still returns fixture placeholders — see the table above. Has **not** been republished with this release candidate; its actual current behavior should not be assumed beyond what was last checked by a GET request.
- **Scenarios (design; not checked in the app):** when signals are passed to Hussain's two future scenarios (moderate and fast AI adoption), only rising or falling signals change a skill's weight, a little up or down. RunPod-assisted semantic matching is available where `RUNPOD_API_KEY`/`RUNPOD_ENDPOINT_ID` are configured and reachable, falling back to exact-skill matching otherwise — this has not been live-tested against the final 30-role release candidate specifically; do not claim it has.

**SDG mapping.** Every role and every skill is linked to at least one UN Sustainable Development Goal, with a one-sentence reason. For example, the Civil Engineer role is linked to SDG 9 (infrastructure) and SDG 11 (sustainable cities), and SQL is linked to SDG 8 (decent work, target 8.6). These links are the team's own judgment. In our data that is 39 role links and 20 skill links. **IMPLEMENTED in the app for the first 8 roles:** on 2026-10-22 the deployed `GET /api/v1/sdgs/{role_id}` returned exactly these mappings for the 8 roles it had (`data_mode: "cached"`). The 28 links for the 22 new roles are not in the app yet.

**Learning roadmap** (standalone `get_roadmap()` in `services/roadmaps`; the app's `POST /roadmaps/generate` uses Rehan's own roadmap code and was not checked).
- For each missing skill, the roadmap picks one free learning resource we have checked.
- Required skills come first, ordered by importance, then optional skills.
- If a resource assumes another skill (for example, VBA assumes Excel), that skill comes first or a warning is shown.
- Each step has hours, either the provider's own number or a team estimate, and a label saying which.
- If we have no checked resource for a skill, the roadmap says so instead of guessing.

**Portfolio projects.** Each of the first 8 roles has 2 or 3 projects (the 22 newer roles have none yet; `get_projects()` returns an empty list for them) built on a real open dataset or an official tutorial. Each project has 4 to 6 steps and an hours number, which is the sum of our per-step estimates. Datasets are only linked, never copied into the app. (In our data and the standalone `get_projects()`. The app's `POST /projects/recommend` was not checked.)

**Status in the backend code — two snapshots in time, do not conflate them:**

*As of `feature/rehan-backend-foundation` at `f0cb9db`, 2026-10-23 (an earlier branch, read-only check):*
- **Data served:** the backend can serve this cached data for roles, skills, SDG mappings, roadmap resources and projects when `CATALOG_MODE=cached`. The default is `fixture`. The deployed SDG endpoint returns `cached`, so the deployment uses cached mode for SDGs. Whether this branch commit is what's deployed is not confirmed.
- **Data version:** that branch's copy of the data matches PR #1, not yet the updated video links in PR #2.
- **Trends:** on that branch, `GET /trends` did not yet use our snapshots.
- **Roadmap:** the backend has its own roadmap code. It orders steps by role weight and puts the hours note in the step's reason text, so its output may differ from the standalone `get_roadmap()`.

*Updated: as of the current release candidate, `feature/13b-release-candidate` (the 30-role integration branch):*
- The 30-role catalog (roles, skills, SDG mappings) is integrated and validated on this branch — see the status line above.
- `GET /trends` now **is** wired to our 12 real cached GitHub snapshots under `CATALOG_MODE=cached` (verified) — this was "planned, not implemented" on the earlier branch above; it is implemented on the release candidate now. **This release candidate has not been deployed/republished**, so the live app (checked above) still shows the older, un-wired behavior.

**Live deployed app today (https://mustaqbal-ai.replit.app):** still the state described in the table at the top of this document — fixture trends, 8 roles only. **Has not been republished with the 30-role release candidate.** Its exact current behavior beyond what was last checked by a GET request is not verified here — avoid asserting anything about the live app beyond those checked endpoints.

**Still planned, not implemented anywhere (release candidate or live):**
- A Replit Republish of this release candidate — until that happens, the 30-role data, the real cached trends, and everything else validated on `feature/13b-release-candidate` remain **prepared, not deployed**.

---

## (c) Honest limitations

- **GitHub activity is not job demand.** The trend signal counts new GitHub repositories. It does not count job openings, and it is global, not Malaysia-specific.
- **One snapshot is not a trend.** Each skill has one 30-day vs 30-day comparison. GitHub topic tags are voluntary, so activity can be undercounted.
- **Cached, not live.** Our trend data is 12 saved snapshots from 2026-10-21 and 2026-10-22. The standalone `services/trends` labels them "cached" with their dates. Nothing is refreshed live in the demo.
- **Trends are not in the live deployed app.** The deployed `/api/v1/trends` (https://mustaqbal-ai.replit.app, not republished with this release candidate) returns placeholder data labelled `fixture`. On the backend release candidate (`feature/13b-release-candidate`), `GET /trends` under `CATALOG_MODE=cached` is already wired to our 12 real cached snapshots — integrated and validated, not yet deployed. Either way, these are GitHub developer-activity counts, never hiring demand or job-market growth.
- **App output not fully checked.** We checked only the deployed GET endpoints. Matching, roadmap and project outputs come from POST endpoints we did not call, so app roadmap hours are not confirmed. Our hour figures are standalone.
- **30 roles prepared, 8 live.** The 30-role dataset is prepared and validated but not merged; the deployed app still shows the first 8 roles. The 22 newer roles are not in the app yet. They have no portfolio projects, and some of their skills have no learning resource yet (the roadmap says so).
- **O*NET is US-based.** It describes typical requirements in the US, not the needs of a specific employer or country.
- **Limited coverage** (fewer of our 20 skills fit these roles): `financial_analyst` and `financial_risk_specialist` (O*NET has not yet published their skills data); `information_security_analyst` and `logistician` (our 20 skills lack their main tools).
- **Team estimates.** These are our own choices, not source data: all tool importances, the required/optional split, the rules for which O*NET skills a role includes, 4 raised thinking-skill scores, learning hours where the provider gives none, all project hours, the SDG links and reasons, the 15% trend threshold, and the scenario multipliers (±10% moderate, ±25% fast).
- **Licences we only link to:**
  - CS50x is CC BY-NC-SA 4.0 (non-commercial). Jawad checked its Week 0 to Week 10 (11 weeks) in a browser on 2026-10-22. It states no hours, so its 110 h stays a team estimate.
  - The QGIS Training Manual's page footer names no licence ("© Copyright 2002-now, QGIS project").
  - Onshape's CAD course is under Onshape's own terms of use.
  - For all three, we link only and never copy the material.
- **Not checked by Jawad in a browser:** every source marked "Automated fetch" in the tables above, including the first 8 O*NET pages, the skill scores and tool lists of the 22 newer O*NET pages (only their titles, codes and 3 mathematics scores were checked by Jawad, on 2026-10-24), 7 learning resources and every project dataset except UCI Concrete. These were checked by automated fetches only.
- **No hiring prediction.** Scores are a skill-alignment estimate (`profile_alignment_estimate`), not a chance of getting hired.
