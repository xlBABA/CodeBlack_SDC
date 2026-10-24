# RunPod proof: embedding worker deployed and tested

Own-account proof for `COMPLIANCE.md` (Participant Handbook §§9.3, 10.7): RunPod Serverless endpoint, GPU and runtime.
Date: 2026-10-23 MYT. Account owner: Hussain.

## What was deployed
| Item | Value |
|---|---|
| Endpoint name | `CodeBlack_SDC` |
| Endpoint type | Queue-based Serverless |
| Endpoint ID | `f0phohhegtydji` |
| Source | GitHub integration: `xlBABA/CodeBlack_SDC`, branch `feature/hussain-matching`, Dockerfile `runpod-worker/Dockerfile` |
| GPU | 24 GB class, 1 GPU (as shown on the endpoint page) |
| Worker code | `runpod-worker/handler.py` (model `sentence-transformers/all-MiniLM-L6-v2`, loaded once at startup, baked into the image at build time) |

## Builds (screenshot 3)
| Build | Result |
|---|---|
| Commit `f4e03e8` "Make runpod-worker Dockerfile build from the repo root" | **Completed** |
| Previous build, commit `61373a5` "Update AI usage log: confirm RunPod fallback pause and .env.example location" (old Dockerfile with `COPY` paths relative to `runpod-worker/`) | **Build Failed** |

The screenshot shows commit messages, not hashes; the hashes come from `git log`. The build log is not in the screenshots;
per Hussain, the failure was caused by the old `COPY` paths (relative to `runpod-worker/`). The fix in `f4e03e8` changed them to
start with `runpod-worker/`, because RunPod's GitHub integration builds with the repo root as context.

## Test request (screenshot 1)
Input: `{"input": {"texts": ["SQL", "Database Querying"]}}`

| Result | Value |
|---|---|
| Status | **COMPLETED** |
| Embedding size | `"dim": 384` |
| Delay time (queue + cold start) | **19.62 s** (`delayTime` 19616 ms) |
| Execution time | **345 ms** |
| Request ID | `7de2e7d8-32af-4344-a250-b8235f9ed794-e1` |
| Worker | `7m7rcmeirlyvbj` |

The model name (`sentence-transformers/all-MiniLM-L6-v2`) is returned in the `model` field of the handler output but is
below the visible part of the JSON in the screenshot. It is set in `runpod-worker/handler.py` and was also returned when the
handler was run locally.

## Endpoint overview (screenshot 2)
Status Ready, 0 running workers and 0 jobs waiting (scaled to zero between requests), request volume: 1 total, 1 completed,
0 retried, 0 failed. The page also shows "Rollout in progress, 4/5 (80%) of workers running the latest configuration" at the
time of the screenshot.

## Screenshots
| File | Shows |
|---|---|
| `1-request-completed.png` | Request Completed, delay 19.62 s, execution 345 ms, `dim` 384, input texts |
| `2-endpoint-overview.png` | Queue based, Ready, GitHub repo and branch, GPU count 1, GPU type 24 GB, endpoint ID |
| `3-build-completed.png` | Builds tab: Completed build and the earlier failed build |

**No API key appears in any screenshot.** The curl example on the overview page contains only the placeholder `YOUR_API_KEY`.
The endpoint ID is visible; it is not a credential, but calls to the endpoint need the API key, which is kept in
`RUNPOD_API_KEY` and never committed.

## Not covered by this proof
- The test request was made from the RunPod console, and the screenshot shows it fetched through the `/status/<id>` API. The matcher's own client
  (`services/matching/runpod_client.py`, which calls `/runsync`) has not yet been run against this live endpoint; its tests mock the HTTP calls.
- The backend adapter's fallback ("Semantic matching unavailable ... (degraded)") has been tested with mocked failures only.
- Only one request was made, so there is no warm-start timing. The 19.62 s delay is a single cold start.
