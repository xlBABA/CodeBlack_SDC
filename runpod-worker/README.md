# runpod-worker: skill embeddings on RunPod Serverless

Serves `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) for `services/matching`.

| | |
|---|---|
| Input | `{"input": {"texts": ["data visualization", "dashboards"]}}` (1 to 256 texts, 1 to 200 characters each) |
| Output | `{"embeddings": [[...384 floats...], ...], "model": "sentence-transformers/all-MiniLM-L6-v2", "dim": 384}` |
| Bad input | `{"error": "<reason>"}`, for example `texts[1] is too long: 201 characters (maximum 200)` |

The model is loaded once when the worker starts (`load_model()` in the `__main__` block of `handler.py`),
and the Docker image downloads it at build time (`HF_HUB_OFFLINE=1` afterwards), so a cold start never
downloads anything. Vectors are L2-normalised.

## Test locally (no RunPod, no GPU, no model)
```
python -m pytest runpod-worker -q
```
`test_handler.py` calls `handler.handler(...)` with fake jobs and a fake model.

To try the real model on your machine (needs `pip install -r runpod-worker/requirements.txt`):
```
python -c "import sys; sys.path.insert(0, 'runpod-worker'); import handler; handler.load_model(); print(handler.handler({'input': {'texts': ['SQL', 'Database Querying']}})['dim'])"
```

## Deploy on RunPod Serverless

The `Dockerfile` was not built on the machine this was written on (no Docker installed there), so the
first build is the real test. Menu names below may differ slightly in the RunPod console.

### Option A: GitHub integration
1. Push this repo (the `runpod-worker/` folder) to GitHub and make sure the branch is pushed.
2. RunPod console, **Serverless**, **New Endpoint**, **GitHub Repo**. Connect GitHub and pick the repo and branch.
3. Set the Dockerfile path to `runpod-worker/Dockerfile` and the build context to `runpod-worker`.
4. Wait for the build to finish (the model download happens here).
5. Pick a GPU (a small one is enough, for example a 16 GB class card), **Active workers 0**,
   **Max workers 1**, idle timeout about 5 seconds, and deploy.

### Option B: Docker image
```
docker build -t <dockerhub-user>/futurepath-embeddings:1 runpod-worker
docker push <dockerhub-user>/futurepath-embeddings:1
```
Then **Serverless**, **New Endpoint**, **Custom source / Docker image**, enter
`<dockerhub-user>/futurepath-embeddings:1`, choose the same GPU and worker settings as above, and deploy.
(Use a fresh tag for each change; RunPod caches by tag.)

No secrets are needed inside the worker. Do not put the RunPod API key in the image.

### Create the API key and test the endpoint
1. RunPod console, **Settings**, **API Keys**, create a key (give it only the access it needs).
2. Set it in your shell and in `.env` (see `services/matching/.env.example`):
   ```
   RUNPOD_API_KEY=...        # keep secret
   RUNPOD_ENDPOINT_ID=...    # shown on the endpoint page
   ```
3. Test:
   ```
   curl -X POST "https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID/runsync" \
     -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" \
     -d '{"input": {"texts": ["SQL", "Database Querying"]}}'
   ```
   Expect `"status": "COMPLETED"` and `"dim": 384`. The first call after idle includes a cold start.

## Screenshots to take as proof
Hide or blur the API key in every screenshot.

1. **Endpoint page**: shows the **endpoint ID**, the endpoint name and status (Ready/Running).
2. **GPU type and worker settings**: the endpoint's configuration with the selected **GPU type**, min and max workers.
3. **Runtime**: **Requests** tab (or the request details) of a completed `runsync` call showing the **delay time**
   (queue plus cold start) and **execution time**. Take one cold and one warm request if you can.
4. **Response body**: the `curl` output showing `"status": "COMPLETED"`, `"model"` and `"dim": 384`
   (shorten the embeddings if the output is long).
5. **Worker logs** (optional): the log line from the worker start showing it is up, taken from the endpoint's **Logs** tab.
6. **End to end** (optional): a `/careers/match` response whose caveats do **not** contain
   "Semantic matching unavailable", next to one with the endpoint turned off that does.
