# Source register

One real, public, dated source per row. `source_id` is referenced from `data/roles.json`.

| source_id | name | url | license / access | observed_at (source's own update date) | retrieved_at (when we checked it) | what it actually tells us | update interval | limits |
|---|---|---|---|---|---|---|---|---|
| onet_15_2051_01 | O*NET OnLine — Business Intelligence Analysts (15-2051.01) | https://www.onetonline.org/link/summary/15-2051.01 | Public domain (US Dept. of Labor, O*NET data free to use with attribution) | 2026-10-06 | 2026-10-21 | Typical skills, technology tools, and work activities for this occupation. **Not** a live job-vacancy or hiring-demand feed. | O*NET refreshes occupation data periodically (observed multiple times per year) | US-labor-market-centric; describes typical requirements, not a specific employer's requirements |
| onet_13_2051_00 | O*NET OnLine — Financial and Investment Analysts (13-2051.00) | https://www.onetonline.org/link/summary/13-2051.00 | Public domain (US Dept. of Labor, O*NET) | 2026-10-06 | 2026-10-21 | Technology/software skills (27 categories, fully populated) and work styles for this occupation. **LIMITED:** O*NET's own page states "data collection is currently underway" for this occupation — its Knowledge, Abilities, and Basic/Cross-Functional Skills sections are not yet populated at the source. We only use the populated Technology/Software Skills and Work Styles sections; nothing is invented to fill the gap. Not a hiring-demand feed. | Periodic | **Knowledge, Abilities, and general Skills sections: LIMITED (not yet available at source)**; US-labor-market-centric |
| onet_17_2141_00 | O*NET OnLine — Mechanical Engineers (17-2141.00) | https://www.onetonline.org/link/summary/17-2141.00 | Public domain (US Dept. of Labor, O*NET) | 2026-10-06 | 2026-10-21 | Typical skills and technology tools for this occupation. Not a hiring-demand feed. | Periodic | US-labor-market-centric |
| onet_19_1041_00 | O*NET OnLine — Epidemiologists (19-1041.00) | https://www.onetonline.org/link/summary/19-1041.00 | Public domain (US Dept. of Labor, O*NET) | 2026-10-06 | 2026-10-21 | Typical skills and technology tools for this occupation (used as the closest public-health analysis role). Not a hiring-demand feed. | Periodic | US-labor-market-centric |
| github_search_repos | GitHub REST API — Search Repositories (`topic:<x> created:<start>..<end>`) | https://docs.github.com/en/rest/search/search#search-repositories | Public API; GitHub Terms of Service apply (documented, rate-limited automated use is permitted); free, optional personal access token via `services/trends/.env` (never committed) | continuous/live (a query against the current state of GitHub, not a fixed-date publication) | 2026-10-21 (first integration) | Count of NEW repositories created in a rolling 30-day window and tagged with a specific topic, compared to the prior 30-day window. **Developer/tech-ecosystem activity signal. NOT a hiring-demand measure.** | On demand per refresh; unauthenticated ~10 req/min, ~30 req/min with a token | Only 8 of 14 catalogue skills have a clear, verified GitHub topic (see `services/trends/README.md` for the full coverage table and the 6 explicitly excluded skills); topic tagging is voluntary so true activity can be undercounted; a count GitHub itself flags `incomplete_results: true` is treated as `unknown`, never trusted |

## Notes
- All four sources are **occupation/skill-requirement descriptions**, not live job-posting or vacancy-demand data. They answer "what skills does this job typically need," not "how many jobs are open right now."
- "observed_at" = the date O*NET's own page says it was last updated. "retrieved_at" = the date we looked at the page (today).
- A real **updatable trend feed** (job-posting counts, research signals, etc.) is a separate, later task — not covered by this table.
- `data_mode` for this catalog is **`cached`**, not `live`: it's a one-time retrieved snapshot (2026-10-21), not an automatically-refreshing feed. Contract enum (`contracts/API_CONTRACT.md`): `live | cached | fixture`.

## Importance score methodology (the 1-5 numbers in `data/roles.json`)

`required_skills[].importance` is a 1-5 number (Hussain's matcher scale). Two different kinds of skill get it two different ways:

**1. Cognitive skills (critical_thinking, mathematics, complex_problem_solving, systems_analysis, attention_to_detail).**
O*NET publishes a real 0-100 "Importance" score per skill/work-style, per occupation (its Details report, not the Summary report). We bucket that score: **≥70 → 5, 60-69 → 4, 50-59 → 3, 40-49 → 2, <40 → 1.** Where our roles.json number matches the bucket, it's **derived**. Where it doesn't, it's a **team estimate** with a stated reason.

| role | skill | O*NET importance (0-100) | bucket value | roles.json value | basis |
|---|---|---|---|---|---|
| data_analyst | critical_thinking | 72 | 5 | 5 | derived |
| data_analyst | mathematics | 63 | 4 | 5 | **team estimate** — we weight quantitative ability higher for a data role than O*NET's general score |
| data_analyst | complex_problem_solving | 60 | 4 | 4 | derived |
| data_analyst | systems_analysis | 53 | 3 | 3 | derived |
| mechanical_engineer | critical_thinking | 72 | 5 | 5 | derived |
| mechanical_engineer | mathematics | 69 | 4 | 5 | **team estimate** — core to engineering calculation work, weighted above O*NET's score |
| mechanical_engineer | complex_problem_solving | 69 | 4 | 5 | **team estimate** — central to engineering design, weighted above O*NET's score |
| public_health_analyst | critical_thinking | 81 | 5 | 5 | derived |
| public_health_analyst | mathematics | 69 | 4 | 5 | **team estimate** — same reasoning as above |
| financial_analyst | attention_to_detail | 100 (Work Style importance) | 5 | 5 | derived |

Source for each number: the occupation's own O*NET Details page (`https://www.onetonline.org/link/details/<code>`), retrieved 2026-10-21.

**2. Technology/tool skills (excel, sql, python, data_visualization, cad_software, matlab, financial_analysis_software, analytical_scientific_software, vba).**
O*NET does **not** publish a 0-100 importance number for individual technology/software skills — only whether a tool appears in the occupation's Technology Skills list, and sometimes a "Hot Technology" / "In Demand" badge. Our retrieval (an AI-summarized read of the rendered page) returned that badge inconsistently across repeated fetches for the same tool, so **every tool-skill importance number in `data/roles.json` is a team estimate**, informed by (a) whether the tool is confirmed present at all for that occupation [verified — see `data/skills.json` `source_ids`], and (b) the team's judgment of how central that tool is to the role. None should be read as an O*NET-derived score.

**3. The `required: true/false` flag itself.** O*NET has no "required vs optional" field — this split is our own product design choice (to keep each role's core list short). It is a **team estimate** for every skill in every role.

## Learning-resource hours (`data/resources.json` and roadmap steps)

Every roadmap step has a numeric `estimated_hours` (Rehan's `RoadmapStep` requires a number >= 0) and an `hours_basis` label saying where the number came from:

| `hours_basis` | meaning | where it comes from |
|---|---|---|
| `provider_stated` | The provider's own published duration. | `resources.json` → `estimated_hours` (with `hours_source` quoting it). Currently the 3 Microsoft Learn paths (`duration_in_minutes` in Microsoft Learn's official catalog API), the freeCodeCamp Excel video (2:26:10 on the player) and Alison "Thinking Critically" (upper end of its stated 1.5-3 h). |
| `team_estimate` | The provider states **no** duration, so the team estimated one. **Not** a provider figure. | `resources.json` → `team_estimate_hours`, with `team_estimate_basis` showing the arithmetic from facts on the page. |

Current team estimates (checked 2026-10-22):

| resource | team estimate | basis |
|---|---|---|
| Microsoft Learn — Getting started with VBA in Office | 1.5 h | 5,106-word article (page metadata) at ~200 words/min ≈ 0.5 h + ~1 h trying the examples |
| MathWorks — MATLAB Onramp | 3 h | 35 short lessons in 14 modules (counted on the page) × ~5 min |
| MIT OCW — 18.05 Probability and Statistics | 112 h | Full one-semester course with weekly problem sets; assumed ~8 h/week × ~14 weeks |
| SAS — SAS Programming 1: Essentials | 21 h | SAS says "a complete how-to in two days" and lists 21 h for the live-class format; assumed similar for self-paced |
| Onshape — CAD Basics (Learning Pathway) | 7 h | 7 listed topics at about 1 h each; Onshape publishes no duration |
| freeCodeCamp — statistics video by Monika Wahi | 8 h | Only a third-party article (expertbeacon.com, updated 2024-08-20) calls it an "8-hour course"; the video page itself has not been seen |

`checked_by` in `data/resources.json` records how each page was verified: `automated fetch (Claude Code)` or `Jawad, manually in browser` (used for pages that block automated requests or need a sign-in). When a skill has more than one resource, `rank` (lower = preferred) decides which one `get_roadmap` uses; mathematics uses the statistics video (rank 1) and keeps MIT 18.05 as rank 2.

Rules: a resource has either `estimated_hours` (provider) or `team_estimate_hours` (team), never both. `total_estimated_hours` includes both kinds, and the roadmap's warnings name every step that uses a team estimate.

## Project datasets and tutorials (`data/projects.json`)

Each page was opened on `checked_at` and its licence read from the page itself. Datasets are **linked, never copied** into the app.

| source_id | name | url | licence (as stated on the page) | checked_at | used by | notes |
|---|---|---|---|---|---|---|
| uci_online_retail_ii | UCI ML Repository — Online Retail II | https://archive.ics.uci.edu/dataset/502/online+retail+ii | CC BY 4.0 | 2026-10-22 | da_online_retail_dashboard | Transaction data with anonymised customer IDs |
| uci_bank_marketing | UCI ML Repository — Bank Marketing | https://archive.ics.uci.edu/dataset/222/bank+marketing | CC BY 4.0 | 2026-10-22 | da_bank_campaign_analysis | |
| uci_default_credit_card | UCI ML Repository — Default of Credit Card Clients | https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients | CC BY 4.0 | 2026-10-22 | fa_credit_default_analysis | 30,000 rows, 23 features. Includes sex, marital status and age; the project excludes them from its risk score |
| worldbank_wdi | World Bank — World Development Indicators | https://datacatalog.worldbank.org/search/dataset/0037712/World-Development-Indicators | Creative Commons Attribution 4.0 | 2026-10-22 | fa_macro_indicator_workbook, ph_health_indicator_trends | Catalog page shows dateModified 2026-10-12 |
| uci_ai4i_2020 | UCI ML Repository — AI4I 2020 Predictive Maintenance Dataset | https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset | CC BY 4.0 | 2026-10-22 | me_predictive_maintenance | |
| uci_ccpp | UCI ML Repository — Combined Cycle Power Plant | https://archive.ics.uci.edu/dataset/294/combined+cycle+power+plant | CC BY 4.0 | 2026-10-22 | me_power_plant_regression | |
| onshape_cad_basics | Onshape Learning Center — CAD Basics (Learning Pathway) | https://learn.onshape.com/learning-paths/introduction-to-cad | Onshape terms of use (tutorial, not a dataset) | 2026-10-22 | me_parametric_bracket_cad | `source_type: tutorial`; free sign-in required; checked manually by Jawad in a browser |
| uci_diabetes_130 | UCI ML Repository — Diabetes 130-US Hospitals for Years 1999-2008 | https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008 | CC BY 4.0 | 2026-10-22 | ph_diabetes_readmission | **De-identified, public patient records. No part of the dataset is included in this app**; the project only links to the UCI page |

Checked and **not used**: SEC Financial Statement Data Sets (page returned 403 to automated checks), Our World in Data COVID-19 repository (archived; licence file not found), WHO Global Health Observatory (no licence text found on the page).
