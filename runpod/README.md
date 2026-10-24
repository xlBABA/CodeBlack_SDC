# RunPod usage — entry point

Mustaqbal AI uses **two separate RunPod integrations**. They use different endpoints, different models,
different code paths, and fail independently — never conflate them.

| | CV extraction | Optional embedding similarity |
|---|---|---|
| Model | Z.ai **GLM-5.3** (chat/LLM) | `sentence-transformers/all-MiniLM-L6-v2` |
| Endpoint type | RunPod **Public Endpoint** (OpenAI-compatible), ID `b1dd8hy2hqo1nb` | RunPod **Serverless** endpoint, ID `f0phohhegtydji` |
| What it does | Reads extracted CV PDF text and drafts a structured profile (education, skills, projects, experience) for the student to review and confirm | Embeds a skill name/phrase so the matcher can give partial credit for a close-but-not-exact skill, or interpret free text that isn't in the 20-skill catalogue |
| Client code | `backend/app/services/glm_client.py` | `backend/app/services/hussain_matching/runpod_client.py` |
| Settings | `RUNPOD_API_KEY`, `RUNPOD_GLM_BASE_URL`, `RUNPOD_GLM_MODEL` (`backend/app/core/config.py`) | `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT_ID` |
| Worker we deployed ourselves? | No — GLM-5.3 is a RunPod-hosted public endpoint we call as a client | **Yes** — see `../runpod-worker/`, our own Dockerfile + handler |
| On failure | 30 s timeout falls back to manual profile entry; nothing is silently guessed | Falls back to exact skill matching only; every affected match is labelled `Semantic matching unavailable; exact skill matching only (degraded)` — never silently guessed |
| Called on every request? | Only when a student uploads a CV PDF (`POST /api/v1/cv/parse`) | Only when `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` are both set and the endpoint is reachable; `MATCHING_MODE=hussain` runs fully offline otherwise |

## The embedding worker we deployed (`../runpod-worker/`)

Full deployment instructions, GitHub-integration build steps, and a local no-GPU test path are in
[`../runpod-worker/README.md`](../runpod-worker/README.md). That worker was deployed and live-tested
on RunPod Serverless on 2026-10-23 (endpoint `f0phohhegtydji`) — see
[`../docs/proof/runpod/README.md`](../docs/proof/runpod/README.md) and
[`../docs/proof/runpod/live-run.md`](../docs/proof/runpod/live-run.md) for the full evidence (screenshots,
request IDs, cold/warm timings, and a live demonstration of the fallback path). This work and its
documentation are Hussain's (AI matching & RunPod lead); brought into this branch from
`origin/feature/hussain-matching` without modification.

## GLM-5.3 CV extraction

Implemented in `backend/app/services/glm_client.py` and `backend/app/services/cv_extraction_service.py`,
exposed via `POST /api/v1/cv/parse` (see `backend/CV_UPLOAD_INTEGRATION.md` for the request/response
shape). The CV's extracted text is truncated to 12,000 characters before it reaches the model; the
request times out after 30 seconds and falls back to manual entry. A skill is only added to the draft if
GLM-5.3 can point to a short, exact quote in the CV text that supports it — the student still reviews and
confirms everything before it is used for matching.

**No live-deployment proof screenshots exist for this integration** (unlike the embedding worker above).
The code is implemented and unit-tested with mocked HTTP responses (`backend/tests/test_cv_parse.py`),
and `submission/SDC2026_CodeBlack_Runpod_POU.pdf` documents that the RunPod sponsor credit funds both
this endpoint and the embedding worker — but a dedicated live-request screenshot for GLM-5.3 specifically
is not currently part of this repository.

**TODO (team):** if judges require it, add a GLM-5.3-specific proof screenshot (a completed `/v1/chat/completions`
request against `b1dd8hy2hqo1nb`, with the API key hidden) alongside the embedding worker's evidence.

## What is actually active on the live deployment right now

- `CATALOG_MODE=cached` and the 30-role catalogue are confirmed live (verified by GET requests to
  `/api/v1/sdgs/{role_id}` for roles outside the original 8).
- **This session made no POST calls to the live deployment** (deliberately, to avoid any risk of a paid
  RunPod call), so it independently verified nothing about RunPod's live state beyond what
  `submission/SDC2026_CodeBlack_Replit_POU.pdf` documents — that the RunPod credentials are stored in
  Replit Secrets, which confirms configuration, not a confirmed successful live call.
- **Jawad separately made one real POST test** against the live deployment on 2026-10-24 at ~19:43 UTC
  (`POST /careers/match`/`/scenarios/simulate`/`/roadmaps/generate`/`/projects/recommend` with an
  invented profile, no CV upload — see `docs/prd-inputs-jawad.md` and
  `docs/tools-declaration-inputs.md`). In that one test, **every match was labelled "Semantic matching
  unavailable; exact skill matching only (degraded)"** — i.e. semantic/RunPod matching was off (either
  unconfigured or unreachable) at that moment.
- **This is a single-test, point-in-time finding, not a confirmed permanent state.** RunPod credentials
  can be added, removed, or temporarily unreachable independently of a deployment; Jawad's test proves
  only what was true at that one timestamp. Do not state in any submission material that the optional
  embedding service is confirmed active — or confirmed permanently inactive — in production beyond
  this one dated observation.
