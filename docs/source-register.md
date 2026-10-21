# Source register

One real, public, dated source per row. `source_id` is referenced from `data/roles.json`.

| source_id | name | url | license / access | observed_at (source's own update date) | retrieved_at (when we checked it) | what it actually tells us | update interval | limits |
|---|---|---|---|---|---|---|---|---|
| onet_15_2051_01 | O*NET OnLine — Business Intelligence Analysts (15-2051.01) | https://www.onetonline.org/link/summary/15-2051.01 | Public domain (US Dept. of Labor, O*NET data free to use with attribution) | 2026-10-06 | 2026-10-21 | Typical skills, technology tools, and work activities for this occupation. **Not** a live job-vacancy or hiring-demand feed. | O*NET refreshes occupation data periodically (observed multiple times per year) | US-labor-market-centric; describes typical requirements, not a specific employer's requirements |
| onet_13_2051_00 | O*NET OnLine — Financial and Investment Analysts (13-2051.00) | https://www.onetonline.org/link/summary/13-2051.00 | Public domain (US Dept. of Labor, O*NET) | 2026-10-06 | 2026-10-21 | Technology/software skills and work styles for this occupation. **Note:** O*NET's own page states Basic/Cross-Functional Skills data collection for this occupation is "currently underway" — that section is not yet populated at the source, so we only use its Software Skills and Work Styles sections. Not a hiring-demand feed. | Periodic | Skills section incomplete at source (disclosed above); US-labor-market-centric |
| onet_17_2141_00 | O*NET OnLine — Mechanical Engineers (17-2141.00) | https://www.onetonline.org/link/summary/17-2141.00 | Public domain (US Dept. of Labor, O*NET) | 2026-10-06 | 2026-10-21 | Typical skills and technology tools for this occupation. Not a hiring-demand feed. | Periodic | US-labor-market-centric |
| onet_19_1041_00 | O*NET OnLine — Epidemiologists (19-1041.00) | https://www.onetonline.org/link/summary/19-1041.00 | Public domain (US Dept. of Labor, O*NET) | 2026-10-06 | 2026-10-21 | Typical skills and technology tools for this occupation (used as the closest public-health analysis role). Not a hiring-demand feed. | Periodic | US-labor-market-centric |

## Notes
- All four sources are **occupation/skill-requirement descriptions**, not live job-posting or vacancy-demand data. They answer "what skills does this job typically need," not "how many jobs are open right now."
- "observed_at" = the date O*NET's own page says it was last updated. "retrieved_at" = the date we looked at the page (today).
- A real **updatable trend feed** (job-posting counts, research signals, etc.) is a separate, later task — not covered by this table.
