# Demo talking points — Jawad

## Data-section narration (30-45 seconds, about 100 words)

Say this out loud. Every app claim here was checked on the deployed API (https://mustaqbal-ai.replit.app) with GET requests.

> "My part is the data behind Mustaqbal AI.
> Our catalog has 30 career roles and 20 skills, all from O*NET, the US Department of Labor's job database.
> Each role has free learning resources; the first 8 have portfolio projects.
> Every one has a dated, registered source.
> Every role and skill links to a UN Sustainable Development Goal, with a reason.
> The app shows the first 8 roles, labelled cached.
> Trends are different.
> The app's trend data is a placeholder, labelled fixture, not live.
> Our GitHub snapshots exist, but are not connected yet.
> And GitHub activity is not job demand."

**What each sentence rests on:**
- **30 roles, 20 skills:** counted in our data on `feat/jawad-30-roles` (standalone). The 22 newer roles are not in the app yet.
- **SDGs, "cached" label:** on 2026-10-22, `GET /api/v1/sdgs/{role_id}` returned `data_mode: "cached"` for the 8 role IDs the app had, covering 20 distinct skills. Every mapping matched our data.
- **Trends are "fixture":** `GET /api/v1/trends` returns `data_mode: "fixture"` and the warning "No real trend source is connected yet".
- **Resources and projects:** in our data (16 resources, 17 projects for the first 8 roles, each with a dated, registered source). The app's roadmap and project endpoints are POST, so we did not check them.

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
- "We didn't invent any roles or skills. The app still shows the first 8; the other 22 are in our data and not connected yet."

**2. One role's skills (about 25 s): Standalone**
*[Terminal: Data Analyst skills with importance.]*
- "Here's the Data Analyst. Each skill has an importance from 1 to 5."
- "Critical thinking is 5. O*NET scores it 72 out of 100, and we turn that into 1 to 5."
- "Some numbers are our own estimate, and we say so. O*NET gives mathematics 63, which would be a 4. We raised it to 5 for a data role."
- "For tools like SQL and Excel, O*NET doesn't give an importance score. So those numbers are team estimates."

**3. Trend signal (about 30 s): App first, then Standalone**
*[App: `GET /api/v1/trends`. Show `data_mode: "fixture"` and the warning.]*
- "In the app, the trend section is a placeholder. It says fixture, not live, and warns that no real trend source is connected yet."

*[Terminal (standalone): Data Analyst trend output, with status "cached" and the date.]*
- "Our real trend data exists, but it's not connected to the app yet. Here it is from our own service."
- "It counts new GitHub projects for each skill, comparing the last 30 days with the 30 days before."
- "For Excel, it's rising. For SQL, it's stable: 3,531 new projects, up from 3,273."
- "The status says cached, last refreshed 21 October 2026. It's saved data, not live."
- "And to be clear: this is developer activity, not job demand."

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

**Don't say:**
- "trending", "live data" or "you will get hired"
- that GitHub activity shows job demand
- that a standalone number is what the app shows
- any number not shown on screen
