# Tools Declaration inputs — Jawad's part

For the Mustaqbal AI Tools Declaration. My part covers `data/**`, `services/trends/**`, `services/catalog/**`, `services/roadmaps/**`, `services/sdg/**`, plus `docs/source-register.md` and my own docs. Based on `docs/jawad-ai-usage.md` (on branches `feat/jawad-trends-data` and `feat/jawad-video-links`).

## AI tools

| Tool | What it was used for | How much AI was involved |
|---|---|---|
| **Claude Code** (Anthropic). Models: Claude Sonnet 5 at first, then Claude Opus 5.5; the `Co-Authored-By` line on each commit shows which. | Writing the Python code and tests in my folders; building the JSON data files; fetching public pages to check sources, licences, prices and hours; running the tests; drafting my docs (including this file) and commit messages. | **High for code and drafting.** Claude Code wrote most of the code, tests, data files and docs from my prompts. I set the rules, made the decisions listed below, approved each step before files were written, and re-ran all test suites myself. In my own browser, I checked 9 learning resources (including the 2 freeCodeCamp.org YouTube videos), the UCI Concrete dataset, the CS50x licence page and the QGIS Training Manual's footer. On 2026-10-24 I checked the titles and codes of the 22 newer O*NET pages and 3 mathematics scores. |
| **Claude** (claude.ai chat, project "SDC Hackathon") | Planning, reviewing pushed code on GitHub, web searches for course leads, and drafting the prompts I gave Claude Code. | **Medium, advice only.** It did not write any files in the repo. |

**Decisions I made (not AI):**
- Chose the 4 starter roles and the 4 extra roles, and confirmed their O*NET matches.
- Gave the candidate list and alternates for the 22 newer roles. Claude Code checked them and replaced Epidemiologists (already used by Public Health Analyst) with the first alternate, Hydrologists.
- Chose GitHub as the trend source, with the 30-day windows, the 15% threshold, and "cached" or "unavailable" (never fake "live") on failure.
- Swapped out unsuitable datasets: SEC, then UCI Air Quality because it is research-only.
- Gave the direct YouTube links and video lengths for the statistics and Excel videos.

**Not AI-decided:** no AI tool decides a student's score. Scores come from Hussain's fixed, documented formula.

## 30-role dataset

**Status of the 30-role dataset: in the deployed app.** The deployed app showed **30 roles** when checked on **2026-10-24 at 19:50 UTC (2026-10-25 03:50 MYT)**: `GET /api/v1/sdgs/{role_id}` returned role SDG mappings (`data_mode: "cached"`) for all 30 role IDs, and one earlier `POST /api/v1/careers/match` with an invented profile (19:43 UTC) returned `catalog_coverage` 30 of 30. The data is validated: all 8 of Jawad's test suites pass, and Rehan's cached-data validators accept it. The app's match, roadmap and project responses carry `data_mode: "fixture"` and the UI shows a "Demo data" badge; this label is being fixed. Their real source is our cached data.

**Limited coverage** (fewer of our 20 skills fit these roles; the app labels them): `financial_analyst` and `financial_risk_specialist` (O*NET has not yet published their skills data); `information_security_analyst` and `logistician` (our 20 skills lack their main tools); `public_health_analyst` (no health-specific skill in our 20).

**Team estimates, not source data:** tool importances, required/optional flags, the inclusion rules (which O*NET skills a role gets: thinking skills only with an O*NET score of 50 or more, Attention to Detail only with a Work Style score of 100) and the SDG links and reasons.

Jawad checked the titles and codes of the 22 newer O*NET pages in a browser on 2026-10-24 (MYT); all matched. He also spot-checked 3 mathematics scores on their Details pages (Statistician 97, Data Scientist 85, Actuary 85). Their other skill scores and tool lists were fetched automatically by Claude Code and not checked by hand.

## Data sources

| Source | Used for | Licence / terms |
|---|---|---|
| O*NET OnLine (US Dept. of Labor), 30 occupation pages plus 23 Software Skills CSV exports (fetched by Claude Code; for the 22 pages added on 2026-10-24, Jawad checked titles, codes and 3 mathematics scores in a browser) | Role skills, 0-100 importance scores and technology tools | CC BY 4.0, attribution required (page footer: "licensed under a Creative Commons Attribution 4.0 International License"). Attribution line: "Source: O*NET OnLine by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA), licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)." |
| GitHub REST API — Search Repositories | Trend signal: new repositories per skill topic, 30 days vs the previous 30 | GitHub Terms of Service. 12 saved snapshots (retrieved 2026-10-21 and 2026-10-22) exist as data and in my standalone `services/trends`. The demo makes no live GitHub request. **Shown in the app:** on 2026-10-24 at 19:50 UTC, the deployed `/api/v1/trends` returned these 12 snapshots (`data_mode: "cached"`, `source_status: "stale"`). 8 of our 20 skills have no signal. Developer activity, NOT live and NOT job demand. |
| Microsoft Learn: catalog API, 4 learning paths and modules, and 1 VBA documentation page | Learning resources; provider-stated hours from the catalog API's `duration_in_minutes` | Free to access |
| MathWorks MATLAB Onramp, MIT OpenCourseWare 18.05, SAS Programming 1, Alison, MDN, GnuCash guide, 2 freeCodeCamp.org videos on YouTube | Learning resources | Free to access (see `docs/source-register.md`) |
| Harvard CS50x 2026 | Learning resource (programming) | CC BY-NC-SA 4.0; we link only and never copy or redistribute it |
| QGIS Training Manual | Learning resource and project tutorial (GIS) | No licence named on the page (footer: "© Copyright 2002-now, QGIS project"); we link only |
| Onshape CAD Basics | Learning resource and project tutorial (CAD) | Onshape's own terms of use; we link only |
| UCI Machine Learning Repository: 8 datasets | Portfolio projects (linked, not copied) | CC BY 4.0 |
| World Bank — World Development Indicators | Portfolio projects (linked, not copied) | Creative Commons Attribution 4.0 |
| UN Sustainable Development Goals (17 goals and their targets; target wording for the 22 newer roles checked against the UN Statistics Division SDG API) | SDG mapping for every role and skill (team judgment). **Shown in the app for all 30 roles:** on 2026-10-24 at 19:50 UTC, the deployed `/api/v1/sdgs/{role_id}` returned role mappings for all 30 role IDs (`data_mode: "cached"`). | Public UN framework |

## Software and libraries

| Tool | Used for |
|---|---|
| Python 3.14 (CPython) and its standard library (`json`, `pathlib`, `urllib`, `re`, `datetime`, and others) | All of my services and tests. My code uses no third-party packages at runtime. |
| Pydantic v2 | Only in tests, to check my output against copies of Rehan's backend schemas |
| Git and GitHub | Version control. Branches: `feat/jawad-trends-data` (PR #1), `feat/jawad-video-links` (PR #2), `feat/jawad-data-fixes` (PR #5), `feat/jawad-30-roles`, `feat/jawad-docs` and `feat/jawad-docs-final` |
| Hussain's matcher (`services/matching`, his branch, used read-only) | Tested that my data works with his matcher, in a throwaway worktree. Nothing was committed there. |

## Not used in my part
I did not use RunPod, Replit, or a Gemini/OpenAI model in my part. The app is deployed on Replit by Rehan (https://mustaqbal-ai.replit.app). I checked it with GET requests, plus one test of its match, scenario, roadmap and project endpoints with invented profiles (no CV upload).
