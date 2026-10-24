# Demo talking points — Jawad

**These are draft presenter notes to support recording the demo video, not the final submitted script or the video itself.** Re-check every "app" claim against whatever is actually live at recording time before saying it on camera.

## Data-section narration (30-45 seconds, about 100 words)

Say this out loud. Every app claim here was checked on the deployed app (https://mustaqbal-ai.replit.app) on 2026-10-24 at 19:50 UTC (2026-10-25 03:50 MYT) with GET requests, plus one earlier POST test with invented profiles (19:43 UTC). **Still re-check at recording time** — this was one check, not a continuous guarantee.

> "My part is the data behind Mustaqbal AI.
> The app has 30 career roles and 20 skills, from a real occupational dataset.
> Every role and every skill links to a UN Sustainable Development Goal, with a reason you can read.
> Some roles say 'limited skills coverage', because our 20 skills can't measure everything they need.
> The trend section shows our saved GitHub snapshots from 21 and 22 October, labelled cached, not live.
> That's developer activity, not job demand.
> And the score is an alignment estimate, not a hiring chance."

**What each sentence rests on:**
- **30 roles, 20 skills:** on 2026-10-24 at 19:50 UTC, `GET /api/v1/sdgs/{role_id}` returned role SDG mappings for all 30 role IDs. The one POST match test returned `catalog_coverage` 30 of 30, which the Roles page shows as "30 of 30 roles verified". The app lists at most 6 roles per profile. The 20 skills in the form are the same as `data/skills.json`. "Real occupational dataset" is the app's own note; the roles come from O*NET (CC BY 4.0, see the attribution line in `docs/prd-inputs-jawad.md`).
- **SDGs, "cached" label:** `GET /api/v1/sdgs/{role_id}` returns `data_mode: "cached"` with one reason per role and per skill.
- **Limited coverage:** the app adds this caveat to financial_analyst, financial_risk_specialist, information_security_analyst, logistician and public_health_analyst.
- **Trends are "cached":** `GET /api/v1/trends` returns `data_mode: "cached"`, `source_status: "stale"` and 12 signals that equal our 12 snapshots (observed 2026-10-21 and 2026-10-22). 8 of our 20 skills have no trend signal.
- **Alignment estimate:** every match has `score_type: "profile_alignment_estimate"`.
- **"Demo data" badge:** the match, roadmap and project screens currently show a "Demo data" badge, because those responses carry `data_mode: "fixture"`. The label is being fixed. Their real source is our cached data. Don't call it demo, fixture or live data.
- **Resources and projects:** in our data (16 resources; 17 projects, only for the first 8 roles), each with a dated, registered source. Not in the narration, because the app does not show the source register.

---

## Longer version (about 2.5 minutes)

**Two kinds of numbers. Say which one you show:**
- **App:** what the deployed API returned to a GET request (checked; `generated_at` 2026-10-22T18:34Z UTC).
- **Standalone:** output of my Python services (`services/catalog`, `services/sdg`, `services/trends`, `services/roadmaps`), run in the terminal on the data in branch `feat/jawad-30-roles`. It is **not confirmed in the app**.
  - The app's roadmap and project endpoints are POST, and we sent no POST request, so app hours may differ.
  - The standalone trend output uses only the 12 saved (cached) snapshots, with no live GitHub request.

**1. The roles (about 20 s): Standalone**
*[Terminal: list the 30 roles.]*
- "Our data has 30 career roles in 4 industry groups: 9 in Technology and AI, 8 in Business and Finance, 7 in Engineering and 6 in Healthcare and Sustainability."
- "Each role comes from a real occupation in O*NET, the US Department of Labor's job database."
- "We didn't invent any roles or skills. All 30 roles are in the deployed app, which showed them when we checked on 24 October 2026 (UTC)."

**2. One role's skills (about 25 s): Standalone**
*[Terminal: Data Analyst skills with importance.]*
- "Here's the Data Analyst. Each skill has an importance from 1 to 5."
- "Critical thinking is 5. O*NET scores it 72 out of 100, and we turn that into 1 to 5."
- "Some numbers are our own estimate, and we say so. O*NET gives mathematics 63, which would be a 4. We raised it to 5 for a data role."
- "For tools like SQL and Excel, O*NET doesn't give an importance score. So those numbers are team estimates."

**3. Trend signal (about 30 s): App first, then Standalone**
*[App: `GET /api/v1/trends`. Show `data_mode: "cached"`, `source_status: "stale"` and the dates.]*
- "In the app, the trend section shows our 12 saved GitHub snapshots. It says cached, not live. 8 of our 20 skills have no trend signal."

*[Terminal (standalone): Data Analyst trend output, with status "cached" and the date.]*
- "Here is the same data from our own service."
- "It counts new GitHub projects for each skill, comparing the last 30 days with the 30 days before."
- "For Excel, it's rising. For SQL, it's stable: 3,531 new projects, up from 3,273."
- "The status says cached, last refreshed 21 October 2026. It's saved data, not live."
- "And to be clear: this is developer activity, never hiring demand or job-market growth."

**4. SDG impact (about 20 s): App**
*[App: `GET /api/v1/sdgs/data_analyst`. Show `data_mode: "cached"`.]*
- "This one is in the app. Every role and every skill is linked to a UN Sustainable Development Goal, with a reason."
- "Data Analyst links to SDG 8, decent work and economic growth, because it helps organisations make evidence-based decisions."
- "Skills like critical thinking link to SDG 4, quality education. These links are our team's judgment."

**5. Learning roadmap (about 40 s): Standalone**
*[Terminal: a roadmap for a student missing data visualization, mathematics, SQL and Excel.]*
- "From our own roadmap service: if a student is missing skills, they get an ordered plan of free resources."
- "Required skills come first, most important first. Here that's data visualization with Microsoft Learn's Power BI path: 8.2 hours."
- "The standalone total is about 24 and a half hours." (exact: 24.64 h)
- "Each step says where its hours come from. Here every number comes from the provider. For example, the statistics video is 8.25 hours, which is its length on YouTube."

*[Terminal: a Mechanical Engineer roadmap for a student missing CAD, MATLAB and Python.]*
- "Some providers don't say how long their course takes. For a Mechanical Engineer, Onshape's CAD course and MathWorks' MATLAB Onramp give no hours."
- "So we estimate them, 7 hours and 3 hours, and label them team estimate. The plan shows a warning saying so."
- "The Python course gives its own number, 3.2 hours. The standalone total is 13.2 hours."

**6. A portfolio project (about 20 s): Standalone**
*[Terminal: the "Online retail sales dashboard" project.]*
- "Each role also gets portfolio projects on real open data."
- "This one uses the UCI Online Retail II dataset, which is CC BY 4.0."
- "It has 5 steps, from cleaning the data to a Power BI dashboard, and about 14 hours. Those hours are our estimate."
- "We only link to datasets. We never copy them."

**7. Close (about 10 s)**
- "Every source is in our source register with its date and licence. All 85 links were checked on 23 October 2026 (UTC)."
- "Where something is our estimate, or not in the app yet, we say so."

---

**Presenter rule:** Do not state a role's rank or score. Show matches only as example output; rankings change when the catalog or data changes (for example, Data Analyst moved from 3rd to 6th for a Python+SQL profile after 22 roles were added).

**Don't say:**
- "trending", "live data" or "you will get hired"
- that all 30 roles are live in the app
- a role's rank or match score
- that GitHub activity shows job demand or job-market growth
- that a standalone number is what the app shows
- any number not shown on screen
- "the app" without saying which one — the live deployed app (https://mustaqbal-ai.replit.app, not yet republished with the 30-role release candidate) and the backend release candidate (`feature/13b-release-candidate`, integrated and validated but not deployed) are in different states; say which one a claim is about
- that live RunPod-assisted matching was tested against the final 30-role release candidate — it is available where configured, falling back to exact-skill matching otherwise, but that combination has not been live-tested end to end on this release
