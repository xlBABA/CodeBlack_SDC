# Tools Declaration inputs — Jawad's part

For the Mustaqbal AI Tools Declaration. My part covers `data/**`, `services/trends/**`, `services/catalog/**`, `services/roadmaps/**`, `services/sdg/**`, plus `docs/source-register.md` and my own docs. Based on `docs/jawad-ai-usage.md` (on branches `feat/jawad-trends-data` and `feat/jawad-video-links`).

## AI tools

| Tool | What it was used for | How much AI was involved |
|---|---|---|
| **Claude Code** (Anthropic). Models: Claude Sonnet 5 at first, then Claude Opus 5.5; the `Co-Authored-By` line on each commit shows which. | Writing the Python code and tests in my folders; building the JSON data files; fetching public pages to check sources, licences, prices and hours; running the tests; drafting my docs (including this file) and commit messages. | **High for code and drafting.** Claude Code wrote most of the code, tests, data files and docs from my prompts. I set the rules, made the decisions listed below, approved each step before files were written, and re-ran all test suites myself. In my own browser, I checked 9 learning resources (including the 2 freeCodeCamp.org YouTube videos), the UCI Concrete dataset, the CS50x licence page and the QGIS Training Manual's footer. |
| **Claude** (claude.ai chat, project "SDC Hackathon") | Planning, reviewing pushed code on GitHub, web searches for course leads, and drafting the prompts I gave Claude Code. | **Medium, advice only.** It did not write any files in the repo. |

**Decisions I made (not AI):**
- Chose the 4 starter roles and the 4 extra roles, and confirmed their O*NET matches.
- Chose GitHub as the trend source, with the 30-day windows, the 15% threshold, and "cached" or "unavailable" (never fake "live") on failure.
- Swapped out unsuitable datasets: SEC, then UCI Air Quality because it is research-only.
- Gave the direct YouTube links and video lengths for the statistics and Excel videos.

**Not AI-decided:** no AI tool decides a student's score. Scores come from Hussain's fixed, documented formula.

## Data sources

| Source | Used for | Licence / terms |
|---|---|---|
| O*NET OnLine (US Dept. of Labor), 8 occupation pages plus 1 Software Skills CSV export | Role skills, 0-100 importance scores and technology tools | CC BY 4.0, attribution required (page footer: "licensed under a Creative Commons Attribution 4.0 International License") |
| GitHub REST API — Search Repositories | Trend signal: new repositories per skill topic, 30 days vs the previous 30 | GitHub Terms of Service. 12 saved snapshots (retrieved 2026-10-21 and 2026-10-22) exist as data and in my standalone `services/trends`. The demo makes no live GitHub request. **Not shown in the app:** the deployed `/api/v1/trends` returns placeholder data labelled `fixture`. |
| Microsoft Learn: catalog API, 4 learning paths and modules, and 1 VBA documentation page | Learning resources; provider-stated hours from the catalog API's `duration_in_minutes` | Free to access |
| MathWorks MATLAB Onramp, MIT OpenCourseWare 18.05, SAS Programming 1, Alison, MDN, GnuCash guide, 2 freeCodeCamp.org videos on YouTube | Learning resources | Free to access (see `docs/source-register.md`) |
| Harvard CS50x 2026 | Learning resource (programming) | CC BY-NC-SA 4.0; we link only and never copy or redistribute it |
| QGIS Training Manual | Learning resource and project tutorial (GIS) | No licence named on the page (footer: "© Copyright 2002-now, QGIS project"); we link only |
| Onshape CAD Basics | Learning resource and project tutorial (CAD) | Onshape's own terms of use; we link only |
| UCI Machine Learning Repository: 8 datasets | Portfolio projects (linked, not copied) | CC BY 4.0 |
| World Bank — World Development Indicators | Portfolio projects (linked, not copied) | Creative Commons Attribution 4.0 |
| UN Sustainable Development Goals (17 goals and their targets) | SDG mapping for every role and skill (team judgment). **Shown in the app:** the deployed `/api/v1/sdgs/{role_id}` returns these mappings (`data_mode: "cached"`). | Public UN framework |

## Software and libraries

| Tool | Used for |
|---|---|
| Python 3.14 (CPython) and its standard library (`json`, `pathlib`, `urllib`, `re`, `datetime`, and others) | All of my services and tests. My code uses no third-party packages at runtime. |
| Pydantic v2 | Only in tests, to check my output against copies of Rehan's backend schemas |
| Git and GitHub | Version control. Branches: `feat/jawad-trends-data` (PR #1), `feat/jawad-video-links` (PR #2), `feat/jawad-docs` and `feat/jawad-docs-final` |
| Hussain's matcher (`services/matching`, his branch, used read-only) | Tested that my data works with his matcher, in a throwaway worktree. Nothing was committed there. |

## Not used in my part
I did not use RunPod, Replit, or a Gemini/OpenAI model in my part. The app is deployed on Replit by Rehan (https://mustaqbal-ai.replit.app). I only read it with GET requests to check what it shows.
