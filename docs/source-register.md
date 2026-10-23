# Source register

One real, public, dated source per row. `source_id` is referenced from `data/roles.json`.

| source_id | name | url | license / access | observed_at (source's own update date) | retrieved_at (when we checked it) | what it actually tells us | update interval | limits |
|---|---|---|---|---|---|---|---|---|
| onet_15_2051_01 | O*NET OnLine — Business Intelligence Analysts (15-2051.01) | https://www.onetonline.org/link/summary/15-2051.01 | CC BY 4.0, attribution required (U.S. Department of Labor, Employment and Training Administration; see the licence note below) | 2026-10-06 | 2026-10-21 | Typical skills, technology tools, and work activities for this occupation. Python, R and Jupyter Notebook are listed under "Object or component oriented development software" (https://www.onetonline.org/link/tt/15-2051.01/43232405), not marked as Hot Technologies; checked by Jawad in a browser on 2026-10-23. **Not** a live job-vacancy or hiring-demand feed. | O*NET refreshes occupation data periodically (observed multiple times per year) | US-labor-market-centric; describes typical requirements, not a specific employer's requirements |
| onet_13_2051_00 | O*NET OnLine — Financial and Investment Analysts (13-2051.00) | https://www.onetonline.org/link/summary/13-2051.00 | CC BY 4.0, attribution required (U.S. Department of Labor, Employment and Training Administration; see the licence note below) | 2026-10-06 | 2026-10-21 | Technology/software skills (27 categories, fully populated) and work styles for this occupation. **LIMITED:** O*NET's own page states "data collection is currently underway" for this occupation — its Knowledge, Abilities, and Basic/Cross-Functional Skills sections are not yet populated at the source. We only use the populated Technology/Software Skills and Work Styles sections; nothing is invented to fill the gap. Not a hiring-demand feed. | Periodic | **Knowledge, Abilities, and general Skills sections: LIMITED (not yet available at source)**; US-labor-market-centric |
| onet_17_2141_00 | O*NET OnLine — Mechanical Engineers (17-2141.00) | https://www.onetonline.org/link/summary/17-2141.00 | CC BY 4.0, attribution required (U.S. Department of Labor, Employment and Training Administration; see the licence note below) | 2026-10-06 | 2026-10-21 | Typical skills and technology tools for this occupation. Not a hiring-demand feed. | Periodic | US-labor-market-centric |
| onet_19_1041_00 | O*NET OnLine — Epidemiologists (19-1041.00) | https://www.onetonline.org/link/summary/19-1041.00 | CC BY 4.0, attribution required (U.S. Department of Labor, Employment and Training Administration; see the licence note below) | 2026-10-06 | 2026-10-21 | Typical skills and technology tools for this occupation (used as the closest public-health analysis role). Not a hiring-demand feed. | Periodic | US-labor-market-centric |
| onet_15_1252_00 | O*NET OnLine — Software Developers (15-1252.00) | https://www.onetonline.org/link/summary/15-1252.00 | CC BY 4.0, attribution required (U.S. Department of Labor, Employment and Training Administration; see the licence note below) | 2026-10-06 | 2026-10-22 | Typical skills (with 0-100 importance) and technology tools for this occupation. Tools come from O*NET's full Software Skills CSV export (https://www.onetonline.org/link/table/details/tc/15-1252.00/Software_Skills_15-1252-00.csv?fmt=csv), because the on-page list is truncated. Not a hiring-demand feed. | Periodic | US-labor-market-centric; Hot Technology flags are not in the CSV export |
| onet_13_2011_00 | O*NET OnLine — Accountants and Auditors (13-2011.00) | https://www.onetonline.org/link/summary/13-2011.00 | CC BY 4.0, attribution required (U.S. Department of Labor, Employment and Training Administration; see the licence note below) | 2026-10-06 | 2026-10-22 | Typical skills, work styles (Attention to Detail 100) and technology tools; one occupation covering both accountants and auditors. Not a hiring-demand feed. | Periodic | US-labor-market-centric; does not separate accountant from auditor |
| onet_17_2051_00 | O*NET OnLine — Civil Engineers (17-2051.00) | https://www.onetonline.org/link/summary/17-2051.00 | CC BY 4.0, attribution required (U.S. Department of Labor, Employment and Training Administration; see the licence note below) | 2026-10-06 | 2026-10-22 | Typical skills (with 0-100 importance) and technology tools for this occupation. Not a hiring-demand feed. | Periodic | US-labor-market-centric |
| onet_19_2041_00 | O*NET OnLine — Environmental Scientists and Specialists, Including Health (19-2041.00) | https://www.onetonline.org/link/summary/19-2041.00 | CC BY 4.0, attribution required (U.S. Department of Labor, Employment and Training Administration; see the licence note below) | 2026-10-06 | 2026-10-22 | Typical skills (with 0-100 importance) and technology tools for this occupation. Not a hiring-demand feed. | Periodic | US-labor-market-centric; lists no Python or R |
| github_search_repos | GitHub REST API — Search Repositories (`topic:<x> created:<start>..<end>`) | https://docs.github.com/en/rest/search/search#search-repositories | Public API; GitHub Terms of Service apply (documented, rate-limited automated use is permitted); free, optional personal access token via `services/trends/.env` (never committed) | continuous/live (a query against the current state of GitHub, not a fixed-date publication) | 2026-10-21 (first integration) | Count of NEW repositories created in a rolling 30-day window and tagged with a specific topic, compared to the prior 30-day window. **Developer/tech-ecosystem activity signal. NOT a hiring-demand measure.** | On demand per refresh; unauthenticated ~10 req/min, ~30 req/min with a token | Only 12 of 20 catalogue skills have a clear, verified GitHub topic (see `services/trends/README.md` for the full coverage table and the 8 explicitly excluded skills); topic tagging is voluntary so true activity can be undercounted; a count GitHub itself flags `incomplete_results: true` is treated as `unknown`, never trusted |

## Notes
- **O*NET licence.** O*NET OnLine pages are not public domain. Each page footer says, for example: "15-2051.01 - Business Intelligence Analysts by U.S. Department of Labor, Employment and Training Administration is licensed under a Creative Commons Attribution 4.0 International License" (linking to https://creativecommons.org/licenses/by/4.0/; read on 2026-10-23 from https://www.onetonline.org/link/summary/15-2051.01). So we credit O*NET and the U.S. Department of Labor, Employment and Training Administration wherever O*NET-derived data is shown.
- **Attribution line** (use wherever O*NET-derived data is shown): "Source: O*NET OnLine by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA), licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)."
- **Data Analyst mapping.** Our role `data_analyst` is mapped to O*NET 15-2051.01, "Business Intelligence Analysts" (the exact title on https://www.onetonline.org/link/summary/15-2051.01, checked in a browser by Jawad on 2026-10-23). Python is listed under this occupation's Technology Skills. The Python importance of 3 and `required: true` on `data_analyst` are a **team estimate**, not an official O*NET importance score.
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
| software_developer | programming | 75 | 5 | 5 | derived |
| software_developer | critical_thinking | 72 | 5 | 5 | derived |
| software_developer | systems_analysis | 63 | 4 | 4 | derived |
| software_developer | complex_problem_solving | 60 | 4 | 4 | derived |
| software_developer | mathematics | 44 | 2 | 2 | derived (optional: team estimate) |
| accountant | attention_to_detail | 100 (Work Style importance) | 5 | 5 | derived |
| accountant | critical_thinking | 63 | 4 | 4 | derived |
| accountant | complex_problem_solving | 63 | 4 | 4 | derived |
| accountant | mathematics | 60 | 4 | 4 | derived |
| civil_engineer | mathematics | 72 | 5 | 5 | derived |
| civil_engineer | critical_thinking | 72 | 5 | 5 | derived |
| civil_engineer | complex_problem_solving | 72 | 5 | 5 | derived |
| civil_engineer | systems_analysis | 69 | 4 | 4 | derived |
| civil_engineer | science | 69 | 4 | 4 | derived |
| environmental_scientist | science | 75 | 5 | 5 | derived |
| environmental_scientist | complex_problem_solving | 75 | 5 | 5 | derived |
| environmental_scientist | critical_thinking | 72 | 5 | 5 | derived |
| environmental_scientist | mathematics | 56 | 3 | 3 | derived |
| environmental_scientist | systems_analysis | 50 | 3 | 3 | derived |

Source for each number: the occupation's own O*NET Details page (`https://www.onetonline.org/link/details/<code>`), retrieved 2026-10-21 for the first 4 roles and 2026-10-22 for the last 4. For the 4 newer roles, the scores were read directly from the page HTML (the `Importance` cell of each skill row), not from an AI summary, and every value follows the bucket rule exactly.

**2. Technology/tool skills (excel, sql, python, data_visualization, cad_software, matlab, financial_analysis_software, analytical_scientific_software, vba, javascript, git, accounting_software, gis).**
O*NET does **not** publish a 0-100 importance number for individual technology/software skills — only whether a tool appears in the occupation's Technology Skills list, and sometimes a "Hot Technology" / "In Demand" badge. Our retrieval (an AI-summarized read of the rendered page) returned that badge inconsistently across repeated fetches for the same tool, so **every tool-skill importance number in `data/roles.json` is a team estimate**, informed by (a) whether the tool is confirmed present at all for that occupation [verified — see `data/skills.json` `source_ids`], and (b) the team's judgment of how central that tool is to the role. None should be read as an O*NET-derived score. Example: `python` on `data_analyst` (importance 3, required) is a team estimate on the same basis as `sql`: both are listed in the occupation's Technology Skills, and neither is a Hot Technology.

**3. The `required: true/false` flag itself.** O*NET has no "required vs optional" field — this split is our own product design choice (to keep each role's core list short). It is a **team estimate** for every skill in every role.

## Close-but-different skill pairs (`data/skill_not_equivalent.json`)

Hussain's matcher uses these pairs to give a similarity of 0, so one skill never earns credit for the other. They are team judgments, based on what each skill means. Their similarity scores were **not** measured by us. `programming`/`python` and `programming`/`javascript` are deliberately **not** listed, because a Python or JavaScript skill is a kind of programming.

| pair | why they are different |
|---|---|
| python / javascript | Two different programming languages |
| python / matlab | Both used for scientific computing, but different languages and tools |
| excel / vba | VBA is Excel's macro language; using Excel is not the same as writing VBA |
| excel / accounting_software | A spreadsheet is not a bookkeeping package |
| accounting_software / financial_analysis_software | Bookkeeping tools vs financial analysis and planning tools |
| critical_thinking / complex_problem_solving | Two separate O*NET skills with separate importance scores |
| complex_problem_solving / systems_analysis | Two separate O*NET skills |
| mathematics / science | Two separate O*NET skills |
| git / programming | Version control is not writing code |
| cad_software / gis | Drawing parts and buildings vs mapping places |
| data_visualization / gis | Charts and dashboards vs maps |
| matlab / analytical_scientific_software | MATLAB vs statistics packages (SPSS, SAS, Stata) |

## Learning-resource hours (`data/resources.json` and roadmap steps)

Every roadmap step has a numeric `estimated_hours` (Rehan's `RoadmapStep` requires a number >= 0) and an `hours_basis` label saying where the number came from:

| `hours_basis` | meaning | where it comes from |
|---|---|---|
| `provider_stated` | The provider's own published duration. | `resources.json` → `estimated_hours` (with `hours_source` quoting it). Currently the 3 Microsoft Learn paths and the Microsoft Learn *Introduction to Git* module (`duration_in_minutes` in Microsoft Learn's official catalog API), the two freeCodeCamp YouTube videos (Excel 2:26:09 and statistics 8:15:04, video length shown on YouTube) and Alison "Thinking Critically" (upper end of its stated 1.5-3 h). |
| `team_estimate` | The provider states **no** duration, so the team estimated one. **Not** a provider figure. | `resources.json` → `team_estimate_hours`, with `team_estimate_basis` showing the arithmetic from facts on the page. |

Current team estimates (checked 2026-10-22):

| resource | team estimate | basis |
|---|---|---|
| Microsoft Learn — Getting started with VBA in Office | 1.5 h | 5,106-word article (page metadata) at ~200 words/min ≈ 0.5 h + ~1 h trying the examples |
| MathWorks — MATLAB Onramp | 3 h | 35 short lessons in 14 modules (counted on the page) × ~5 min |
| MIT OCW — 18.05 Probability and Statistics | 112 h | Full one-semester course with weekly problem sets; assumed ~8 h/week × ~14 weeks |
| SAS — SAS Programming 1: Essentials | 21 h | SAS says "a complete how-to in two days" and lists 21 h for the live-class format; assumed similar for self-paced |
| Onshape — CAD Basics (Learning Pathway) | 7 h | 7 listed topics at about 1 h each; Onshape publishes no duration |
| MDN — Dynamic scripting with JavaScript | 23 h | 23 lesson and challenge pages in the module × ~1 h |
| Harvard — CS50x 2026 | 110 h | 11 weeks of material (Week 0–10, checked by Jawad in a browser on 2026-10-22) × ~10 h/week. CS50x states no hours, so 110 h stays a team estimate |
| GnuCash — Tutorial and Concepts Guide | 12 h | 16 chapters × ~45 min |
| QGIS — Training Manual | 14 h | Core modules 2–8 (7 modules) × ~2 h |

`checked_by` in `data/resources.json` records how each page was verified: `automated fetch (Claude Code)` or `Jawad, manually in browser` (used for pages that block automated requests or need a sign-in). When a skill has more than one resource, `rank` (lower = preferred) decides which one `get_roadmap` uses; mathematics uses the freeCodeCamp statistics video (rank 1) and keeps MIT 18.05 as rank 2.

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
| uci_concrete_compressive_strength | UCI ML Repository — Concrete Compressive Strength | https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength | CC BY 4.0 | 2026-10-22 | ce_concrete_strength_model | 1,030 rows; ingredients in kg/m^3 and age in days; licence CC BY 4.0 checked manually by Jawad in a browser on 2026-10-22 |
| uci_beijing_multi_site_air_quality | UCI ML Repository — Beijing Multi-Site Air Quality | https://archive.ics.uci.edu/dataset/501/beijing+multi+site+air+quality+data | CC BY 4.0 ("This dataset is licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) license."); no other use restriction on the page | 2026-10-22 | es_beijing_air_quality_trends | 420,768 hourly rows from 12 sites, 2013-03-01 to 2017-02-28; data from the Beijing Municipal Environmental Monitoring Center; creator Song Chen; DOI 10.24432/C5RK5G; missing data marked NA |

Tutorial sources reused from the learning-resources table: `gnucash_tutorial_concepts_guide` (ac_gnucash_small_business_books) and `qgis_training_manual` (ce_qgis_site_analysis, es_qgis_forestry_mapping); both are `source_type: tutorial`. They are linked, not copied. Licence as seen on 2026-10-22: the GnuCash guide's contents list a "GNU Free Documentation License" appendix; the QGIS Training Manual page footer says only "© Copyright 2002-now, QGIS project" and names no licence (checked by Jawad in a browser on 2026-10-22). Licence: not stated on the page; we link only and do not copy the manual.

Checked and **not used**: UCI Air Quality (https://archive.ics.uci.edu/dataset/360/air+quality; labelled CC BY 4.0, but its description says "This dataset can be used exclusively for research purposes. Commercial purposes are fully excluded.", which does not fit a public Apache-2.0 repo), Natural Earth (returned 406 to automated checks, licence not read), SEC Financial Statement Data Sets (page returned 403 to automated checks), Our World in Data COVID-19 repository (archived; licence file not found), WHO Global Health Observatory (no licence text found on the page).

## Learning resources (`data/resources.json`)

Each resource's `source_id` equals its `resource_id`. Price, hours and their basis are in `data/resources.json`; see "Learning-resource hours" above.

| source_id | name | url | price status | checked_at | checked_by | used for |
|---|---|---|---|---|---|---|
| mslearn_tsql_query_modify | Microsoft Learn — Query and modify data with Transact-SQL | https://learn.microsoft.com/en-us/training/paths/get-started-querying-with-transact-sql/ | price: no_charge_observed | 2026-10-22 | automated fetch (Claude Code) | skill: sql |
| mslearn_python_part1_fundamentals | Microsoft Learn — Get Started with Python Programming: Part 1 - Fundamentals | https://learn.microsoft.com/en-us/training/paths/get-started-with-python-fundamentals/ | price: no_charge_observed | 2026-10-22 | automated fetch (Claude Code) | skill: python |
| mslearn_power_bi_prepare_visualize | Microsoft Learn — Prepare and visualize data with Microsoft Power BI | https://learn.microsoft.com/en-us/training/paths/prepare-visualize-data-power-bi/ | price: no_charge_observed | 2026-10-22 | automated fetch (Claude Code) | skill: data_visualization |
| mslearn_vba_getting_started_office | Microsoft Learn (official Office VBA documentation) — Getting started with VBA in Office | https://learn.microsoft.com/en-us/office/vba/library-reference/concepts/getting-started-with-vba-in-office | price: no_charge_observed | 2026-10-22 | automated fetch (Claude Code) | skill: vba |
| mathworks_matlab_onramp | MathWorks (MATLAB Academy) — MATLAB Onramp | https://matlabacademy.mathworks.com/details/matlab-onramp/gettingstarted | price: not_stated | 2026-10-22 | automated fetch (Claude Code) | skill: matlab |
| fcc_statistics_video_monika_wahi | freeCodeCamp.org (YouTube) — Statistics - A Full University Course on Data Science Basics | https://youtu.be/xxpc-HPKN28 | price: free_stated | 2026-10-22 | Jawad, manually in browser | skill: mathematics. Instructor: Monika Wahi, confirmed in the YouTube description ("Course by Monika Wahi") by Jawad in a browser on 2026-10-22 |
| mit_ocw_18_05_probability_statistics | MIT OpenCourseWare — 18.05 Introduction to Probability and Statistics (Spring 2022) | https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/ | price: free_stated | 2026-10-22 | automated fetch (Claude Code) | skill: mathematics |
| sas_programming_1_essentials | SAS — SAS Programming 1: Essentials | https://learn.sas.com/course/view.php?id=118 | price: free_stated | 2026-10-22 | automated fetch (Claude Code) | skill: analytical_scientific_software |
| fcc_excel_beginners_full_course | freeCodeCamp.org (YouTube) — Microsoft Excel Tutorial for Beginners - Full Course | https://youtu.be/Vl0H-qTclOg | price: free_stated | 2026-10-22 | Jawad, manually in browser | skill: excel |
| alison_thinking_critically | Alison — Thinking Critically | https://alison.com/course/thinking-critically | price: free_stated | 2026-10-22 | Jawad, manually in browser | skill: critical_thinking |
| onshape_cad_basics_pathway | Onshape Learning Center — CAD Basics (Learning Pathway) | https://learn.onshape.com/learning-paths/introduction-to-cad | price: free_stated | 2026-10-22 | Jawad, manually in browser | skill: cad_software |
| mslearn_intro_to_git | Microsoft Learn — Introduction to Git | https://learn.microsoft.com/en-us/training/modules/intro-to-git/ | price: no_charge_observed | 2026-10-22 | Jawad, manually in browser | skill: git |
| mdn_javascript_dynamic_scripting | MDN Web Docs (Mozilla) — Dynamic scripting with JavaScript (Learn web development) | https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Scripting | price: no_charge_observed | 2026-10-22 | Jawad, manually in browser | skill: javascript |
| cs50x_2026 | Harvard University (CS50 OpenCourseWare) — CS50x 2026 (CS50's Introduction to Computer Science) | https://cs50.harvard.edu/x/ | price: free_stated | 2026-10-22 | Jawad, manually in browser | skill: programming. Licence: CC BY-NC-SA 4.0, read from https://cs50.harvard.edu/x/license/ manually by Jawad in a browser on 2026-10-22; we link only and do not copy or redistribute the material |
| gnucash_tutorial_concepts_guide | GnuCash (official documentation) — GnuCash Tutorial and Concepts Guide | https://www.gnucash.org/viewdoc.phtml?rev=5&lang=C&doc=guide | price: free_stated | 2026-10-22 | Jawad, manually in browser | skill: accounting_software |
| qgis_training_manual | QGIS (official documentation) — QGIS Training Manual | https://docs.qgis.org/latest/en/docs/training_manual/ | price: free_stated | 2026-10-22 | Jawad, manually in browser | skill: gis. Licence: not stated on the page (footer says only "© Copyright 2002-now, QGIS project"; checked by Jawad 2026-10-22); we link only |

## Scenario assumptions

How our dated GitHub signals feed Hussain's two scenarios (`services/matching/scenarios.py`, read from `origin/feature/hussain-matching` at commit 53de9cc):

1. **Our signal.** For each covered skill, `services/trends` counts new GitHub repositories tagged with that skill's topic in the last 30 days and compares the count with the previous 30 days. A change of more than +15% is `rising`, more than -15% is `falling`, anything else is `stable`, and a failed or incomplete fetch is `unknown`. Every signal has `observed_at` and `retrieved_at`.
2. **What a scenario does with it.** Only `rising` and `falling` signals are used, and each one changes the *weight* of that one skill in the match score:
   - **Moderate AI adoption:** rising skill × 1.10 (+10%), falling skill × 0.90 (-10%).
   - **Fast AI adoption:** rising skill × 1.25 (+25%), falling skill × 0.75 (-25%).
   - `stable` and `unknown` signals change nothing. If one skill gets both a rising and a falling signal, it is left unchanged and a note is added. With no signals at all, the scenario changes nothing and says so.
   - The signal's `source_id` (`github_search_repos`) is added to the role's `evidence_ids`, so the result shows where the change came from.
3. **Today's effect** (snapshots retrieved 2026-10-21 for the first 8 covered skills, 2026-10-22 for the 4 added later): python, matlab, excel, vba, cad_software, javascript, git, accounting_software and gis are `rising`; sql, data_visualization and financial_analysis_software are `stable`; nothing is `falling`. git only just crosses the threshold (+15.9%). The 8 skills without a GitHub topic (critical_thinking, mathematics, complex_problem_solving, systems_analysis, attention_to_detail, analytical_scientific_software, programming, science) never get a signal, so scenarios never change their weight.

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
