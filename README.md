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
| **University** | UCSI University, Malaysia |
| **Number of Members** | 4 |

## Links

| Resource | Link |
|---|---|
| GitHub Repository | https://github.com/xlBABA/CodeBlack_SDC |
| Live Demo | https://mustaqbal-ai.replit.app |
| RunPod Endpoints | https://api.runpod.ai/v2/f0phohhegtydji |
| CV Extraction API Provider | https://openrouter.ai |
| Slide Deck | https://drive.google.com/file/d/1BT8s42cli9p-Q5nXa0CJn5SRnVuFVror/view?usp=sharing |
| Demo Video | **TODO:** `[ADD_DEMO_VIDEO_URL]` — not yet supplied |

---

## Overview

### Problem

University students and recent graduates often struggle to identify suitable career paths because they lack accessible, personalized guidance connecting their academic qualifications, technical skills and project experience to real-world employment opportunities. The International Labour Organization's *Global Employment Trends for Youth 2024* reports approximately 20.4% of young people worldwide were not in employment, education or training in 2023 — a global contextual baseline, not a measured impact of this project, but illustrative of the wider challenge.

### Solution

Mustaqbal AI is an AI-assisted career exploration platform designed to help university students identify suitable career paths based on their education, skills, interests and experience.

Students can create their profiles manually or upload a PDF resume. The application integrates **OpenRouter with Z.ai GLM-5.3 FlashX** to extract structured information from uploaded CVs into editable profiles, which students must review and confirm before proceeding.

For intelligent skill interpretation, Mustaqbal AI integrates **RunPod Serverless GPU infrastructure**, hosting the **all-MiniLM-L6-v2 embedding model** to identify semantically related skills and improve skill matching. The application also retains its existing RunPod GLM-5.3 CV extraction integration as a configurable alternative, where supported by the deployed configuration.

Career recommendations are generated using a deterministic, explainable weighted scoring engine that ranks 30 curated O*NET-derived occupational roles. Students receive career recommendations, skill-gap insights, personalized learning roadmaps, portfolio project suggestions, cached GitHub-based trend indicators and relevant United Nations Sustainable Development Goal (SDG) connections.

The platform supports **SDG 8 — Decent Work and Economic Growth** and **SDG 4 — Quality Education** by helping students explore career opportunities and identify skills they can develop for future employment.

### Key Features

- **AI-Assisted CV Extraction** — Students can upload PDF resumes and extract education, technical skills, experience, projects and certifications into structured profile drafts. The application supports Z.ai GLM-5.3 FlashX through OpenRouter and the existing GLM-5.3 integration through a RunPod Public Endpoint, selected through backend configuration.
- **Manual Profile Entry** — Students can create profiles manually without uploading a CV.
- **Editable CV Review and Confirmation** — AI-extracted information must be reviewed and confirmed by the student before career matching. Manual entry remains available when extraction is unavailable.
- **Explainable Career Recommendations** — A deterministic weighted matching engine evaluates student skills against 30 curated O*NET-derived occupational roles and provides transparent matching explanations.
- **RunPod-Powered Semantic Skill Matching** — A RunPod Serverless GPU endpoint hosts the `all-MiniLM-L6-v2` embedding model to recognize semantically related skills, such as interpreting "Database Querying" as SQL. If the service is unavailable, matching falls back to exact skills with an appropriate warning.
- **Skill Normalization and Gap Analysis** — Identifies recognized skills, aliases, transferable skills and missing competencies relevant to selected careers.
- **Career Learning Roadmaps** — Provides curated learning resources and suggested next steps for developing career-related skills.
- **Portfolio Project Recommendations** — Recommends practical portfolio projects where catalogue coverage is available. The current dataset includes 17 projects across 8 career roles.
- **Cached Technology Trend Insights** — Displays GitHub repository-activity snapshots for selected skills, clearly distinguished from job-market demand.
- **Sustainable Development Goal Alignment** — Connects career exploration with relevant United Nations SDGs, particularly SDG 8 and SDG 4.
- **Responsible AI and Graceful Fallback** — Provides profile confirmation, transparent scoring caveats, semantic-matching degradation notices and manual CV-entry alternatives.

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | Python, FastAPI, Pydantic |
| Database | SQLite, SQLAlchemy |
| AI CV Extraction | OpenRouter API — Z.ai GLM-5.3 FlashX (`z-ai/glm-5.3-flashx`) |
| Semantic Skill Matching | RunPod Serverless — `all-MiniLM-L6-v2` |
| Career Recommendation | Explainable weighted matching algorithm |
| Hosting | Replit |

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
Student → React frontend → FastAPI backend → (manual profile | CV → GLM-5.3 RunPod/ ZAI GLM 5.3 FlashX Paid → draft)
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

RunPod is an official SDC Hackathon sponsor resource used in Mustaqbal AI for GPU-powered artificial intelligence capabilities.

### 1. Semantic Skill Matching — RunPod Serverless

The application integrates a RunPod Serverless GPU endpoint hosting the pre-trained `sentence-transformers/all-MiniLM-L6-v2` embedding model.

The model generates semantic representations of skills, allowing the application to identify relationships between different expressions of related skills.

For example, "Database Querying" may be interpreted as SQL based on semantic similarity.

**RunPod Serverless Endpoint:**

https://api.runpod.ai/v2/f0phohhegtydji

The integration uses server-side `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` configuration. No credentials are included in the repository.

If semantic matching is unavailable, the application falls back to exact skill matching and displays an appropriate limitation.

### 2. GLM-5.3 — RunPod Public Endpoint

The application also retains its original Z.ai GLM-5.3 CV extraction integration through a RunPod Public Endpoint.

This integration converts extracted PDF resume text into a structured, editable student profile draft.

The provider can be selected using `LLM_PROVIDER=runpod`.

**RunPod GLM Public Endpoint ID:** `b1dd8hy2hqo1nb`

The student must review and confirm extracted profile information before career matching.

### 3. RunPod Sponsor Usage

RunPod sponsor-provided credits were used to deploy and test the semantic embedding worker and to support the original GLM-5.3 CV extraction integration.

The actual embedding worker implementation is available in `runpod-worker/`.

Detailed integration documentation is available in [`runpod/README.md`](runpod/README.md).

**RunPod Proof of Use:**

[SDC2026_CodeBlack_Runpod_POU.pdf](submission/SDC2026_CodeBlack_Runpod_POU.pdf)

Additional evidence:

- [RunPod deployment proof](docs/proof/runpod/README.md)
- [RunPod live testing records](docs/proof/runpod/live-run.md)

The RunPod embedding endpoint was deployed and successfully tested by the team. Its activation in the currently published Replit configuration must be verified separately.

---

## How We Use OpenRouter

Mustaqbal AI also supports fast AI-assisted CV extraction using OpenRouter.

**API Provider:** OpenRouter

**Model:** Z.ai GLM-5.3 FlashX (`z-ai/glm-5.3-flashx`)

**API Base URL:** https://openrouter.ai/api/v1

**Purpose:** Extract structured education, skills, experience, projects and certifications from uploaded PDF resume text.

**Access Tier:** Paid API credits arranged by the team, separate from RunPod sponsor credits.

The backend supports two configurable CV extraction providers:

| Configuration | CV Extraction Provider |
|---|---|
| `LLM_PROVIDER=openrouter` | OpenRouter — Z.ai GLM-5.3 FlashX |
| `LLM_PROVIDER=runpod` | RunPod Public Endpoint — GLM-5.3 |

The OpenRouter implementation was developed and benchmarked on the team's fix branch. Its deployment to the live Replit application remains subject to final integration and verification.

OpenRouter API credentials are stored as server-side secrets and are never included in frontend code or committed to GitHub.

All AI-generated CV information remains subject to student review and confirmation before matching.

📄 Proof of use: [`submission/SDC2026_CodeBlack_Runpod_POU.pdf`](submission/SDC2026_CodeBlack_Runpod_POU.pdf)
· detailed evidence: [`docs/proof/runpod/README.md`](docs/proof/runpod/README.md),
[`docs/proof/runpod/live-run.md`](docs/proof/runpod/live-run.md)

---

## Testing & Validation

Mustaqbal AI has undergone backend regression testing, frontend validation, RunPod worker testing, CV extraction benchmarking and security checks.

The following results represent separate verified development snapshots and should not be interpreted as a completed end-to-end validation of the final integrated production build.

| Test / Validation | Reported Result |
|---|---|
| Submission preparation branch — Backend regression suite | 810 passed, 13 skipped |
| Submission preparation branch — Frontend lint | Passed |
| Submission preparation branch — Frontend production build | Passed |
| RunPod embedding worker — Unit tests | 9 passed |
| OpenRouter GLM-5.3 FlashX — CV extraction benchmark | 15 calls across 5 test CVs, 100% successful in the reported sample |
| OpenRouter GLM-5.3 FlashX — Median CV extraction latency | Approximately 2.2 seconds in the reported benchmark |
| OpenRouter/CV-specific automated tests | 16 passed |
| Mohammad's security/CV fix branch — Backend suite | 846 passed, 13 skipped, 1 environment-related failure |
| Secret scanning | No exposed API credentials reported in the reviewed files |

### OpenRouter Performance

The GLM-5.3 FlashX integration was benchmarked using five sample CVs across 15 API calls.

The reported median extraction latency was approximately 2.2 seconds, with successful extraction across the tested sample.

These are development benchmark results, not guaranteed response times for all users or production conditions.

### Security Validation

The backend includes a path-traversal protection fix for SPA static-file serving.

The security test suite covers encoded traversal attempts, path normalization, absolute paths and symlink escapes.

One symlink-related test could not execute successfully in the Windows test environment because the operating-system account lacked symbolic-link creation privileges. This test requires verification in a suitable environment before final release.

### Responsible AI

- Students must review and confirm AI-extracted CV information.
- Matching scores are experimental estimates, not employment predictions.
- RunPod semantic matching has an exact-match fallback.
- API credentials are kept in server-side environment secrets.
- External AI processing and provider usage are disclosed in the Technical & Tools Declaration.

**Final integration status:** Combined OpenRouter, RunPod and backend changes require a final regression run and deployment verification before the results can be described as production-validated.
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
