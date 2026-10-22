# Tools declaration: Hussain (AI matching)

Scope: `services/matching/` and `runpod-worker/`. Licences were read from the actual model card or
package metadata on 2026-10-21 (sources in the last column), not written from memory.
Related log: `AI_USAGE_LOG.md`.

| Tool | Version / identifier | Licence | Used for | Where | Source of the licence information |
|---|---|---|---|---|---|
| **all-MiniLM-L6-v2** (embedding model) | `sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions, snapshot `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` | **Apache-2.0** | Turning skill names and aliases into vectors; cosine similarity gives partial credit for related skills (threshold 0.60) | `services/matching/embeddings.py`; baked into the `runpod-worker` Docker image at build time | Model card front matter in the downloaded snapshot (`license: apache-2.0`). The card says it is `nreimers/MiniLM-L6-H384-uncased` fine-tuned on more than 1 billion sentence pairs; the training datasets it lists were **not** individually reviewed |
| **sentence-transformers** (library) | 6.2.0 | **Apache-2.0** | Loading the model and `encode()` | `runpod-worker/handler.py` (always); `services/matching/embeddings.py` (optional, lazy import; tests skip without it) | Wheel `METADATA`: `License-Expression: Apache-2.0`; the wheel ships `LICENSE` and `NOTICE.txt` |
| **runpod** (Python SDK) | 1.12.0 | **MIT** | `runpod.serverless.start` in the worker. The matching client does **not** use the SDK; it calls the HTTP API with `urllib` | `runpod-worker/handler.py` | Wheel `METADATA`: `License: MIT License`, classifier `OSI Approved :: MIT License`; wheel ships `LICENSE` |
| **RunPod Serverless** (hosted GPU service) | Endpoint serving `runpod-worker/`; called at `https://api.runpod.ai/v2/<endpoint-id>/runsync` | Commercial hosted service; no code licence applies. Governed by RunPod's own terms, **not reviewed here** | Running the embedding model on GPU, per the rule that GPU-dependent work uses RunPod | `services/matching/runpod_client.py`, `runpod-worker/` | n/a. **Status: deployed and verified on 2026-10-23.** Queue-based endpoint built from GitHub (`xlBABA/CodeBlack_SDC`, `feature/hussain-matching`, commit `f4e03e8`; an earlier build of the old Dockerfile failed), 1 GPU (24 GB). Test request `["SQL","Database Querying"]` returned COMPLETED, dim 384, delay 19.62 s (cold start), execution 345 ms. Proof: `proof/runpod/README.md` and screenshots. |
| **Claude Code** (AI coding assistant) | CLI 2.1.306, model Claude Sonnet 5.5 (`claude-sonnet-5-5`), used for the embeddings, calibration and RunPod work (log rows 3 and 4) | Proprietary product of Anthropic, not an open-source licence. Plan: Claude Pro. Terms: Anthropic Consumer Terms of Service (per Hussain; not verifiable from the installed binary) | Drafting and editing code, tests and documentation; every piece is listed in `AI_USAGE_LOG.md` with the human review and tests run | Embeddings, calibration, RunPod files; also committed the earlier matcher files | See Licence column |
| **Claude (claude.ai chat)** (AI assistant, not Claude Code) | Claude Opus 5.5, as reported by that chat session (per Hussain) | Proprietary product of Anthropic, not an open-source licence. Plan: Claude Pro. Terms: Anthropic Consumer Terms of Service (per Hussain) | Wrote the original matcher: normalizer, scoring v1, scenarios, matcher and backend adapter, with tests (log rows 1 and 2). Hussain reviewed it and ran the tests; the adapter was tested against Rehan's branch (115 backend tests passed, 4 endpoints returned 200, per Hussain) | `services/matching/` core files, delivered as `hussain-matching-v2.zip` | See Licence column |

## Other pinned dependencies of the worker
| Package | Version | Licence as listed on PyPI |
|---|---|---|
| torch | 2.14.1 | `Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT` (license expression) |
| transformers | 5.20.2 | `Apache 2.0 License` |

## Credentials and data
- The RunPod key and endpoint ID are read from `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID`. Only the names are committed (`services/matching/.env.example`); `.env` is git-ignored. The key is never logged.
- Only skill names and aliases (catalogue text) are sent to the endpoint. No student profiles or CVs are sent. Calibration pairs are fictional skill names.

## Not checked yet
- Licences of the datasets the embedding model was trained on (listed in its model card).
- Docker base image (`python:3.11-slim`), `pytest`, and the other transitive dependencies of the worker.
- RunPod's terms of service, and Anthropic's Consumer Terms of Service (stated by Hussain, not read here).
- A live run of the matcher's own client (`runpod_client.py`, `/runsync`) and the adapter fallback against the deployed endpoint; the proof covers the worker only (tests mock the HTTP calls).

## How the licences were checked
- Model: read `license:` from `README.md` in the local Hugging Face snapshot of `all-MiniLM-L6-v2`.
- `runpod`, `sentence-transformers`: `pip download --no-deps` of the pinned versions, then read `METADATA` and the bundled licence files inside the wheel.
- `torch`, `transformers`: PyPI JSON metadata for the pinned versions.
