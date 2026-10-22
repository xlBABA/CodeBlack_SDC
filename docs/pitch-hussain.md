# Pitch: AI matching (Hussain), about 60 seconds

## Read this before recording (three things that must be true, or the script says something the demo cannot show)
1. **The app must run my current matcher with RunPod on.** Today Rehan's branch still runs an older offline copy (no RunPod, no "Database Querying" to SQL).
   Use the integrated setup from `docs/integration-notes-for-rehan.md`: `MATCHING_MODE=hussain`, `CATALOG_MODE=cached`, `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` exported in the shell that starts the server.
2. **Scenarios only change scores if Jawad's signals reach the matcher.** In Rehan's backend they currently do not (`NullTrendProvider`): moderate and fast give the same numbers as the baseline.
   If that is not wired before you record, delete the scenario paragraph from the script and from the demo. Do not say it while the screen shows identical scores.
3. **Warm RunPod up first.** The first request after idle takes about 20 to 25 s (cold start); later ones about 1 to 2 s. Send one match request a minute before recording.
   I have not seen the frontend (it is built separately and is not in this repo), so button names below are placeholders: use the real labels.

## The script (about 60 seconds, about 150 words)

> **[Formula]** Our matching is a transparent score, not a black box. For each role we estimate how well a student's profile lines up with it:
> fifty percent skills, twenty percent experience, fifteen percent prerequisites, fifteen percent transferable skills.
> It is an estimated alignment, not a hiring prediction.
>
> **[Scenarios]** Moderate or fast AI adoption nudges the weight of rising or falling skills by ten or twenty-five percent, no more.
> That is a labelled assumption, and the trend data is GitHub developer activity, not job demand.
>
> **[RunPod]** Students don't type our exact skill names, so embeddings on RunPod map "Database Querying" to SQL.
> It's an interpretation, so it earns half credit, and the app says: please confirm.
>
> **[Fallback]** If RunPod is down, matching still works on exact skills and says it is degraded.
>
> **[Projects]** And students can ask: what if I built this project? One data project lifts a Data Analyst score from seven to forty. A hypothetical, not a promise.

Delivery notes: at a normal 150 words per minute this runs just over 60 seconds; if it runs long, drop "A hypothetical, not a promise." (the demo step shows the disclaimer anyway).
Say "seven to forty" slowly. Do not say "accuracy" or "predicts jobs" anywhere.

## Demo steps for the video

**Student (fictional, use exactly this so the numbers match):** semester 5, Computer Science, undergraduate; interest "data analytics"; skills **Python, Excel, "Database Querying", "Charts and graphs"**; one project "Synthetic sales dashboard exercise".
Target role for the project step: **Data Analyst**.

| # | Do | Point at | Say (short) |
|---|---|---|---|
| 1 | Enter the profile above and run **career matching** (`POST /careers/match`) | The ranked list: public_health_analyst 20, financial_analyst 18, software_developer 16, accountant 13, data_analyst 7 | "Each role gets one score, with the breakdown underneath." |
| 2 | Open the top role's **score breakdown** | Skills / experience / prerequisites / transferable. Prerequisites show 0 and the explanation says "prerequisites not assessed" | "Where a role has no prerequisites we don't invent a score; that weight is shared out." |
| 3 | Open the **caveats** of the top role | `Interpreted "Database Querying" as SQL (similarity 0.71), partial credit; please confirm.` | "The student typed it their own way. RunPod mapped it to SQL, half credit, and asks them to confirm." |
| 4 | Run the **scenario** screen, moderate then fast (`POST /scenarios/simulate`) | The scenario caveat: "based on dated GitHub developer-activity (not job demand) signals; an assumption, not a forecast" and the small score changes. **Skip this row if signals are not wired (item 2 above).** | "Bounded, labelled, and the signal type is on screen." |
| 5 | **Fallback:** stop the server, restart it with `RUNPOD_API_KEY` unset, run the same match again (or show the saved screenshot) | Every match carries "Semantic matching unavailable; exact skill matching only (degraded)" and the interpreted-SQL caveat is gone | "Same app, no RunPod, still works, and it tells you." |
| 6 | Run **project simulation** for Data Analyst with `da_bank_campaign_analysis` (`POST /projects/simulate`) | `baseline_score 7.0`, `simulated_score 40.0`, the disclaimer "Hypothetical simulation only..." | "If they gained these four skills: seven to forty. A what-if." |

Recording tips: record step 5 separately and cut it in; the restart is slow. If the UI is not ready, the same six calls work in the API docs page at `/docs` of the running backend (FastAPI generates it), with the profile pasted as JSON.

## Five likely judge questions, honest answers

1. **Is this a trained AI model? How accurate is it?**
   No. The score is a transparent weighted formula; the weights (50/20/15/15) are our team's choices, not research results. The only model is a small open embedding model (all-MiniLM-L6-v2) that compares skill names.
   We have not validated the scores against real hiring outcomes, so we call it an estimated alignment and never a prediction. The similarity threshold of 0.60 was tuned on 52 fictional skill pairs.

2. **Why are the scores so low (7 to 20)?**
   Because the score is weighted coverage of what the role asks for, and our demo student has four skills, one project and no experience. Each role asks for six to nine skills.
   The number is for comparing roles and seeing gaps, not a grade. For example, a Python and SQL student scores 28 skill-coverage for Public Health Analyst but 10 for Data Analyst, because that role needs critical thinking, mathematics and visualization that they do not list.

3. **Are the scenarios a forecast of the job market?**
   No. They are two labelled assumptions that scale a skill's weight by 10% or 25% when a dated trend signal is rising or falling. Our signals are counts of new GitHub repositories, which show developer activity, not hiring demand, and the app says so on every adjusted match.
   In our tests the effect was small, a point or two. Where there are no signals, the scenario changes nothing and says so.

4. **What stops the AI from mapping a skill wrongly, and what do you send to RunPod?**
   It can map wrongly, so it is designed to be checked: only matches at or above 0.60 count, they get half credit, and the student is asked to confirm. A known miss: "Accounting" mapped to "Accounting Software" at 0.77 on Jawad's catalogue, and "Charts and graphs" narrowly missed (0.60).
   Known look-alike pairs can be blocked with a `not_equivalent` list, but Jawad's catalogue does not have one yet. Only skill names and phrases (200 characters at most) go to RunPod, no name, email or CV text, and the API key stays on the server.

5. **Does it use personal data, and is it fair? How many roles does it cover?**
   It uses skills, projects, interests, semester and degree. It does not use age, gender or nationality. Degree and semester only matter for a role's stated prerequisites, and none of the current 8 roles lists any, so prerequisites are marked "not assessed".
   Coverage is small: 8 verified roles from Jawad's O*NET-based catalogue, out of a target of 30. We say that in the response (`catalog_coverage`) and do not claim the list is complete.

## Facts behind the numbers (so nothing in the script is a guess)
- Weights: `services/matching/scoring.py` (`WEIGHTS`). Scenario multipliers: `scenarios.py` (moderate 1.10 / 0.90, fast 1.25 / 0.75).
- "Database Querying" to SQL, 0.71; partial credit `RELATED_CREDIT` 0.5: live RunPod run, `docs/proof/runpod/live-run.md`.
- 7 to 40: live API trial in the integration worktree (student above, role `data_analyst`, project `da_bank_campaign_analysis`). It assumes the project's four skills (SQL, Data Visualization, Mathematics, Systems Analysis) are gained.
- Scenario effect of a point or two: my matcher run on Jawad's data and cached signals (Python + SQL and Excel + Accounting students).
