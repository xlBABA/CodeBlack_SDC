# AI usage — Jawad (data, catalog, trends, roadmaps, SDGs)

Disclosure for the SDC Hackathon 2026 submission. Tool: **Claude Code** (Anthropic), run from my own prompts during the hacking window (2026-10-21 to 2026-10-24). Models: Claude Sonnet 5 at first, then Claude Opus 5.5 (the `Co-Authored-By` lines on each commit show which). I gave the instructions and rules, and approved each step before files were written. Claude Code ran the tests during development. I re-ran all suites myself with the single command below and saw them pass:

```
C:\Users\jawad\AppData\Local\Python\pythoncore-3.14-64\python.exe -m services.catalog.run_all_tests
```

(`services/catalog/run_all_tests.py` runs all 8 suites in order and prints one PASS/FAIL summary.)

## What Claude helped me build

| Commit | What | Files |
|---|---|---|
| ce0d4bb, d54cfdf* | Source register; 4 verified roles from O*NET; skills; SDG mapping for every role and skill | `docs/source-register.md`, `data/roles.json`, `data/skills.json`, `data/sdg_mappings.json`, `services/catalog/tests/test_roles_schema.py` |
| ce78f4e | Converted the data to Hussain's matcher format and tested it against his real matcher in a throwaway worktree (nothing committed there) | `data/skills.json`, `data/roles.json`, `data/sdg_mappings.json` |
| dcee82f | Fixed `data_mode` to `cached`; documented how every 1-5 importance number was derived | `data/skills.json`, `docs/source-register.md` |
| ff83304, 725dcb2 | GitHub trend feed: fetch, snapshot, aggregate, `refresh_all()`, `get_trends()`, the first real snapshot, and the "change since last snapshot" field | `services/trends/**`, `data/trend_snapshots/*.json` |
| e21eb20 | `get_roles()`, `get_role()`, `get_sdg_impact()` | `services/catalog/catalog.py`, `services/sdg/**` |
| 1f3611d, 675d938, eecd84c | Learning resources and `get_roadmap()`, with hours labelled provider-stated or team estimate | `data/resources.json`, `services/roadmaps/roadmap.py` |
| 9e782c1 | Portfolio projects and `get_projects()` | `data/projects.json`, `services/roadmaps/projects.py` |
| d8152b4 | Link checker and report, provenance test, scenario assumptions, this file | `services/catalog/check_links.py`, `docs/link-check-report.md`, `services/catalog/tests/test_provenance.py`, `services/catalog/tests/test_check_links.py`, `docs/jawad-ai-usage.md` |
| 2838340 | One command that runs all test suites; corrections to this file | `services/catalog/run_all_tests.py`, `docs/jawad-ai-usage.md` |
| ab21a9c | Renamed the product to "Mustaqbal AI" in 4 docstrings and 2 User-Agent labels (no IDs changed) | `services/*/__init__.py`, `services/trends/github_client.py`, `services/catalog/check_links.py` |
| ecdeee3 | 4 more verified roles from O*NET (Software Developer, Accountant, Civil Engineer, Environmental Scientist), 6 new skills, SDG mappings, trend coverage and first real GitHub snapshots for the new skills, learning resources, and 2 portfolio projects per new role | `data/*.json`, `data/trend_snapshots/*.json`, `docs/source-register.md`, `services/trends/queries.py`, `services/trends/README.md`, `services/catalog/tests/test_catalog.py`, `services/roadmaps/tests/test_roadmap.py`, `services/roadmaps/tests/test_projects.py` |
| a5045cb | Updated link-check report and this file | `docs/link-check-report.md`, `docs/jawad-ai-usage.md` |
| 4ba98a0 | Recorded my browser checks for 5 resources and the UCI Concrete dataset; moved the GnuCash resource to its gnucash.org guide URL | `data/resources.json`, `docs/source-register.md`, `services/roadmaps/tests/test_roadmap.py`, `docs/link-check-report.md`, `docs/jawad-ai-usage.md` |
| 86bdcb5 | Pointed the statistics and Excel resources at their direct freeCodeCamp YouTube videos, with video lengths I saw (statistics hours now provider-stated, 8.25 h) | `data/resources.json`, `docs/source-register.md`, `services/roadmaps/tests/test_roadmap.py`, `services/catalog/tests/test_check_links.py`, `docs/link-check-report.md`, `docs/jawad-ai-usage.md` |
| 3bae8f4 | Recorded my browser checks of the CS50x licence (CC BY-NC-SA 4.0) and week count, and that the QGIS manual names no licence | `docs/source-register.md`, `data/resources.json` (note text only), `docs/link-check-report.md`, `docs/jawad-ai-usage.md` |
| 72e7ebc | Moved the two video notes (what I saw in the browser; instructor name from a third-party article) into the existing `url_note` field, so the data fits Rehan's cached importer with no new fields; added a test for his allowed field list | `data/resources.json`, `services/roadmaps/tests/test_roadmap.py`, `docs/jawad-ai-usage.md` |
| 1dce89f | Recorded that the statistics video's instructor (Monika Wahi) is confirmed in its YouTube description, as I checked in a browser (text only, in the existing `url_note`) | `data/resources.json`, `docs/source-register.md`, `docs/jawad-ai-usage.md` |
| 2957c71 | Added Python to Data Analyst (importance 3, required; team estimate) after I found it listed on O*NET 15-2051.01, and replaced the wrong "NOT found" note | `data/roles.json`, `data/skills.json`, `docs/source-register.md`, `services/catalog/tests/test_catalog.py` |
| 94d1719 | Added `data/skill_not_equivalent.json` (12 close-but-different skill pairs for Hussain's matcher) with a reason for each in the source register | `data/skill_not_equivalent.json`, `docs/source-register.md`, `services/catalog/tests/test_catalog.py` |
| 76d6b7d | Corrected the O*NET licence from "Public domain" to CC BY 4.0 (attribution required), as the O*NET page footer says; updated the link-check report and this file | `docs/source-register.md`, `docs/link-check-report.md`, `docs/jawad-ai-usage.md` |
| 5fd95c4 | Removed two inaccurate "decisions" bullets from this file | `docs/jawad-ai-usage.md` |
| d4d3acd | Added the O*NET attribution line and the Data Analyst mapping note | `docs/source-register.md` |
| 9817054 | Added 6 CV skill aliases (CAD, QGIS, Microsoft SQL Server, MySQL, PostgreSQL, Advanced Excel) and a no-collision test | `data/skills.json`, `services/catalog/tests/test_catalog.py` |
| cbf3012 | Added 22 roles from O*NET to reach 30 roles. Claude Code fetched the O*NET pages, parsed the skill scores and tool lists, and wrote the records | `data/roles.json`, `data/skills.json` (source ids only), `docs/source-register.md` |
| 9f7425a | SDG rows with reasons for the 22 new roles (team estimates, written by Claude Code) | `data/sdg_mappings.json` |
| d5b0535 | Tests for the 30-role catalog; the two tests that hardcoded 8 roles now check 30 | `services/catalog/tests/test_catalog.py`, `services/roadmaps/tests/test_projects.py` |
| 8cd1166 | 30-role section in the source register, link-check report (85 URLs, all OK), this file | `docs/source-register.md`, `docs/link-check-report.md`, `docs/jawad-ai-usage.md` |
| feat/jawad-ph-fix | Claude Code analysed the Public Health Analyst ranking problem Hussain reported and applied the fix that Rehan and Hussain approved ("Option C"): the role was rebuilt with the same O*NET rule as the 22 newer roles and marked limited coverage | `data/roles.json` (public_health_analyst only), `docs/source-register.md`, tests |
| feat/jawad-ph-fix | Claude Code checked mechanical_engineer against O*NET 17-2141.00 (read-only) and wrote the findings up as a known limitation; Rehan decided to leave the record unchanged for this release | `docs/source-register.md`, `docs/jawad-ai-usage.md` |

\* I made commit d54cfdf myself, but the changes in it were written by Claude.

Claude also wrote the tests in each `tests/` folder and ran them. It fetched public pages (O*NET pages and its Software Skills CSV export, GitHub API, Microsoft Learn's catalog API, UCI, World Bank, SAS, MIT OCW, MathWorks, MDN, Harvard CS50, GnuCash, QGIS) to verify sources, and recorded what it could not verify instead of guessing.

## Other Claude use
I also used a separate Claude chat (claude.ai, project "SDC Hackathon") for:
- planning
- reviewing pushed code on GitHub
- web searches for course leads
- drafting the prompts I gave Claude Code

It did not write any files in the repo.

## Decisions I made (not Claude)
- Picked the 4 starter roles (Data Analyst, Financial Analyst, Mechanical Engineer, Public Health Analyst).
- Chose GitHub as the trend source, and set its rules: compare new repos in the last 30 days with the previous 30, use a >15% threshold, show `cached` or `unavailable` on failure (never fake `live`), and cover only skills with a clear topic.
- Replaced the SEC project with the UCI credit-card dataset, kept the diabetes project with a data note, and accepted a tutorial as the CAD project's source.
- Chose the 4 extra roles and confirmed their O*NET mappings: Accountant = "Accountants and Auditors", Environmental Scientist = "Environmental Scientists and Specialists, Including Health".
- Gave the list of 22 candidate O*NET occupations and 5 alternates for the 30-role catalog (in my prompt). Claude Code checked each code and title, and replaced Epidemiologists (already used by Public Health Analyst) with the first alternate, Hydrologists.
- Asked for Python to be added to Data Analyst after checking O*NET, and approved (with Hussain) the 12 `not_equivalent` skill pairs.
- Dropped the UCI Air Quality dataset, because its page says it is for research use only and this repo is public under Apache-2.0. Required the replacement to be CC BY, CC0 or public domain, with the licence read from the dataset's own page.

## What I checked myself in my browser (2026-10-22)
These have `"checked_by": "Jawad, manually in browser"` in `data/resources.json`:
- Alison, *Thinking Critically*: free, "Avg. Duration 1.5-3 Hours".
- freeCodeCamp *Microsoft Excel Tutorial for Beginners - Full Course* on YouTube (https://youtu.be/Vl0H-qTclOg): the link opens, the title, and length 2:26:09. Earlier I checked it embedded on KDnuggets.
- Onshape *CAD Basics (Learning Pathway)*: free sign-in, 7 topics, no stated duration.
- freeCodeCamp *Statistics - A Full University Course on Data Science Basics* on YouTube (https://youtu.be/xxpc-HPKN28): the link opens, the title, and length 8:15:04. Earlier I had only seen an ExpertBeacon article about it. The instructor name (Monika Wahi) is confirmed in the YouTube description ("Course by Monika Wahi"), checked in my browser on 2026-10-22.
- Microsoft Learn, *Introduction to Git*: free, "1 hr 26 min".
- MDN, *Dynamic scripting with JavaScript*: free.
- Harvard CS50x 2026: free; Week 0 to Week 10 = 11 weeks; no hours stated, so the 110 h stays a team estimate. Licence CC BY-NC-SA 4.0, read on https://cs50.harvard.edu/x/license/; we link only and do not copy or redistribute the material.
- GnuCash *Tutorial and Concepts Guide*, at https://www.gnucash.org/viewdoc.phtml?rev=5&lang=C&doc=guide.
- QGIS Training Manual: the module list includes Vector Analysis and Forestry Application. The page footer says only "© Copyright 2002-now, QGIS project" and names no licence, so we record "licence not stated" and link only.

On 2026-10-23 I checked https://www.onetonline.org/link/tt/15-2051.01/43232405 in my browser: Python (and R and Jupyter Notebook) is listed for Business Intelligence Analysts under "Object or component oriented development software", and is not marked as a Hot Technology.

I also checked the UCI Concrete Compressive Strength dataset page: CC BY 4.0. This one is a project dataset, so it is noted in `docs/source-register.md`, not in `resources.json`.

Everything else was checked by automated requests from Claude Code. See `docs/link-check-report.md`.

The O*NET licence (CC BY 4.0, from the page footer) was read by an automated fetch by Claude Code on 2026-10-23, not by me in a browser.

Not yet checked by me: the other new project datasets (including the UCI Beijing Multi-Site Air Quality dataset, CC BY 4.0) and the O*NET pages for the 4 newer roles.

On 2026-10-24 I checked the 22 O*NET pages for the roles added in cbf3012 in my browser: all 22 titles and codes matched. I also spot-checked 3 Mathematics scores on their Details pages: Statistician 97, Data Scientist 85, Actuary 85. All other skill scores and tool lists on those pages (and the Software Skills CSV exports) were fetched automatically by Claude Code and not checked by hand. The UN SDG target wording used in their SDG reasons was also fetched automatically and not checked by me. Each O*NET URL is listed in `docs/source-register.md`.

## What is a team estimate (not from a source)
- **Role importance numbers:** the cases where `roles.json` differs from O*NET's bucketed score (mostly mathematics), every tool-skill importance, and every `required: true/false` flag. For the 22 roles added on 2026-10-24, also which listed tools each role uses, and the rules for which cognitive skills are included (O*NET score 50 or more) and when attention_to_detail is included (Work Style impact 100). See "Importance score methodology" in `docs/source-register.md`.
- **Learning hours** where the provider states none: VBA doc 1.5 h, MATLAB Onramp 3 h, MIT 18.05 112 h, SAS Programming 1 21 h, Onshape CAD Basics 7 h, MDN JavaScript 23 h, CS50x 110 h, GnuCash guide 12 h, QGIS manual 14 h.
- **All project hours.** Each is the sum of per-milestone estimates.
- **SDG mappings.** The SDG chosen for each role and skill, and its reason, are our own judgment. The 28 rows for the 22 new roles end with "Team estimate."
- **Trend rules.** The 15% threshold, which skills get a GitHub topic, and the exclusion of 8 skills.
- **Scenario multipliers** (±10% moderate, ±25% fast). These are Hussain's team assumptions, not forecasts.
