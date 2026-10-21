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
