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

## Learning resources (`data/resources.json`)

Each resource's `source_id` equals its `resource_id`. Price, hours and their basis are in `data/resources.json`; see "Learning-resource hours" above.

| source_id | name | url | price status | checked_at | checked_by | used for |
|---|---|---|---|---|---|---|
| mslearn_tsql_query_modify | Microsoft Learn — Query and modify data with Transact-SQL | https://learn.microsoft.com/en-us/training/paths/get-started-querying-with-transact-sql/ | price: no_charge_observed | 2026-10-22 | automated fetch (Claude Code) | skill: sql |
| mslearn_python_part1_fundamentals | Microsoft Learn — Get Started with Python Programming: Part 1 - Fundamentals | https://learn.microsoft.com/en-us/training/paths/get-started-with-python-fundamentals/ | price: no_charge_observed | 2026-10-22 | automated fetch (Claude Code) | skill: python |
| mslearn_power_bi_prepare_visualize | Microsoft Learn — Prepare and visualize data with Microsoft Power BI | https://learn.microsoft.com/en-us/training/paths/prepare-visualize-data-power-bi/ | price: no_charge_observed | 2026-10-22 | automated fetch (Claude Code) | skill: data_visualization |
| mslearn_vba_getting_started_office | Microsoft Learn (official Office VBA documentation) — Getting started with VBA in Office | https://learn.microsoft.com/en-us/office/vba/library-reference/concepts/getting-started-with-vba-in-office | price: no_charge_observed | 2026-10-22 | automated fetch (Claude Code) | skill: vba |
| mathworks_matlab_onramp | MathWorks (MATLAB Academy) — MATLAB Onramp | https://matlabacademy.mathworks.com/details/matlab-onramp/gettingstarted | price: not_stated | 2026-10-22 | automated fetch (Claude Code) | skill: matlab |
| fcc_statistics_video_monika_wahi | freeCodeCamp.org (instructor: Monika Wahi) — Statistics video course by Monika Wahi (freeCodeCamp) | https://expertbeacon.com/learn-college-level-statistics-in-this-free-8-hour-course/ | price: free_stated | 2026-10-22 | Jawad, manually in browser | skill: mathematics |
| mit_ocw_18_05_probability_statistics | MIT OpenCourseWare — 18.05 Introduction to Probability and Statistics (Spring 2022) | https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/ | price: free_stated | 2026-10-22 | automated fetch (Claude Code) | skill: mathematics |
| sas_programming_1_essentials | SAS — SAS Programming 1: Essentials | https://learn.sas.com/course/view.php?id=118 | price: free_stated | 2026-10-22 | automated fetch (Claude Code) | skill: analytical_scientific_software |
| fcc_excel_beginners_full_course | freeCodeCamp.org — Microsoft Excel Tutorial for Beginners - Full Course | https://www.kdnuggets.com/2022/09/free-microsoft-excel-beginners-course.html | price: free_stated | 2026-10-22 | Jawad, manually in browser | skill: excel |
| alison_thinking_critically | Alison — Thinking Critically | https://alison.com/course/thinking-critically | price: free_stated | 2026-10-22 | Jawad, manually in browser | skill: critical_thinking |
| onshape_cad_basics_pathway | Onshape Learning Center — CAD Basics (Learning Pathway) | https://learn.onshape.com/learning-paths/introduction-to-cad | price: free_stated | 2026-10-22 | Jawad, manually in browser | skill: cad_software |

## Scenario assumptions

How our dated GitHub signals feed Hussain's two scenarios (`services/matching/scenarios.py`, read from `origin/feature/hussain-matching` at commit 53de9cc):

1. **Our signal.** For each covered skill, `services/trends` counts new GitHub repositories tagged with that skill's topic in the last 30 days and compares the count with the previous 30 days. A change of more than +15% is `rising`, more than -15% is `falling`, anything else is `stable`, and a failed or incomplete fetch is `unknown`. Every signal has `observed_at` and `retrieved_at`.
2. **What a scenario does with it.** Only `rising` and `falling` signals are used, and each one changes the *weight* of that one skill in the match score:
   - **Moderate AI adoption:** rising skill × 1.10 (+10%), falling skill × 0.90 (-10%).
   - **Fast AI adoption:** rising skill × 1.25 (+25%), falling skill × 0.75 (-25%).
   - `stable` and `unknown` signals change nothing. If one skill gets both a rising and a falling signal, it is left unchanged and a note is added. With no signals at all, the scenario changes nothing and says so.
   - The signal's `source_id` (`github_search_repos`) is added to the role's `evidence_ids`, so the result shows where the change came from.
3. **Today's effect** (first snapshot, retrieved 2026-10-21): python, matlab, excel, vba and cad_software are `rising`; sql, data_visualization and financial_analysis_software are `stable`; nothing is `falling`. The 6 skills without a GitHub topic (critical_thinking, mathematics, complex_problem_solving, systems_analysis, attention_to_detail, analytical_scientific_software) never get a signal, so scenarios never change their weight.

**These percentages are team assumptions, not forecasts.** The ±10% and ±25% values are the team's illustrative choices (see `UNCERTAINTY_NOTE` in `scenarios.py`). They are not research results and do not predict the job market or any student's outcome.

**What the signal measures.** It measures developer activity on GitHub, not job demand. More new repositories about a tool does not mean more job openings that need it.

**Uncertainty this leaves:**
- The link from developer activity to hiring demand is assumed, not measured.
- GitHub topic tags are voluntary, so activity can be undercounted.
- Both 30-day windows are counted on the same day, so older repositories have had longer to be deleted or tagged. This can lean the comparison one way.
- One snapshot is a single comparison, not a trend over time.
- GitHub is global, not specific to Malaysia or any one job market.
- The 15% threshold and the scenario multipliers are team choices, so different choices would give different scores.
- A scenario only re-weights skills inside the `profile_alignment_estimate`. It never turns the score into a hiring probability.
