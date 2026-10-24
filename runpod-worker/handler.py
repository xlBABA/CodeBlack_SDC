"""RunPod Serverless worker: texts -> sentence embeddings.

Input : {"texts": ["data visualization", ...]}   (1 to 256 texts, 1 to 200 chars each)
Output: {"embeddings": [[...], ...], "model": "<model name>", "dim": 384}
Invalid input returns {"error": "<reason>"}, which RunPod reports as a failed job.

The model is loaded once at worker startup (see the __main__ block), never per request.
runpod and sentence_transformers are imported lazily so the handler can be unit
tested without either installed (see test_handler.py).
"""
from __future__ import annotations

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MAX_TEXTS = 256
MAX_CHARS = 200

_model = None


def load_model():
    """Load the embedding model into the module-level slot. Called once at startup."""
    global _model
    from sentence_transformers import SentenceTransformer

    _model = SentenceTransformer(MODEL_NAME)  # uses the GPU when one is available
    return _model


def set_model(model) -> None:
    """Install a model object with .encode(texts, normalize_embeddings=True) (tests)."""
    global _model
    _model = model


def validate_input(job_input) -> list[str]:
    """Return the validated list of texts or raise ValueError with a clear message."""
    if not isinstance(job_input, dict):
        raise ValueError('input must be an object like {"texts": ["..."]}')
    texts = job_input.get("texts")
    if not isinstance(texts, list):
        raise ValueError('input.texts must be a list of strings')
    if not texts:
        raise ValueError("input.texts must contain at least 1 text")
    if len(texts) > MAX_TEXTS:
        raise ValueError(f"too many texts: {len(texts)} (maximum {MAX_TEXTS})")
    for i, text in enumerate(texts):
        if not isinstance(text, str):
            raise ValueError(f"texts[{i}] must be a string, got {type(text).__name__}")
        if not text.strip():
            raise ValueError(f"texts[{i}] is empty")
        if len(text) > MAX_CHARS:
            raise ValueError(f"texts[{i}] is too long: {len(text)} characters (maximum {MAX_CHARS})")
    return texts


def handler(job: dict) -> dict:
    try:
        texts = validate_input((job or {}).get("input"))
    except ValueError as exc:
        return {"error": str(exc)}
    if _model is None:
        return {"error": "model is not loaded"}

    vectors = _model.encode(texts, normalize_embeddings=True)
    embeddings = [[round(float(x), 6) for x in vec] for vec in vectors]
    return {"embeddings": embeddings, "model": MODEL_NAME, "dim": len(embeddings[0])}


if __name__ == "__main__":
    import runpod

    load_model()  # once, before the worker starts taking jobs
    runpod.serverless.start({"handler": handler})
