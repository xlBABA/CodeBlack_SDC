# Vendored verbatim from origin/feature/hussain-matching @ 61373a5 (owner: Hussain).
# Source: services/matching/runpod_client.py on that branch. Not modified from the original.
"""Embedding similarity served by a RunPod Serverless endpoint (see runpod-worker/).

    provider = RunPodEmbeddingProvider.from_catalogue(catalogue)   # reads the env vars below
    matcher = Matcher(normalizer, similarity=provider)

Environment variables (names only; never commit values, see .env.example):
    RUNPOD_API_KEY       RunPod API key
    RUNPOD_ENDPOINT_ID   ID of the deployed embedding endpoint

It is an EmbeddingProvider whose "model" calls POST {base}/{endpoint_id}/runsync, so
batching, caching, max-cosine over name and aliases, and `not_equivalent` behave
exactly as in embeddings.py. Each request has a timeout and is retried once on
transient failures (timeout, network error, HTTP 429/5xx, job still queued).
The API key is only sent in the Authorization header and never appears in logs
or error messages.
"""
from __future__ import annotations

import json
import logging
import math
import os
import re
import socket
import urllib.error
import urllib.request
from typing import Callable

from .embeddings import DEFAULT_MODEL, EmbeddingProvider

logger = logging.getLogger(__name__)

ENV_API_KEY = "RUNPOD_API_KEY"
ENV_ENDPOINT_ID = "RUNPOD_ENDPOINT_ID"
BASE_URL = "https://api.runpod.ai/v2"
MAX_TEXTS_PER_REQUEST = 256  # worker limits, see runpod-worker/handler.py
MAX_CHARS = 200
_ENDPOINT_ID = re.compile(r"^[A-Za-z0-9_-]+$")


class RunPodError(RuntimeError):
    """The RunPod call failed or returned something unusable."""


class RunPodConfigError(RunPodError):
    """Required environment variables are missing or invalid."""


class _TransientError(RunPodError):
    """Worth one retry: timeout, network error, HTTP 429/5xx, job still queued."""


def runpod_configured(env=None) -> bool:
    env = os.environ if env is None else env
    return bool((env.get(ENV_API_KEY) or "").strip() and (env.get(ENV_ENDPOINT_ID) or "").strip())


class _RunPodModel:
    """Duck-typed model: `.encode(texts)` -> list of vectors, via the endpoint."""

    def __init__(self, api_key: str, endpoint_id: str, *, expected_model: str = DEFAULT_MODEL,
                 timeout: float = 60.0, retries: int = 1, base_url: str = BASE_URL,
                 opener: Callable | None = None):
        if not _ENDPOINT_ID.match(endpoint_id):
            raise RunPodConfigError(f"{ENV_ENDPOINT_ID} has invalid characters")
        if not base_url.startswith("https://"):
            raise RunPodConfigError("base_url must start with https://")
        self._api_key = api_key
        self._url = f"{base_url.rstrip('/')}/{endpoint_id}/runsync"
        self._expected_model = expected_model
        self._timeout = timeout
        self._retries = max(0, retries)
        self._opener = opener

    def __repr__(self) -> str:  # never show the key
        return f"<_RunPodModel url={self._url}>"

    def encode(self, texts, **_ignored) -> list[list[float]]:
        texts = [t[:MAX_CHARS] for t in texts]
        vectors: list[list[float]] = []
        for start in range(0, len(texts), MAX_TEXTS_PER_REQUEST):
            vectors.extend(self._embed_batch(texts[start:start + MAX_TEXTS_PER_REQUEST]))
        return vectors

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        attempts = self._retries + 1
        for attempt in range(1, attempts + 1):
            try:
                return self._request_once(texts)
            except _TransientError as exc:
                if attempt == attempts:
                    raise RunPodError(f"RunPod request failed after {attempts} attempts: {exc}") from None
                logger.warning("RunPod request failed (attempt %d/%d): %s; retrying",
                               attempt, attempts, exc)
        raise AssertionError("unreachable")

    def _request_once(self, texts: list[str]) -> list[list[float]]:
        request = urllib.request.Request(
            self._url,
            data=json.dumps({"input": {"texts": texts}}).encode("utf-8"),
            headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        opener = self._opener or urllib.request.urlopen
        try:
            with opener(request, timeout=self._timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise RunPodError(f"authentication failed (HTTP {exc.code}); check {ENV_API_KEY}") from None
            if exc.code == 429 or exc.code >= 500:
                raise _TransientError(f"HTTP {exc.code}") from None
            raise RunPodError(f"HTTP {exc.code} from RunPod endpoint") from None
        except (TimeoutError, socket.timeout):
            raise _TransientError(f"timed out after {self._timeout:g}s") from None
        except (urllib.error.URLError, ConnectionError, OSError) as exc:
            raise _TransientError(f"network error ({type(exc).__name__})") from None
        return self._parse(raw, len(texts))

    def _parse(self, raw: bytes, expected_count: int) -> list[list[float]]:
        try:
            body = json.loads(raw)
        except ValueError:
            raise RunPodError("bad response: not valid JSON") from None
        if not isinstance(body, dict):
            raise RunPodError("bad response: expected a JSON object")

        status = body.get("status")
        if status in ("IN_QUEUE", "IN_PROGRESS"):
            raise _TransientError(f"job not finished (status {status})")
        if status != "COMPLETED":
            raise RunPodError(f"job did not complete (status {status!r}){self._detail(body.get('error'))}")

        output = body.get("output")
        if not isinstance(output, dict):
            raise RunPodError("bad response: missing output")
        if "error" in output:
            raise RunPodError(f"worker rejected the request{self._detail(output['error'])}")
        embeddings = output.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != expected_count:
            raise RunPodError(f"bad response: expected {expected_count} embeddings")
        model = output.get("model")
        if model is not None and model != self._expected_model:
            raise RunPodError(f"bad response: unexpected model {str(model)[:80]!r}")

        dim = len(embeddings[0]) if embeddings and isinstance(embeddings[0], list) else 0
        if dim == 0 or ("dim" in output and output["dim"] != dim):
            raise RunPodError("bad response: empty or inconsistent embedding size")
        for vec in embeddings:
            if (not isinstance(vec, list) or len(vec) != dim
                    or not all(isinstance(x, (int, float)) and not isinstance(x, bool)
                               and math.isfinite(x) for x in vec)):
                raise RunPodError("bad response: embeddings must be equal-length lists of numbers")
        return embeddings

    def _detail(self, error) -> str:
        if not error:
            return ""
        text = str(error)[:200].replace(self._api_key, "***")
        return f": {text}"


class RunPodEmbeddingProvider(EmbeddingProvider):
    """EmbeddingProvider backed by a RunPod Serverless endpoint.

    Raises RunPodConfigError if the key or endpoint ID is missing. Calling the
    provider (or `precompute()`) raises RunPodError if the endpoint cannot be used.
    """

    def __init__(self, texts_by_skill, *, api_key: str | None = None, endpoint_id: str | None = None,
                 timeout: float = 60.0, retries: int = 1, base_url: str = BASE_URL,
                 opener: Callable | None = None, model_name: str = DEFAULT_MODEL, **kwargs):
        api_key = (api_key if api_key is not None else os.environ.get(ENV_API_KEY, "")).strip()
        endpoint_id = (endpoint_id if endpoint_id is not None else os.environ.get(ENV_ENDPOINT_ID, "")).strip()
        if not api_key or not endpoint_id:
            raise RunPodConfigError(f"{ENV_API_KEY} and {ENV_ENDPOINT_ID} must both be set")
        model = _RunPodModel(api_key, endpoint_id, expected_model=model_name, timeout=timeout,
                             retries=retries, base_url=base_url, opener=opener)
        super().__init__(texts_by_skill, model_name=model_name, model=model, **kwargs)
