# PRD inputs — data (Jawad)

Ready-to-paste text for the data sections of the Mustaqbal AI PRD.

**Where this comes from:** `docs/source-register.md` and the files in `data/` on branch `feat/jawad-video-links` (PR #2, which is stacked on PR #1, `feat/jawad-trends-data`). Those files are not on `main` yet. Dates are when we checked each source; all are in 2026.

**What the data contains** (counted from the files on `feat/jawad-video-links`):

| Item | Count |
|---|---|
| Career roles | 8 |
| Skills | 20 |
| Learning resources | 16 |
| Portfolio projects | 17 |
| Trend snapshots (cached) | 12 |
| Role-to-SDG links / skill-to-SDG links | 11 / 20 |

---

## (a) Data sources

"Who checked": "Jawad, manually in browser" wherever `docs/source-register.md` says so. Every other source was checked by an automated fetch run by Claude Code (see `docs/jawad-ai-usage.md`).

**Role and skill requirements (O*NET OnLine, US Department of Labor)**

| Source | What we use it for | Licence | Source's own update date / when we checked | Who checked |
|---|---|---|---|---|
| O*NET — Business Intelligence Analysts (15-2051.01) | Skills and tools for the Data Analyst role | Public domain (US Dept. of Labor; free to use with attribution) | Updated 2026-10-06 / checked 2026-10-21 | Automated fetch (Claude Code) |
| O*NET — Financial and Investment Analysts (13-2051.00) | Tools and work styles for the Financial Analyst role (O*NET says its other sections are still being collected) | Public domain | 2026-10-06 / 2026-10-21 | Automated fetch (Claude Code) |
| O*NET — Mechanical Engineers (17-2141.00) | Skills and tools for the Mechanical Engineer role | Public domain | 2026-10-06 / 2026-10-21 | Automated fetch (Claude Code) |
| O*NET — Epidemiologists (19-1041.00) | Skills and tools for the Public Health Analyst role (closest O*NET match) | Public domain | 2026-10-06 / 2026-10-21 | Automated fetch (Claude Code) |
| O*NET — Software Developers (15-1252.00) | Skills and tools for the Software Developer role | Public domain | 2026-10-06 / 2026-10-22 | Automated fetch (Claude Code) |
| O*NET — Accountants and Auditors (13-2011.00) | Skills, work styles and tools for the Accountant role | Public domain | 2026-10-06 / 2026-10-22 | Automated fetch (Claude Code) |
| O*NET — Civil Engineers (17-2051.00) | Skills and tools for the Civil Engineer role | Public domain | 2026-10-06 / 2026-10-22 | Automated fetch (Claude Code) |
| O*NET — Environmental Scientists and Specialists, Including Health (19-2041.00) | Skills and tools for the Environmental Scientist role | Public domain | 2026-10-06 / 2026-10-22 | Automated fetch (Claude Code) |

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
| freeCodeCamp.org — Statistics - A Full University Course on Data Science Basics (YouTube, https://youtu.be/xxpc-HPKN28; 8.25 h, video length shown on YouTube) | Mathematics | Free (stated) | 2026-10-22 | Jawad, manually in browser |
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

Checked and **not used**: UCI Air Quality (its page says research use only), Natural Earth, SEC Financial Statement Data Sets, Our World in Data COVID-19 repository and WHO Global Health Observatory (we could not read a licence for these). Every URL is re-checked by `services/catalog/check_links.py`. On 2026-10-22 (UTC), all 38 URLs returned OK (`docs/link-check-report.md` on `feat/jawad-video-links`).

---

## (b) How the data is produced

**Role catalog.** We have 8 roles, 2 in each industry group: Technology & AI, Business & Finance, Engineering & Manufacturing, and Healthcare & Sustainability. Each role is linked to one real O*NET occupation, and the skills come from that occupation's O*NET page. We do not invent roles or skills. Every role lists its evidence (`evidence_ids`), so each role can be traced back to its source.

**Skill importance (1 to 5).**
- For thinking skills (like critical thinking or mathematics), O*NET gives a score from 0 to 100. We turn it into 1 to 5: 70 or more = 5, 60s = 4, 50s = 3, 40s = 2, below 40 = 1. In 4 cases we raised mathematics or problem solving by one step, and we mark those as team estimates.
- For tools (like Excel, SQL or GIS), O*NET only says the tool is used, not how important it is. So every tool importance is a team estimate.
- Whether a skill is "required" or "optional" is also our own choice.

**Trend signals.**
- **How a signal is made:** for 12 of our 20 skills there is a clear GitHub topic. For each one, we count the new GitHub repositories with that topic in the last 30 days and compare them with the 30 days before. More than 15% up is "rising", more than 15% down is "falling", anything else is "stable". If a request fails, the result is "unknown". Each result is saved as a dated snapshot.
- **What exists now:** 12 saved snapshots. Today 9 skills are rising and 3 are stable.
- **What the demo shows:** `get_trends()` in `services/trends` reads only these saved snapshots. It reports `source_status: "cached"` with the date of the last successful refresh, and never calls a cached or failed result "live". The demo makes no live GitHub request.
- **Scenarios:** when signals are passed to Hussain's two future scenarios (moderate and fast AI adoption), only rising or falling signals change a skill's weight, a little up or down.

**SDG mapping.** Every role and every skill is linked to at least one UN Sustainable Development Goal, with a one-sentence reason. For example, the Civil Engineer role is linked to SDG 9 (infrastructure) and SDG 11 (sustainable cities), and SQL is linked to SDG 8 (decent work, target 8.6). These links are the team's own judgment.

**Learning roadmap** (`get_roadmap()` in `services/roadmaps`).
- For each missing skill, the roadmap picks one free learning resource we have checked.
- Required skills come first, ordered by importance, then optional skills.
- If a resource assumes another skill (for example, VBA assumes Excel), that skill comes first or a warning is shown.
- Each step has hours, either the provider's own number or a team estimate, and a label saying which.
- If we have no checked resource for a skill, the roadmap says so instead of guessing.

**Portfolio projects.** Each role has 2 or 3 projects built on a real open dataset or an official tutorial. Each project has 4 to 6 steps and an hours number, which is the sum of our per-step estimates. Datasets are only linked, never copied into the app.

**Status in the backend** (read-only check of Rehan's branch `feature/rehan-backend-foundation` at `f0cb9db`, 2026-10-23):
- **Data served:** the backend can serve this cached data for roles, skills, SDG mappings, roadmap resources and projects when `CATALOG_MODE=cached`. The default is `fixture`.
- **Data version:** its copy of the data matches PR #1, not yet the updated video links in PR #2.
- **Trends:** the backend's `GET /trends` route does not use these snapshots yet. It returns labelled placeholder data (`data_mode: "fixture"`).
- **Roadmap:** the backend has its own roadmap code. It orders steps by role weight and puts the hours note in the step's reason text, so its output may differ from `get_roadmap()`.

---

## (c) Honest limitations

- **GitHub activity is not job demand.** The trend signal counts new GitHub repositories. It does not count job openings, and it is global, not Malaysia-specific.
- **One snapshot is not a trend.** Each skill has one 30-day vs 30-day comparison. GitHub topic tags are voluntary, so activity can be undercounted.
- **Cached, not live.** The trend data is 12 saved snapshots from 2026-10-21 and 2026-10-22, labelled "cached" with their dates. Nothing is refreshed live in the demo.
- **Trends are not in the app yet.** The backend's trends route still returns placeholder data, so trend signals are shown from `services/trends` directly.
- **Only 8 roles and 20 skills.** The goal is up to 30 roles. With 8, matches and roadmaps only cover those 8 jobs.
- **O*NET is US-based.** It describes typical requirements in the US, not the needs of a specific employer or country. For Financial Analysts, O*NET says data collection is still underway, so that role uses only O*NET's tools and work-styles data.
- **Team estimates.** These are our own choices, not source data: all tool importances, the required/optional split, 4 raised thinking-skill scores, learning hours where the provider gives none, all project hours, the SDG links and reasons, the 15% trend threshold, and the scenario multipliers (±10% moderate, ±25% fast).
- **Licences we only link to:**
  - CS50x is CC BY-NC-SA 4.0 (non-commercial). Jawad checked its Week 0 to Week 10 (11 weeks) in a browser on 2026-10-22. It states no hours, so its 110 h stays a team estimate.
  - The QGIS Training Manual's page footer names no licence ("© Copyright 2002-now, QGIS project").
  - Onshape's CAD course is under Onshape's own terms of use.
  - For all three, we link only and never copy the material.
- **Not checked by Jawad in a browser:** every source marked "Automated fetch" in the tables above, including all 8 O*NET pages, 7 learning resources and every project dataset except UCI Concrete. These were checked by automated fetches only.
- **No hiring prediction.** Scores are a skill-alignment estimate (`profile_alignment_estimate`), not a chance of getting hired.
