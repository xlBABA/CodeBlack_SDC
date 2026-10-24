# Architecture

## Data Flow

Mustaqbal AI is an AI-assisted career exploration application built with a React and TypeScript frontend, a FastAPI backend, SQLite storage, curated occupational data, and external AI integrations through OpenRouter and RunPod.

The application supports two configurable providers for CV extraction:

- **OpenRouter:** Z.ai GLM-5.3 FlashX for fast CV information extraction.
- **RunPod Public Endpoint:** Z.ai GLM-5.3 for the original CV extraction implementation.

Separately, **RunPod Serverless** hosts the `all-MiniLM-L6-v2` embedding model for semantic skill matching.

The CV extraction provider is selected through backend configuration. The two CV providers are not assumed to run simultaneously or provide automatic failover.

```text
STUDENT
   |
   +-- Manual Profile Entry -------------------------+
   |                                                  |
   +-- PDF CV Upload                                  |
          |                                           |
          v                                           |
   React Frontend (Vite + TypeScript)                 |
          |                                           |
          | POST /api/v1/cv/parse                      |
          v                                           |
   FastAPI Backend                                    |
          |                                           |
          | Local PDF Text Extraction                 |
          | (pypdf, in memory)                        |
          v                                           |
   Configurable CV Extraction Provider               |
          |                                           |
          +-------------------+                       |
          |                   |                       |
          v                   v                       |
   OpenRouter API       RunPod Public Endpoint        |
   Z.ai GLM-5.3         Z.ai GLM-5.3                   |
   FlashX              (b1dd8hy2hqo1nb)             |
          |                   |                       |
          +---------+---------+                       |
                    |                                 |
                    v                                 |
         Structured CV Profile Draft                 |
         - Education                                  |
         - Skills + Evidence Quotes                   |
         - Projects                                   |
         - Experience                                 |
         - Certifications                             |
                    |                                 |
                    v                                 |
          Editable Profile Review <-------------------+
                    |
                    | Student reviews, edits,
                    | maps unmatched skills,
                    | and explicitly confirms
                    v
   POST /api/v1/profile/analyze
                    |
                    v
       StudentProfile Stored in SQLite
                    |
                    v
         POST /api/v1/careers/match
                    |
          +---------+-------------------+
          |                             |
          v                             v
   Skill Normalization          RunPod Serverless GPU
   (20 Core Skills)              all-MiniLM-L6-v2
          |                      Semantic Embeddings
          |                             |
          +-------------+---------------+
                        |
                        v
           Explainable Matching Engine
                        |
                        v
             Cached Career Catalogue
                (30 O*NET Roles)
                        |
                        v
             Ranked Career Matches
                        |
        +---------------+----------------+
        |               |                |
        v               v                v
     Roadmaps       Portfolio          SDG Mapping
     Resources      Projects           UN SDGs
        |
        +---------------+
                        |
                        v
               Cached GitHub Trends
                        |
                        v
                Student Dashboard
```

### CV Extraction Flow

Students may create profiles manually or upload PDF resumes.

When a PDF is uploaded, the backend extracts its text locally using `pypdf`. The extracted text is passed to the selected AI provider to generate a structured student profile draft.

The backend supports:

1. **OpenRouter — Z.ai GLM-5.3 FlashX**
   - Model ID: `z-ai/glm-5.3-flashx`
   - API Base URL: `https://openrouter.ai/api/v1`
   - Purpose: Fast extraction of education, skills, experience, projects and certifications.
   - Access: Paid API credits arranged by the team.

2. **RunPod Public Endpoint — Z.ai GLM-5.3**
   - Endpoint ID: `b1dd8hy2hqo1nb`
   - Purpose: Original AI-assisted CV extraction integration.
   - Access: RunPod sponsor-provided credits.

The backend selects the CV extraction provider through the `LLM_PROVIDER` environment variable.

The original RunPod integration remains available in the reviewed code. OpenRouter is implemented as an additional selectable provider, rather than an automatic replacement or automatic fallback.

AI-extracted information is presented as an editable draft. Students must review and confirm the information before matching. If extraction fails or times out, manual entry remains available.

The OpenRouter implementation has been developed and benchmarked on the team's fix branch. Its activation on the published Replit application must be verified after integration and deployment.

### Semantic Skill Matching

The application uses a deterministic weighted career matching engine with optional semantic similarity provided by RunPod.

**RunPod Serverless Embedding Endpoint:**

https://api.runpod.ai/v2/f0phohhegtydji

**Model:** `sentence-transformers/all-MiniLM-L6-v2`

The embedding model helps identify semantically related skill expressions. For example, "Database Querying" may be interpreted as SQL when the model's similarity score exceeds the configured threshold.

Semantic matching uses:

- A cosine similarity threshold of 0.60.
- Partial credit for related skill expressions.
- A student confirmation caveat for inferred skill mappings.
- Fourteen known non-equivalent skill exclusions to reduce incorrect mappings.

RunPod semantic matching requires both `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID`, together with the appropriate backend matching configuration.

If the endpoint is unavailable, incorrectly configured or temporarily failing, the matching engine falls back to exact-skill matching and displays a degraded-mode warning.

The availability of RunPod GLM-5.3 CV extraction does not automatically guarantee that the separate RunPod semantic embedding endpoint is active.

### Career Matching and Recommendations

After confirmation, student skills are normalized against the curated 20-skill catalogue.

The application uses deterministic weighted scoring across 30 O*NET-derived occupational roles.

The current algorithm uses normalized skill relevance and available experience signals, with appropriate redistribution of weights for scoring components not covered by the present catalogue.

Each recommendation includes an explanation and relevant limitations.

Career matching scores are experimental profile-alignment estimates, not validated hiring probabilities.

### Career Resources, Projects, Trends and SDGs

The application provides additional guidance through versioned cached datasets:

- **Learning Roadmaps:** Curated free learning resources for missing or important skills, with source-provided or clearly labelled team-estimated study hours.
- **Portfolio Projects:** Seventeen project records across eight of the thirty occupational roles, based on linked public datasets and learning resources.
- **Technology Trends:** Cached, dated GitHub developer-activity signals covering twelve skills. These signals are not live GitHub queries and do not represent hiring demand.
- **SDG Mapping:** Occupational roles and skills are linked to relevant United Nations Sustainable Development Goals with brief explanations.

The application does not claim that resource estimates or trend signals represent verified employment outcomes.

---

## Components

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS | Single-page application; backend communication through `frontend/src/lib/api.ts` |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy | API endpoints and application services under `backend/app/` |
| Database | SQLite | Stores student profiles; persistence across Replit restarts has not been independently verified |
| Cached Data | Versioned JSON files under `backend/app/data/cached/` | 30 roles, 20 core skills, learning resources, portfolio projects, SDG mappings and trend snapshots |
| CV Extraction — OpenRouter | Z.ai GLM-5.3 FlashX (`z-ai/glm-5.3-flashx`) | Configurable extraction provider implemented in `backend/app/services/glm_client.py` |
| CV Extraction — RunPod | Z.ai GLM-5.3 via RunPod Public Endpoint | Original CV extraction provider retained in code |
| Semantic Matching — RunPod | `sentence-transformers/all-MiniLM-L6-v2` | Separate RunPod Serverless embedding worker |
| Career Scoring | Deterministic weighted matching algorithm | Transparent explanations, skill gaps and responsible-AI caveats |
| Hosting | Replit Autoscale Deployment | https://mustaqbal-ai.replit.app |

### Related Implementation Files

- `backend/app/services/glm_client.py` — CV extraction provider integration.
- `backend/app/services/cv_extraction_service.py` — CV extraction service logic.
- `backend/app/services/hussain_matching/` — Matching engine and RunPod integration.
- `runpod-worker/` — RunPod Serverless embedding worker implementation.
- `runpod/README.md` — RunPod integration documentation.
- `docs/proof/runpod/` — Deployment screenshots and usage evidence.
- `backend/app/core/config.py` — Backend configuration.

---

## Application Configuration

The backend uses environment variables to select data sources, matching behavior and the CV extraction provider.

### Catalogue Configuration

`CATALOG_MODE` supports:

- `fixture` — Illustrative development/test catalogue.
- `cached` — Versioned occupational catalogue and related cached resources.

The deployed application was previously verified to expose the 30-role cached catalogue.

### Matching Configuration

`MATCHING_MODE` supports:

- `fixture` — Illustrative matching mode.
- `hussain` — Deterministic career matching algorithm with optional RunPod semantic similarity.

Semantic matching is available only when the relevant backend adapter is active and the RunPod embedding service is configured and reachable.

### CV Extraction Provider Configuration

| Environment Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | Selects `openrouter` or `runpod` |
| `LLM_API_KEY` | OpenRouter API credential, stored securely server-side |
| `LLM_BASE_URL` | OpenRouter API base URL when using OpenRouter |
| `LLM_MODEL` | Configured CV extraction model |
| `LLM_TIMEOUT_SECONDS` | Configurable timeout where supported |
| `RUNPOD_API_KEY` | RunPod authentication credential |
| `RUNPOD_ENDPOINT_ID` | RunPod semantic embedding endpoint ID |
| `RUNPOD_GLM_READ_TIMEOUT_SECONDS` | Read timeout for the original RunPod GLM extraction path |

Example provider configuration (no real credentials):

```dotenv
CATALOG_MODE=cached
MATCHING_MODE=hussain

LLM_PROVIDER=openrouter
LLM_API_KEY=YOUR_OPENROUTER_API_KEY
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=z-ai/glm-5.3-flashx

RUNPOD_API_KEY=YOUR_RUNPOD_API_KEY
RUNPOD_ENDPOINT_ID=f0phohhegtydji
RUNPOD_GLM_READ_TIMEOUT_SECONDS=40
```

For the existing RunPod CV extraction path, use `LLM_PROVIDER=runpod` with the supported RunPod configuration.

API credentials must be stored in backend/deployment secrets and must never be committed to GitHub or exposed in frontend code.

The CV extraction provider and semantic embedding provider are separate integrations. Selecting OpenRouter for CV extraction does not disable RunPod semantic matching.

---

## Known Architectural Limitations

- **Experimental scoring:** Career scores estimate profile alignment and are not validated predictions of employment or hiring outcomes.
- **Limited skill coverage:** The current catalogue includes 20 core skills across 30 occupations. Some recommendations may have limited coverage.
- **Limited project coverage:** Portfolio projects currently cover eight of thirty roles.
- **Semantic matching availability:** RunPod embedding services may experience cold starts, connectivity issues or credential-related errors. Exact-skill matching remains available as a fallback.
- **AI extraction accuracy:** GLM-based CV extraction may misinterpret or omit resume information. Student confirmation is mandatory.
- **Provider latency:** AI extraction response times depend on the selected model, upstream provider, network conditions and configured timeouts.
- **Cached trends:** Trend snapshots measure GitHub developer activity, not live market demand or employment growth.
- **Database persistence:** SQLite persistence across Replit restarts and redeployments has not been verified.
- **Third-party processing:** Extracted CV text may be transmitted to the configured external AI inference provider. Provider-specific privacy and retention terms must be disclosed in the Technical & Tools Declaration.

---

## Testing and Validation

### OpenRouter CV Extraction

Mohammad's development benchmark used Z.ai GLM-5.3 FlashX through OpenRouter.

Reported results:

- 15 extraction requests across five sample CVs.
- 100% successful responses in the benchmark sample.
- Approximately 2.2 seconds median extraction latency.
- No reported truncation after tuning the model configuration.

These results describe a development benchmark and do not guarantee identical latency or success rates in production.

### RunPod Semantic Matching

The team's RunPod Serverless worker has been deployed and tested using the `all-MiniLM-L6-v2` embedding model.

Recorded RunPod evidence is available in:

- `docs/proof/runpod/README.md`
- `docs/proof/runpod/live-run.md`
- `submission/SDC2026_CodeBlack_Runpod_POU.pdf`

A previous single live test of the Replit application returned degraded semantic matching. That observation does not establish permanent RunPod unavailability; the deployed credentials and configuration require separate verification.

### Application Testing

Backend regression tests, frontend lint/build checks, RunPod worker unit tests and OpenRouter extraction tests have been executed on separate development branches.

A complete test run against the final combined integration and deployed configuration remains required before declaring the final application production-validated.

---

## TODO — Final Submission Verification

- [ ] Verify the final deployed `LLM_PROVIDER` and CV extraction model.
- [ ] Confirm OpenRouter GLM-5.3 FlashX is active on the live Replit application if selected as the final provider.
- [ ] Confirm `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID=f0phohhegtydji` are configured in the published deployment.
- [ ] Verify RunPod semantic matching with the "Database Querying" → SQL acceptance test.
- [ ] Confirm the deployed backend uses Hussain's RunPod-enabled matching adapter.
- [ ] Run full regression tests on the final integrated source snapshot.
- [ ] Update the Technical & Tools Declaration to include OpenRouter, model/provider selection, API access tier and third-party CV processing.
- [ ] Verify the README, architecture documentation and final PDF declarations describe the same deployed implementation.
- [ ] Add an architecture diagram image if required by the submission.

---

## Responsible AI Statement

Mustaqbal AI is an educational career exploration prototype. It does not predict hiring outcomes or guarantee employment.

AI services support CV information extraction and semantic skill interpretation. Career ranking is generated by an explainable scoring algorithm, and students must review and confirm AI-extracted information before recommendations are produced.

The application uses O*NET-derived occupational information, clearly discloses limitations and provides fallback behavior when external AI integrations are unavailable.
