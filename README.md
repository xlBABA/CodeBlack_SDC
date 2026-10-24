# CodeBlack_SDC — Mustaqbal AI

Career-planning prototype for students: compare your skills with 30 real O*NET roles, see dated GitHub developer-activity signals for those skills (not hiring demand), and get a learning path with hours.

- `backend/` — FastAPI API under `/api/v1` (Python 3.11+). Serves `frontend/dist` too when it has been built.
- `frontend/` — Vite + React app.

## Run locally

```bash
cd backend
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt
CATALOG_MODE=cached MATCHING_MODE=hussain .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

cd ../frontend
npm install
npm run dev        # http://localhost:5173, proxies /api to the backend
```

Set environment variables in the shell that starts the backend (see `backend/.env.example` for every name). The embedding variables are read from the process environment, not only from `.env`.

| Variables | Purpose |
|---|---|
| `CATALOG_MODE`, `MATCHING_MODE`, `ENABLE_FIXTURES` | Real cached catalogue and matcher (`cached`, `hussain`) or fixtures |
| `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS` | CV extraction LLM. `openrouter` uses only these; `runpod` (default) uses `RUNPOD_API_KEY`, `RUNPOD_GLM_BASE_URL`, `RUNPOD_GLM_MODEL` |
| `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT_ID` | Optional embeddings for semantic skill matching |

Tests: `cd backend && .venv/bin/python -m pytest`. Frontend checks: `npm run build` and `npm run lint`.

## AI services

- **CV extraction:** OpenRouter with `z-ai/glm-5.3-flashx` (or RunPod GLM-5.3). The model only drafts a profile from the CV text. Every skill must be quoted from the CV, and the student confirms everything. Results: `docs/cv-llm-benchmark.md`.
- **Embeddings:** RunPod Serverless, `all-MiniLM-L6-v2`, for optional partial credit between closely related skills.
- Scores come from a fixed, documented formula, never from a language model. More detail: `docs/tools-declaration-inputs.md`.

## Data credit and licence

Role and skill data: Source: O*NET OnLine by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA), licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).

Code: Apache License 2.0 (see `LICENSE`).
