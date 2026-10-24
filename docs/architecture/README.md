# Architecture

## Data flow

```
Student
  │
  ├─ manual profile entry ──────────────────────────┐
  │                                                   │
  └─ PDF CV upload                                    │
       │                                               │
       ▼                                               │
  React frontend (Vite, TypeScript)                    │
       │ POST /api/v1/cv/parse (multipart, PDF)        │
       ▼                                               │
  FastAPI backend                                      │
       │                                               │
       ├─ local PDF text extraction (pypdf, in memory, │
       │  never written to disk)                       │
       │                                               │
       ├─ RunPod Public Endpoint: Z.ai GLM-5.3          │
       │  (b1dd8hy2hqo1nb) — text → structured draft    │
       │  (education, skills+evidence quotes, projects, │
       │  experience, certifications). 30s timeout      │
       │  falls back to manual entry, never invents.    │
       │                                               │
       ▼                                               │
  Editable draft review screen (frontend) ◄─────────────┘
       │ student reviews, maps unmatched skills,
       │ confirms before anything is scored
       ▼
  POST /api/v1/profile/analyze → StudentProfile stored in SQLite (SQLAlchemy)
       │
       ▼
  POST /api/v1/careers/match
       │
       ├─ Skill normalization (exact id/name/alias match against the
       │  20-skill catalogue; "Python (pandas)" → Python with partial
       │  credit and a confirm caveat; unrecognised fragments get a
       │  "Did you mean…?" suggestion)
       │
       ├─ Optional: RunPod Serverless embedding endpoint
       │  (all-MiniLM-L6-v2, f0phohhegtydji) — only when
       │  RUNPOD_API_KEY + RUNPOD_ENDPOINT_ID are both set and the
       │  endpoint is reachable. Maps free-text skills to the closest
       │  catalogue skill (≥0.60 cosine similarity, half credit,
       │  "please confirm"), and gives related-skill partial credit.
       │  Hussain's 14-pair not_equivalent exclusion list blocks
       │  known false positives (e.g. Git↔GIS) even if the embedding
       │  model would otherwise score them close.
       │  On failure/absence: falls back to exact-skill matching only,
       │  every affected match labelled
       │  "Semantic matching unavailable; exact skill matching only
       │  (degraded)" — never silently guessed.
       │
       ├─ Deterministic weighted scoring against the 30-role cached
       │  catalogue (skills 5/7 + experience 2/7 weight, since
       │  prerequisites/transferable skills are empty for all 30 roles
       │  today, so that weight is redistributed) — every score has a
       │  written explanation and per-match caveats, never a bare number.
       │
       └─ Optional scenario adjustment (moderate/fast): re-weights
          skills using cached, dated GitHub developer-activity
          snapshots (never a live GitHub call, never framed as hiring
          demand).
       │
       ▼
  Ranked RoleMatch list → frontend dashboard
       │
       ├─ Roadmap: POST /api/v1/roadmaps/generate — missing skills →
       │  cached learning resources, ordered by importance, with hours
       │  (provider-stated or a labelled team estimate); skills with no
       │  checked resource are disclosed, not silently dropped.
       ├─ Projects: POST /api/v1/projects/recommend / /simulate —
       │  cached portfolio projects on real open datasets (linked, not
       │  copied), plus a hypothetical "what if I had skill X" simulation.
       └─ SDG mapping: GET /api/v1/sdgs/{role_id} — every role and
          skill linked to a UN SDG with a one-sentence team-judgment
          reason.
```

## Components

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS | Single-page app; `frontend/src/lib/api.ts` is the one place that talks to the backend |
| Backend | FastAPI, Pydantic, SQLAlchemy | `backend/app/api/v1/endpoints/*.py`; see `contracts/` (if present) for the frozen API shape |
| Database | SQLite | Student profiles only (no name/contact field); persistence across Replit restarts is unverified — see `backend/DEPLOYMENT.md` |
| Cached data | Versioned JSON under `backend/app/data/cached/` | 30 roles (O*NET-derived), 20 skills, learning resources, portfolio projects, SDG mappings, 12 GitHub trend snapshots, 14 `not_equivalent` skill-exclusion pairs |
| CV extraction AI | Z.ai GLM-5.3 via RunPod Public Endpoint | `backend/app/services/glm_client.py`; see `../../runpod/README.md` |
| Optional matching AI | `sentence-transformers/all-MiniLM-L6-v2` via our own RunPod Serverless worker | `backend/app/services/hussain_matching/runpod_client.py`; worker source in `../../runpod-worker/` |
| Hosting | Replit (Autoscale Deployment) | Live at https://mustaqbal-ai.replit.app |

## Matching modes (server configuration, not user-visible toggles)

The backend has two independent config switches, both read from environment variables
(`backend/app/core/config.py`):

- **`CATALOG_MODE`**: `fixture` (small illustrative placeholder data) or `cached` (Jawad's real,
  sourced 30-role/20-skill/SDG/trend dataset). The deployed app has been confirmed (via live GET
  requests to role IDs outside the original 8) to be running `CATALOG_MODE=cached`.
- **`MATCHING_MODE`**: `fixture` (illustrative scoring, for early-stage testing) or `hussain`
  (the real deterministic algorithm described above). Both run fully offline unless the optional
  RunPod embedding endpoint is also configured and reachable.

These two switches are independent: `CATALOG_MODE=cached` can run with either matching mode, and
the matching algorithm itself never depends on which catalogue backs it.

## Known architectural limitations

- The 20-skill catalogue is small relative to 30 roles, so some role rankings for generic profiles
  can look implausible; 5 roles are explicitly flagged `skills_coverage: "limited"` rather than
  silently scored as if fully covered.
- Scenario trend signals cover only 12 of 20 skills and are GitHub developer-activity counts, never
  hiring demand or job-market growth.
- SQLite persistence across Replit restarts/redeploys has not been verified.
- Scores are an estimated profile-alignment number (`profile_alignment_estimate`), never a hiring
  probability — this disclaimer is embedded directly in every API response, not just in docs.

## TODO (team)

- Add a system block diagram image here if one exists from the Preliminary submission's appendix.
- Confirm whether `RUNPOD_API_KEY`/`RUNPOD_ENDPOINT_ID` are actually set on the live Replit
  deployment (see `../../runpod/README.md`'s last section) — not verified in this branch.
