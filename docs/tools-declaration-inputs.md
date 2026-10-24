# Tools Declaration inputs — Jawad's part

**This is a supporting input document covering only Jawad's part, not the complete official submitted Tools Declaration.** For the Mustaqbal AI Tools Declaration — merge with the other members' inputs (e.g. Hussain's) into the final declaration; don't submit this file alone. My part covers `data/**`, `services/trends/**`, `services/catalog/**`, `services/roadmaps/**`, `services/sdg/**`, plus `docs/source-register.md` and my own docs. Based on `docs/jawad-ai-usage.md` (on branches `feat/jawad-trends-data` and `feat/jawad-video-links`).

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

**Decisions Rehan made on my data (not me, not AI), 2026-10-24:** adding `onet_19_1041_00` to three skills' `source_ids` for the Public Health Analyst rebuild; adding the 2 new `skill_not_equivalent.json` pairs, after Hussain measured their embedding similarities (git/gis 0.74, financial_analysis_software/analytical_scientific_software 0.67) and Claude Code gathered the O*NET category evidence; leaving `mechanical_engineer` unchanged rather than rebuilding it under the 22-newer-roles rule, for release stability.

**Not AI-decided:** no AI tool decides a student's score. Scores come from Hussain's fixed, documented formula.

## 30-role dataset

**Status of the 30-role dataset: PREPARED, not live.** The 30 roles are on branch `feat/jawad-30-roles` (pushed, not merged). They are validated: all 8 of Jawad's test suites pass, and Rehan's cached-data validators accept them (checked read-only on his branches `feature/12b-team-integration` and `feature/13b-release-candidate`). On that release candidate, the 30 roles, 20 skills, and the 12 cached GitHub developer-activity snapshots (via `CATALOG_MODE=cached`) are integrated and validated. The **live deployed app (https://mustaqbal-ai.replit.app) still shows only the first 8 roles and fixture trend data** — it has not been republished with this release candidate, and its exact current behavior beyond what was last checked by a GET request is not confirmed. Do not claim that all 30 roles are live, and do not describe the GitHub signal as hiring demand or job-market growth. RunPod-assisted semantic matching is available where configured but has not been live-tested against this specific 30-role release candidate — do not claim otherwise. The 20-skill catalog and the original 8 roles are unchanged.

**Limited coverage** (fewer of our 20 skills fit these roles): `financial_analyst` and `financial_risk_specialist` (O*NET has not yet published their skills data); `information_security_analyst` and `logistician` (our 20 skills lack their main tools); `public_health_analyst` (added 2026-10-24 with the approved "Option C" rebuild — our 20-skill catalog cannot represent its epidemiology-specific knowledge or software, e.g. Biology, Medicine and Dentistry, CDC Epi Info).

**Team estimates, not source data:** tool importances, required/optional flags, the inclusion rules (which O*NET skills a role gets: thinking skills only with an O*NET score of 50 or more, Attention to Detail only with a Work Style score of 100) and the SDG links and reasons.

Jawad checked the titles and codes of the 22 newer O*NET pages in a browser on 2026-10-24 (MYT); all matched. He also spot-checked 3 mathematics scores on their Details pages (Statistician 97, Data Scientist 85, Actuary 85). Their other skill scores and tool lists were fetched automatically by Claude Code and not checked by hand.

## Data sources

| Source | Used for | Licence / terms |
|---|---|---|
| O*NET OnLine (US Dept. of Labor), 30 occupation pages plus 23 Software Skills CSV exports (fetched by Claude Code; for the 22 pages added on 2026-10-24, Jawad checked titles, codes and 3 mathematics scores in a browser) | Role skills, 0-100 importance scores and technology tools | CC BY 4.0, attribution required (page footer: "licensed under a Creative Commons Attribution 4.0 International License"). Attribution line: "Source: O*NET OnLine by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA), licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)." |
| GitHub REST API — Search Repositories | Trend signal: new repositories per skill topic, 30 days vs the previous 30 — developer-activity data, never hiring demand or job-market growth | GitHub Terms of Service. 12 saved snapshots (retrieved 2026-10-21 and 2026-10-22) exist as data and in my standalone `services/trends`. The demo makes no live GitHub request. **Not shown in the live deployed app:** the deployed `/api/v1/trends` (https://mustaqbal-ai.replit.app, not republished with the 30-role release candidate) returns placeholder data labelled `fixture`. **Shown on the backend release candidate** (`feature/13b-release-candidate`): `GET /trends` under `CATALOG_MODE=cached` already serves these same 12 snapshots — integrated and validated, not yet deployed. |
| Microsoft Learn: catalog API, 4 learning paths and modules, and 1 VBA documentation page | Learning resources; provider-stated hours from the catalog API's `duration_in_minutes` | Free to access |
| MathWorks MATLAB Onramp, MIT OpenCourseWare 18.05, SAS Programming 1, Alison, MDN, GnuCash guide, 2 freeCodeCamp.org videos on YouTube | Learning resources | Free to access (see `docs/source-register.md`) |
| Harvard CS50x 2026 | Learning resource (programming) | CC BY-NC-SA 4.0; we link only and never copy or redistribute it |
| QGIS Training Manual | Learning resource and project tutorial (GIS) | No licence named on the page (footer: "© Copyright 2002-now, QGIS project"); we link only |
| Onshape CAD Basics | Learning resource and project tutorial (CAD) | Onshape's own terms of use; we link only |
| UCI Machine Learning Repository: 8 datasets | Portfolio projects (linked, not copied) | CC BY 4.0 |
| World Bank — World Development Indicators | Portfolio projects (linked, not copied) | Creative Commons Attribution 4.0 |
| UN Sustainable Development Goals (17 goals and their targets; target wording for the 22 newer roles checked against the UN Statistics Division SDG API) | SDG mapping for every role and skill (team judgment). **Shown in the app for the first 8 roles only:** the deployed `/api/v1/sdgs/{role_id}` returns these mappings (`data_mode: "cached"`). | Public UN framework |

## Software and libraries

| Tool | Used for |
|---|---|
| Python 3.14 (CPython) and its standard library (`json`, `pathlib`, `urllib`, `re`, `datetime`, and others) | All of my services and tests. My code uses no third-party packages at runtime. |
| Pydantic v2 | Only in tests, to check my output against copies of Rehan's backend schemas |
| Git and GitHub | Version control. Branches: `feat/jawad-trends-data` (PR #1), `feat/jawad-video-links` (PR #2), `feat/jawad-data-fixes` (PR #5), `feat/jawad-30-roles`, `feat/jawad-docs` and `feat/jawad-docs-final` |
| Hussain's matcher (`services/matching`, his branch, used read-only) | Tested that my data works with his matcher, in a throwaway worktree. Nothing was committed there. |

## Not used in my part
I did not use RunPod, Replit, or a Gemini/OpenAI model in my part. The app is deployed on Replit by Rehan (https://mustaqbal-ai.replit.app). I only read it with GET requests to check what it shows.

## AI services the app uses at runtime (backend, branch `fix/rc-security-cv`)

This section covers the deployed app's own AI calls, not Jawad's data work above.

| Service | Model | Used for | Configuration (environment variable names only) |
|---|---|---|---|
| **OpenRouter** (provider endpoint: Z.AI, Singapore) | `z-ai/glm-5.3-flashx` | CV upload: reads the text of an uploaded PDF CV and suggests a draft profile. Every suggested skill must be quoted word-for-word from the CV and is mapped to our 20-skill catalogue by fixed rules. The student reviews and confirms everything; nothing is stored until they do. | `LLM_PROVIDER=openrouter`, `LLM_API_KEY`, `LLM_BASE_URL` (e.g. `https://openrouter.ai/api/v1`), `LLM_MODEL` (e.g. `z-ai/glm-5.3-flashx`), `LLM_TIMEOUT_SECONDS` (default 60). If any of the first four is missing, CV upload falls back to manual entry; it never uses the RunPod key. |
| **RunPod** (alternative CV extraction provider, the default) | GLM-5.3 | Same CV extraction, when `LLM_PROVIDER` is `runpod` or unset | `RUNPOD_API_KEY`, `RUNPOD_GLM_BASE_URL`, `RUNPOD_GLM_MODEL` |
| **RunPod** Serverless | `sentence-transformers/all-MiniLM-L6-v2` (embeddings) | Optional semantic skill similarity in matching (partial credit for a closely related skill). Without it, matching uses exact skills only and says so on every match. | `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT_ID` |

What is sent: up to 12,000 characters of the CV's text go to the CV extraction provider. Only skill names go to the embedding endpoint. Scores, profiles and IDs are never sent to either. OpenRouter's published data policy for the Z.AI endpoint (checked 2026-10-25 on https://openrouter.ai/z-ai/glm-5.3-flashx): no training on prompts, prompts not retained, not published. See `docs/cv-llm-benchmark.md` for the measured accuracy, latency and cost.

**Not AI-decided:** scores still come only from the fixed, documented matching formula; no language model scores a student.

**Data credit:** the role and skill data are from O*NET. The app shows this credit in the landing-page footer and on every role page: "Source: O*NET OnLine by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA), licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)."
