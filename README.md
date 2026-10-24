# Mustaqbal AI

> AI-assisted career exploration for university students: see which roles fit the skills you already have, how GitHub developer activity is moving for them, and what to learn next — with hours for each step.

---

## Team Information

| Field | Details |
|---|---|
| **Team Name** | CodeBlack |
| **Team Domain** | Domain 1 — AIVERSECITY |
| **SDG Track** | SDG 4, 5, 8, 9, 10 (declared track); **primary focus SDG 8** — Decent Work and Economic Growth, **supporting SDG 4** — Quality Education |
| **Team Leader** | Rehan Anjum |
| **University** | UCSI University, Malaysia (team affiliation on record — individual members are not all assumed to attend UCSI) |
| **Number of Members** | 4 |

## Links

| Resource | Link |
|---|---|
| GitHub Repository | https://github.com/xlBABA/CodeBlack_SDC |
| Live Demo | https://mustaqbal-ai.replit.app |
| RunPod Endpoints | https://api.runpod.ai/v2/f0phohhegtydji |
| Slide Deck | https://canva.link/pf4g0a1ofti915u |
| Demo Video | **TODO:** `[ADD_DEMO_VIDEO_URL]` — not yet supplied |

---

## Overview

### Problem

University students and recent graduates often struggle to identify suitable career paths because they lack accessible, personalized guidance connecting their academic qualifications, technical skills and project experience to real-world employment opportunities. The International Labour Organization's *Global Employment Trends for Youth 2024* reports approximately 20.4% of young people worldwide were not in employment, education or training in 2023 — a global contextual baseline, not a measured impact of this project, but illustrative of the wider challenge.

### Solution

Mustaqbal AI is a web-based career exploration platform. A student builds a profile manually or uploads a CV PDF; GLM-5.3 (via a RunPod Public Endpoint) drafts a structured profile that the student reviews and must confirm before anything is scored. A deterministic, explainable matching engine then ranks 30 curated occupational roles against the student's skills, discloses exactly which skills matched and which are missing, and surfaces a learning roadmap, portfolio project ideas, cached GitHub trend signals, and UN SDG links for each role.

This supports **SDG 8** (Target 8.6 — reducing the proportion of youth not in employment, education or training) by helping students identify realistic career pathways, and **SDG 4** (Target 4.4 — increasing youth with skills relevant to employment) by surfacing concrete, free learning resources for each skill gap.

### Key Features

- **Manual student profile entry** — degree, semester, interests, skills and project text, mapped to a shared 20-skill vocabulary.
- **PDF CV upload** with local text extraction (never written to disk).
- **GLM-5.3-assisted extraction** — structured draft (education, skills with an exact supporting quote, projects, experience, certifications) via a RunPod Public Endpoint; a 30-second timeout falls back to manual entry rather than guessing.
- **Editable draft and user confirmation** — nothing is scored until the student reviews and confirms; unmatched CV skills can be manually mapped to a catalogue skill.
- **Deterministic career recommendations** — a written, weighted scoring formula, not a black box; every score ships with an explanation.
- **Skill normalization and skill-gap analysis** — exact/alias matching, contained-phrase detection ("Python (pandas)" → Python, partial credit), and "Did you mean…?" suggestions for unrecognised fragments.
- **Thirty-role occupational catalogue**, sourced from O*NET, across Technology & AI, Business & Finance, Engineering & Manufacturing, and Healthcare & Sustainability.
- **Learning resources and project recommendations** — cached, checked, free-to-access resources with real or team-estimated hours; portfolio projects on real open datasets, linked not copied.
- **Cached GitHub-based trend signals** — developer-activity counts for 12 of the 20 skills, always labelled as developer activity, never hiring demand.
- **SDG mappings** — every role and skill linked to a UN Sustainable Development Goal with a one-sentence reason.
- **Explainability and graceful fallback** — every match carries caveats (limited coverage, degraded semantic matching, unrecognised skills); nothing is silently dropped or invented.

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| Backend | Python, FastAPI, Pydantic |
| Database | SQLite (via SQLAlchemy) |
| AI — CV extraction | Z.ai **GLM-5.3**, via a RunPod **Public Endpoint** |
| AI — optional matching | `sentence-transformers/all-MiniLM-L6-v2`, via our own RunPod **Serverless** worker |
| Hosting | Replit (Autoscale Deployment) |

See `submission/SDC2026_CodeBlack_TechDeclaration.pdf` §2.2 for the complete, version-pinned dependency list with individual licenses.

---

## Project Structure

```
.
├── backend/                     # FastAPI application (unchanged in structure)
│   ├── app/
│   │   ├── api/v1/endpoints/    # One router module per route group
│   │   ├── services/            # Business logic, incl. hussain_matching/ (vendored matcher)
│   │   ├── data/cached/         # Versioned JSON: roles, skills, resources, projects, SDGs, trends
│   │   └── schemas/             # Pydantic request/response models
│   ├── tests/                   # Backend regression suite
│   └── .env.example
├── frontend/                    # React + Vite application (unchanged in structure)
│   ├── src/
│   └── .env.example
├── runpod-worker/                # Our own RunPod Serverless handler (embedding worker)
│   ├── handler.py
│   ├── Dockerfile
│   └── README.md                 # Full deploy instructions (Hussain)
├── runpod/
│   └── README.md                 # Entry point: distinguishes GLM-5.3 from the embedding worker
├── docs/
│   ├── architecture/              # Data-flow and component documentation
│   ├── screenshots/                # TODO: application UI screenshots
│   ├── proof/runpod/                # Real RunPod deployment evidence (screenshots + logs)
│   ├── LICENSE_REVIEW.md
│   └── (team working docs: prd-inputs-jawad.md, tools-declaration-inputs.md, …)
├── submission/
│   ├── SDC2026_CodeBlack_Preliminary.pdf
│   ├── SDC2026_CodeBlack_TechDeclaration.pdf
│   ├── SDC2026_CodeBlack_Replit_POU.pdf
│   └── SDC2026_CodeBlack_Runpod_POU.pdf
├── .env.example                   # Top-level pointer — see backend/ and frontend/ for the real ones
├── .gitignore
├── LICENSE
└── README.md
```

`backend/` and `frontend/` are unchanged from the working application — this submission does not
restructure them to match the official template's `src/`-style layout, since that layout does not fit a
two-service (API + SPA) application.

### Architecture

Full data-flow diagram and component breakdown: [`docs/architecture/README.md`](docs/architecture/README.md).

Short version:
```
Student → React frontend → FastAPI backend → (manual profile | CV → GLM-5.3 → draft)
        → student review & confirmation → skill normalization → matching engine
        → career recommendations, roadmap, projects, SDG mapping, trend signals
```

---

## How to Run

### Option 1 — Use the live deployment (no setup)

Open https://mustaqbal-ai.replit.app.

### Option 2 — Run on Replit

1. Import this repository: **Create Repl → Import from GitHub** → `xlBABA/CodeBlack_SDC`.
2. No `.replit`/`replit.nix` file is committed to this repository (see `backend/DEPLOYMENT.md` — the
   team deliberately left this undecided before deployment, and the live deployment's Replit workspace
   configuration was set up directly in the Replit UI, never version-controlled). **TODO (team):**
   export and commit the actual `.replit` configuration from the live workspace if it should be part of
   the submission.
3. Set the variables listed in `backend/.env.example` in Replit's **Secrets** tab — at minimum
   `RUNPOD_API_KEY` if you want GLM-5.3 CV extraction or the optional embedding endpoint active.
4. Run `cd backend && python start.py` (reads `PORT` from the platform; binds `0.0.0.0`).

### Option 3 — Run locally

**Backend** (Python 3.11 or 3.12 — verified against 3.11.9 in this environment):
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
copy .env.example .env         # then fill in only what you actually have
python -m uvicorn app.main:app --reload
```
Backend listens on `http://127.0.0.1:8000`; health check at `GET /api/v1/health`.

**Frontend** (Node.js, npm):
```bash
cd frontend
npm ci
copy .env.example .env.local   # optional — defaults already point at the local backend via proxy
npm run dev
```
Frontend dev server listens on `http://localhost:5173` and proxies `/api` to the backend.

Both command sets above were run and confirmed working in this environment during submission
preparation (see Testing & Validation below) — not merely copied from a template.

### Run Tests

```bash
# Backend
cd backend
python -m pytest -q tests app/services/hussain_matching/tests

# Frontend
cd frontend
npm run lint
npm run build
```

---

## How We Use Replit

- **Hosting:** the full application (React frontend served by the FastAPI backend) runs on a Replit
  Autoscale Deployment at https://mustaqbal-ai.replit.app.
- **Development:** Replit Agent was used by Rehan for the CV PDF extraction feature — timeout
  investigation, FastAPI improvements, diagnostics, implementation and automated testing.
- **Secrets:** RunPod API credentials are stored in Replit Secrets on the server side, never in the
  code or repository.
- **Plan:** Replit Core, via the SDC sponsor voucher.

📄 Proof of use: [`submission/SDC2026_CodeBlack_Replit_POU.pdf`](submission/SDC2026_CodeBlack_Replit_POU.pdf)
(usage screenshots, $10.68 spent of a $10.68+$9.32 period total, 1,150 requests over 2 days of deployment).

## How We Use RunPod

Mustaqbal AI uses **two separate RunPod integrations** — see [`runpod/README.md`](runpod/README.md)
for the full breakdown. In short:

1. **GLM-5.3 (CV extraction)** — a RunPod **Public Endpoint** (`b1dd8hy2hqo1nb`) running Z.ai's
   GLM-5.3, called from `backend/app/services/glm_client.py` to turn an uploaded CV's text into a
   structured, student-reviewed draft profile.
2. **Optional embedding similarity (matching)** — our **own RunPod Serverless worker**
   (`runpod-worker/`, endpoint `f0phohhegtydji`), running `sentence-transformers/all-MiniLM-L6-v2`,
   deployed and live-tested on 2026-10-23. When reachable, it gives partial credit for related skills
   and interprets free-text skills; when not, matching falls back to exact-skill matching only, and
   every affected result is visibly labelled "degraded."

Example request (embedding endpoint, no real key shown):
```bash
curl -X POST "https://api.runpod.ai/v2/f0phohhegtydji/runsync" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \
  -d '{"input": {"texts": ["SQL", "Database Querying"]}}'
```

**Whether the optional embedding endpoint is active on the live Replit deployment is a single-test,
point-in-time finding, not a confirmed permanent state.** Jawad made one real `POST /careers/match`
test against the live deployment on 2026-10-24 (~19:43 UTC, invented profile, no CV upload); every
match in that one response was labelled "degraded" — semantic matching was off at that moment. This
does not confirm RunPod's state generally; credentials can be added, removed, or temporarily
unreachable independently of any single check. See [`runpod/README.md`](runpod/README.md) for the
full, dated evidence and its caveats.

📄 Proof of use: [`submission/SDC2026_CodeBlack_Runpod_POU.pdf`](submission/SDC2026_CodeBlack_Runpod_POU.pdf)
· detailed evidence: [`docs/proof/runpod/README.md`](docs/proof/runpod/README.md),
[`docs/proof/runpod/live-run.md`](docs/proof/runpod/live-run.md)

---

## Testing & Validation

Results from this submission-preparation session (2026-10-25):

| Check | Result |
|---|---|
| Backend regression suite (`pytest tests app/services/hussain_matching/tests`) | **800 passed, 13 skipped** |
| Frontend lint (`oxlint`) | **Passed**, 0 issues |
| Frontend production build (`vite build`) | **Passed** |
| `runpod-worker` unit tests (mocked, no GPU/model) | **9 passed** |
| Secret scan (tracked files, common key patterns, committed databases/PDFs) | **Clean** — no real keys, no committed `.db`/`.sqlite` files, no PDFs/CVs tracked |
| GitHub public read access | **Confirmed** (`git ls-remote` succeeds with no auth) |

AI-generated code was reviewed through tests, diffs and cross-review rather than line-by-line reading
of every change — see `submission/SDC2026_CodeBlack_TechDeclaration.pdf` §4.3 and
[`docs/AI_USAGE_LOG.md`](docs/AI_USAGE_LOG.md) (Hussain's matching work, dated 2026-10-21; brought over
from `origin/feature/hussain-matching`, unmodified) for the full AI-usage disclosure.

---

## Known Limitations & Responsible AI

- **Scores are not hiring predictions.** Every response carries this disclaimer explicitly, not just in docs.
- **CV extraction can misread a CV.** Mitigated: a skill is only added if GLM-5.3 can quote it directly from the CV text, and the student must review and confirm the full draft before it is used.
- **Semantic matching can map a skill wrongly.** Mitigated: a 0.60 similarity threshold, half credit with a "please confirm" caveat, and a 14-pair exclusion list blocking known look-alike false positives (e.g. Git↔GIS, Financial Analysis Software↔Analytical/Statistical Software).
- **The 20-skill catalogue is small relative to 30 roles** — rankings for very generic profiles can look implausible; 5 roles are explicitly flagged `skills_coverage: "limited"` rather than scored as if fully covered.
- **GitHub trend signals are developer activity, not hiring demand**, cover only 12 of 20 skills, and move a score by at most a few points.
- **Single external AI provider (RunPod)** for both optional features — both fail gracefully (manual entry / exact-match fallback), never silently.
- **SQLite persistence across Replit restarts is unverified.**
- **No user accounts, no name/contact field stored** — student profiles are otherwise retained with no expiry currently set in code.

## Challenges & Learnings

- Reconciling a deterministic, explainable scoring algorithm with an optional semantic-matching layer that can fail independently — solved with a labelled "degraded" fallback rather than a silent one.
- Keeping role/skill provenance (O*NET sourcing, team-estimated values, cached-vs-live data) honestly disclosed throughout the API responses themselves, not only in docs that a user would never see.
- Coordinating four parallel workstreams (backend/integration, frontend, matching/RunPod, data/catalogue) on long-lived feature branches without losing track of what had — and had not — actually been merged into the release candidate at any given point.

## Future Improvements

- [ ] Expand the skill catalogue beyond 20 skills to reduce implausible rankings for generic profiles.
- [ ] Verify and, if needed, fix SQLite persistence across Replit restarts/redeploys (or switch to the already-designed-for Postgres DSN path).
- [ ] Add live, not just offline, GitHub trend refresh with rate-limit handling.
- [ ] Structured usability testing with a pilot group, per the Phase 1 preliminary submission's proposed KPI (20% reduction in career-exploration task completion time).
- [ ] Add dedicated live-deployment proof for GLM-5.3 specifically (see `runpod/README.md`).

---

## Team

| Name | Role | GitHub |
|---|---|---|
| Rehan Anjum | Team Lead — Backend development, integration, deployment, submission coordination | [@rehanjum9](https://github.com/rehanjum9) |
| Mohammad S. | Frontend development, React UI and user experience | [@xlBABA](https://github.com/xlBABA) |
| Hussain | Career matching, semantic embeddings, RunPod integration | [@Hussaink10](https://github.com/Hussaink10) |
| Jawad | Occupational data, trends, learning resources and SDG mapping | [@jvwvd](https://github.com/jvwvd) |

GitHub usernames above are inferred from commit author identity (two confirmed directly via GitHub's
no-reply commit email format; two confirmed to exist as real accounts via the public GitHub API) —
please confirm all four are correct before final submission.

---

## Submission Checklist

- [x] Team name, domain and SDG track filled in
- [x] Slide deck link added (reachability confirmed, HTTP 200 — content not reviewed)
- [ ] Demo video link added — **pending**, see Links above
- [x] Replit used, with proof of use in `submission/`
- [x] RunPod used, with proof of use in `submission/`
- [x] Preliminary submission completed (`SDC2026_CodeBlack_Preliminary.pdf`)
- [x] Technology declaration completed (`SDC2026_CodeBlack_TechDeclaration.pdf`) — all 7 compliance boxes ticked in the document itself, including third-party licensing/attribution and judge prototype access; this README's O*NET/third-party attribution section (below) is what makes the attribution part of that declaration actually true in the repository
- [x] All four submission PDFs present, correctly named, inspected and readable (see `submission/`)
- [x] "How to Run" steps verified in this environment (backend `uvicorn`, frontend `npm run dev`/`build`)
- [x] No API keys or secrets committed to the repository (scanned; see Testing & Validation)
- [ ] **Judge/committee collaborator access** beyond public repository read — not independently verifiable from this session; confirm directly in GitHub → Settings → Collaborators

---

## Data Attribution & Third-Party Licenses

### O*NET Attribution (mandatory)

> This application uses occupational information derived from the O*NET database, developed under the sponsorship of the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA).
>
> O*NET® is a trademark of USDOL/ETA.
>
> O*NET data are made available under the Creative Commons Attribution 4.0 International (CC BY 4.0) license.
>
> Source: https://www.onetcenter.org/database.html
>
> License: https://creativecommons.org/licenses/by/4.0/
>
> The occupational data has been adapted into a curated career catalogue for Mustaqbal AI. Matching scores, interpretations and career recommendations are generated by this application and do not constitute endorsement by USDOL/ETA.

**What was actually adapted:** 30 occupations' skill/tool data from individual O*NET OnLine pages
(importance scores 0–100 rescaled by the team to a 1–5 scale; tool importances and required/optional
flags are team estimates, not O*NET-provided values). Full per-source attribution, dates and a 85-link
check are recorded in the team's working documents (`docs/prd-inputs-jawad.md`,
`docs/tools-declaration-inputs.md`).

### Other data sources

| Source | Used for | License |
|---|---|---|
| GitHub Search API (repository-count snapshots, 12 skills) | Cached developer-activity trend signals | GitHub Terms of Service |
| UCI Machine Learning Repository (8 datasets) | Portfolio project ideas (linked, not copied) | CC BY 4.0 |
| World Bank World Development Indicators | Portfolio project ideas (linked, not copied) | CC BY 4.0 |
| UN Sustainable Development Goals | SDG mapping (team judgment reasons) | Public UN framework |
| 16 third-party learning resources (Microsoft Learn, MathWorks, freeCodeCamp, CS50x, QGIS, Onshape, GnuCash, etc.) | Learning roadmap links | Each provider's own terms; linked only, never redistributed — see `docs/prd-inputs-jawad.md` for the per-source table |

### Third-party code licenses

Full version-pinned table: `submission/SDC2026_CodeBlack_TechDeclaration.pdf` §2.2. Summary and a
license-compatibility review for the MIT → Apache 2.0 decision below: see
[`docs/LICENSE_REVIEW.md`](docs/LICENSE_REVIEW.md). One flagged dependency: **GSAP** is used under its
free **"Standard No-Charge License"**, which is not an OSI-approved open-source license (unlike every
other dependency in this project).

---

## License

- **`main`** currently carries **Apache License 2.0** (set by Mohammad, matching the official SDC
  template's own license).
- **This branch (`feature/13b-release-candidate`)** currently still carries the original **MIT License**.
- **Recommendation, not yet applied:** adopt Apache 2.0 project-wide for consistency with `main` and
  the official template — see [`docs/LICENSE_REVIEW.md`](docs/LICENSE_REVIEW.md) for the full
  compatibility review. This has **not** been changed without your approval.

This project uses data under CC BY 4.0 (O*NET and other sources above) independently of whichever
license covers the code itself — CC BY 4.0 requires attribution, provided above, and does not require
the code to share its license.
