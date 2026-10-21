# AI usage — Jawad (data, catalog, trends, roadmaps, SDGs)

Disclosure for the SDC Hackathon 2026 submission. Tool: **Claude Code** (Anthropic), run from my own prompts during the hacking window (2026-10-21 to 2026-10-22). Models: Claude Sonnet 5 at first, then Claude Opus 5.5 (the `Co-Authored-By` lines on each commit show which). I gave the instructions and rules, and approved each step before files were written. Claude Code ran the tests during development. I re-ran all suites myself with the single command below and saw them pass:

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
| this commit | One command that runs all test suites; corrections to this file | `services/catalog/run_all_tests.py`, `docs/jawad-ai-usage.md` |

\* I made commit d54cfdf myself, but the changes in it were written by Claude.

Claude also wrote the tests in each `tests/` folder and ran them. It fetched public pages (O*NET, GitHub API, Microsoft Learn's catalog API, UCI, World Bank, SAS, MIT OCW, MathWorks) to verify sources, and recorded what it could not verify instead of guessing.

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
- Caught that `data_mode` should be `cached`, not `live`.
- Replaced the SEC project with the UCI credit-card dataset, kept the diabetes project with a data note, and accepted a tutorial as the CAD project's source.

## What I checked myself in my browser (2026-10-22)
These have `"checked_by": "Jawad, manually in browser"` in `data/resources.json`:
- Alison, *Thinking Critically*: free, "Avg. Duration 1.5-3 Hours".
- freeCodeCamp *Microsoft Excel Tutorial for Beginners - Full Course*, embedded on KDnuggets: player length 2:26:10.
- Onshape *CAD Basics (Learning Pathway)*: free sign-in, 7 topics, no stated duration.
- The ExpertBeacon article on Monika Wahi's freeCodeCamp statistics course. I have not yet seen the video page itself.

Everything else was checked by automated requests from Claude Code. See `docs/link-check-report.md`.

## What is a team estimate (not from a source)
- **Role importance numbers:** the cases where `roles.json` differs from O*NET's bucketed score (mostly mathematics), every tool-skill importance, and every `required: true/false` flag. See "Importance score methodology" in `docs/source-register.md`.
- **Learning hours** where the provider states none: VBA doc 1.5 h, MATLAB Onramp 3 h, MIT 18.05 112 h, SAS Programming 1 21 h, Onshape CAD Basics 7 h, statistics video 8 h.
- **All project hours.** Each is the sum of per-milestone estimates.
- **SDG mappings.** The SDG chosen for each role and skill, and its reason, are our own judgment.
- **Trend rules.** The 15% threshold, which skills get a GitHub topic, and the exclusion of 6 skills.
- **Scenario multipliers** (±10% moderate, ±25% fast). These are Hussain's team assumptions, not forecasts.
