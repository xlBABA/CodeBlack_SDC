# Pitch: AI matching (Hussain), about 60 seconds

## Read this before recording (four things that must be true, or the script says something the demo cannot show)
1. **The app must run my current matcher with RunPod on, on Jawad's 30-role data.** Today Rehan's branch still runs an older offline copy (no RunPod, no "Database Querying" to SQL).
   Use the integrated setup from `docs/integration-notes-for-rehan.md`: `MATCHING_MODE=hussain`, `CATALOG_MODE=cached`, `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` exported in the shell that starts the server.
   All numbers below were measured on `origin/feat/jawad-30-roles` @ `8cd1166`; with other data they change.
2. **Scenarios only change scores if Jawad's signals reach the matcher.** In Rehan's release candidate (`61eb394`) they do when `CATALOG_MODE=cached` (checked: moderate and fast change the scores below); in the default `fixture` mode they do not (`NullTrendProvider`).
   If the signals are not wired in the build you record with, delete the scenario paragraph from the script and from the demo. Do not say it while the screen shows identical scores.
   The exact request bodies and the results I got are in `docs/demo-payloads/`.
3. **Warm RunPod up first.** The first request after idle took 17 s in my test (cold start); later ones about 1 s. Send one match request a minute before recording.
4. **The project-simulation numbers were first emulated, then checked against Rehan's code only in-process.** I first got 23 to 40 by adding the project's missing skills in my own code (emulated). Rehan's `/projects/simulate` at `61eb394`, run with a test client (not a deployed server), returned the same: 23 to 40 with RunPod, 15 to 37 without.
   **Verify them once more on the running app before recording** and change the script if they differ. The matching numbers also differ if that app runs an older copy of my matcher.
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
> **[Fallback]** If RunPod is down, matching still works on exact skills, says it is degraded, and names what it could not read.
>
> **[Projects]** And students can ask: what if I built this project? One web project lifts a Software Developer score from about twenty-three to about forty. A hypothetical, not a promise.
> *(Project numbers: emulated, verify in the live app before recording.)*

Delivery notes: at a normal 150 words per minute this runs just over 60 seconds; if it runs long, drop "A hypothetical, not a promise." (the demo step shows the disclaimer anyway).
Say "twenty-three to forty" slowly. Do not say "accuracy" or "predicts jobs" anywhere.

## Demo steps for the video

**Student (fictional, use exactly this so the numbers match):** semester 5, Computer Science, undergraduate; interest "web development"; skills **Python, JavaScript, "Database Querying"**; no projects.
Target role for the project step: **Software Developer**.

| # | Do | Point at | Say (short) |
|---|---|---|---|
| 1 | Enter the profile above and run **career matching** (`POST /careers/match`) | The ranked list: software_developer 23, web_developer 22, public_health_analyst 15, data_scientist 14, database_administrator 12, computer_systems_analyst 10 | "Each role gets one score, with the breakdown underneath." |
| 2 | Open the top role's **score breakdown** | Skills 32 / experience 0 / prerequisites 0 / transferable 0. The explanation says "2 of 8 core skills (plus 1 interpreted from your wording, partial credit)" and "prerequisites not assessed" | "Where a role has no prerequisites we don't invent a score; that weight is shared out." |
| 3 | Open the **caveats** of the top role | `Interpreted "Database Querying" as SQL (similarity 0.71), partial credit; please confirm.` (also `Python counted as related to Programming (similarity 0.62); partial credit only.`) | "The student typed it their own way. RunPod mapped it to SQL, half credit, and asks them to confirm." |
| 4 | Run the **scenario** screen, moderate then fast (`POST /scenarios/simulate`) | software_developer 23 to 24 (moderate) to 25 (fast); web_developer 22 to 23; the caveat "Scenario adjusted the weight of: Git, JavaScript, Python (based on dated GitHub developer-activity (not job demand) signals; an assumption, not a forecast)". **Skip this row if signals are not wired (item 2 above).** | "Bounded, labelled, and the signal type is on screen." |
| 5 | **Fallback:** stop the server, restart it with `RUNPOD_API_KEY` unset, run the same match again (or show the saved screenshot) | Scores fall to software_developer 15, web_developer 13. Every match says "Semantic matching unavailable; exact skill matching only (degraded)"; the interpreted-SQL caveat is gone. My current matcher also says `Not recognised and not used: "Database Querying". Try a skill from the list.`, but Rehan's `61eb394` has an older copy that does **not**: point at it only after he re-syncs `hussain_matching` | "Same app, no RunPod, still works, and it tells you what it could not read." |
| 6 | Run **project simulation** for Software Developer with `sd_wdi_web_dashboard` (`POST /projects/simulate`) | **Emulated, verify in the live app:** software_developer 23 to 40 (the student gains Git, Programming and Complex Problem Solving; JavaScript is already held), and the disclaimer "Hypothetical simulation only..." | "If they gained these three skills: twenty-three to forty. A what-if." |

Project step, if you want a second number: in the same emulation `web_developer` goes 22 to 45 (offline: 13 to 43), so after this project the student's best role would be Web Developer, not Software Developer.
Without RunPod the same emulation gives software_developer 15 to 37.

Recording tips: record step 5 separately and cut it in; the restart is slow. If the UI is not ready, the same six calls work in the API docs page at `/docs` of the running backend (FastAPI generates it), with the profile pasted as JSON.

## Five likely judge questions, honest answers

1. **Is this a trained AI model? How accurate is it?**
   No. The score is a transparent weighted formula; the weights (50/20/15/15) are our team's choices, not research results. The only model is a small open embedding model (all-MiniLM-L6-v2) that compares skill names.
   We have not validated the scores against real hiring outcomes, so we call it an estimated alignment and never a prediction. The similarity threshold of 0.60 was tuned on 52 fictional skill pairs.

2. **Why are the scores so low (10 to 25)?**
   Because the score is weighted coverage of what the role asks for, and our demo student has three skills, no project and no experience. Each role asks for six to eleven skills.
   The number is for comparing roles and seeing gaps, not a grade. The demo student has 2 of the 8 core skills of Software Developer and half credit for a third, which is a skills score of 32 out of 100.

3. **Are the scenarios a forecast of the job market?**
   No. They are two labelled assumptions that scale a skill's weight by 10% or 25% when a dated trend signal is rising or falling. Our signals are counts of new GitHub repositories, which show developer activity, not hiring demand, and the app says so on every adjusted match.
   In our tests the effect was small, one to three points. Where there are no signals, the scenario changes nothing and says so.

4. **What stops the AI from mapping a skill wrongly, and what do you send to RunPod?**
   It can map wrongly, so it is designed to be checked: only matches at or above 0.60 count, they get half credit, and the student is asked to confirm. If the two best candidates are within 0.03 of each other it does not guess; it asks "did you mean X or Y?"
   A skill it cannot read is listed on every match ("Not recognised and not used"), not dropped silently. Known look-alike pairs can be blocked with Jawad's `not_equivalent` list (12 pairs). Two wrong pairs still get partial credit today: Git with GIS, and Financial Analysis Software with Analytical/Statistical Software; I have proposed adding them.
   Only skill names and phrases (200 characters at most) go to RunPod, no name, email or CV text, and the API key stays on the server.

5. **Does it use personal data, and is it fair? How many roles does it cover?**
   It uses skills, projects, interests, semester and degree. It does not use age, gender or nationality. Degree and semester only matter for a role's stated prerequisites, and none of the current 30 roles lists any, so prerequisites are marked "not assessed".
   Coverage is limited: 30 verified roles built on a 20-skill catalogue, from Jawad's O*NET-based data, and four roles are flagged as only partly covered by those skills. We say that in the response (`catalog_coverage` and a caveat) and do not claim the list is complete.

## Facts behind the numbers (so nothing in the script is a guess)
- Weights: `services/matching/scoring.py` (`WEIGHTS`). Scenario multipliers: `scenarios.py` (moderate 1.10 / 0.90, fast 1.25 / 0.75).
- "Database Querying" to SQL, 0.71 (0.7061 measured live on 2026-10-24); partial credit `RELATED_CREDIT` 0.5: `docs/proof/runpod/live-run.md` and section 9 of `docs/review-30-roles.md`.
- Demo student numbers (ranking, offline fallback, moderate and fast): my matcher with live RunPod on Jawad's 30 roles `8cd1166` and his cached signals (12 signals, all developer activity).
- **Emulated, verify in the live app before recording:** project simulation (23 to 40, and 22 to 45 for web_developer). Made by adding the project's skills that the student lacks (Git, Programming, Complex Problem Solving) as exact skills and re-matching; the backend's own simulation may differ.
- Scenario effect of one to three points: section 7 of `docs/review-30-roles.md` (10 students x 30 roles) and this student.
