"""CV extraction LLM client (OpenAI-compatible chat completions).

Deliberately separate from app/services/hussain_matching/runpod_client.py
— that module is Hussain's embedding provider (RUNPOD_ENDPOINT_ID=
f0phohhegtydji) and is never touched or imported here. The selected
extraction provider's credentials and endpoint are passed in by
cv_extraction_service.py; embedding configuration is never read here.

The API key is read fresh from Settings for each call (never cached on
an instance, never logged, never included in any exception message or
log line below — only exception *type names* and bounded, generic
messages are logged). The request body (which contains the extracted
CV text) is likewise never logged.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from time import monotonic

import httpx

logger = logging.getLogger(__name__)

# Bounded input: a CV's extracted text is truncated before it ever
# reaches the prompt — requirement 2's "bounded input length". ~12k
# characters is generous for any real one-to-three-page CV while
# keeping the request small and the cost/latency predictable.
MAX_INPUT_CHARS = 12_000
MAX_OUTPUT_TOKENS = 1_200
# OpenRouter's GLM-5.3 FlashX uses reasoning tokens, so reserve enough
# output headroom for both reasoning and the structured JSON response.
OPENROUTER_MAX_OUTPUT_TOKENS = 2_500
REQUEST_TIMEOUT_SECONDS = 30.0
# httpx applies this to each connect/read/write/pool phase, NOT total duration.

_SYSTEM_PROMPT = (
    "You extract structured data from a student's CV/resume text. "
    "Return ONLY a single JSON object (no prose, no markdown fences) "
    "with exactly these top-level keys: name, summary, education, "
    "skills, projects, experience, certifications. "
    "If a whole section is not present in the text, use an empty array "
    "for it — never null, and never omit the key. "
    "education is an array of objects, each optionally with institution, "
    "degree, field_of_study, start_date, end_date (all plain strings). "
    "experience is an array of objects, each optionally with role, "
    "organization, start_date, end_date, description (all plain strings). "
    "projects is an array of objects; every object you include MUST have "
    "a non-empty string \"title\" — if you cannot give a title, omit that "
    "project entirely rather than submitting one without a title. "
    "certifications is an array of objects; every object you include MUST "
    "have a non-empty string \"name\" — if you cannot give a name, omit "
    "that certification entirely rather than submitting one without one. "
    "skills is an array of objects, each with EXACTLY two keys: "
    '"name" (the skill exactly as written in the CV, a plain string) and '
    '"evidence" (a SHORT, word-for-word quote copied directly from the '
    "CV text that shows this skill — one short phrase, not a full "
    "sentence or paragraph; never paraphrase or summarize it, copy the "
    "exact substring). Never include a skill_id, proficiency, or rating "
    "for any skill — those are not your job. If you cannot find a short "
    "exact quote in the text supporting a skill, do not include that "
    "skill at all; never guess, paraphrase, or reuse a quote for a skill "
    "it does not actually support. "
    "Use null or an empty array for anything not clearly present in the "
    "text. Never invent a qualification, employer, date, or skill that "
    "is not actually stated in the text. If the text is too short or "
    "unclear to extract a field, leave it empty rather than guessing."
)


class GlmExtractionError(Exception):
    """GLM could not be reached or did not return usable output. Carries
    only a safe, generic reason — never the prompt, the response body,
    or any credential."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


@dataclass
class GlmExtractionResult:
    raw_json: dict


def _build_payload(cv_text: str, model: str, provider: str = "runpod") -> dict:
    truncated = cv_text[:MAX_INPUT_CHARS]
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": truncated},
        ],
        "max_tokens": MAX_OUTPUT_TOKENS,
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }
    if provider == "openrouter":
        payload["max_tokens"] = OPENROUTER_MAX_OUTPUT_TOKENS
        payload["reasoning"] = {"effort": "low"}
    else:
        # Best-effort: honored by models/gateways that support it
        # (requirement 2: "low reasoning effort ... where supported"),
        # silently ignored otherwise — never required for correctness.
        payload["reasoning_effort"] = "low"
    return payload


def extract_cv_fields(
    cv_text: str,
    *,
    api_key: str,
    base_url: str,
    model: str,
    read_timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
    client: httpx.Client | None = None,
    timeout_seconds: float | None = None,
    provider: str = "runpod",
    key_name: str = "RUNPOD_API_KEY",
) -> GlmExtractionResult:
    """Calls the selected OpenAI-compatible extraction endpoint. Raises
    GlmExtractionError (never a raw httpx/JSON exception) on any
    timeout, network error, non-2xx response, or malformed/non-JSON
    reply — the caller (cv_extraction_service.py) treats every one of
    these identically: fall back to manual review, never fabricate a
    result (requirement 6)."""
    if not api_key:
        raise GlmExtractionError("The extraction API key is not configured.")
    if not cv_text.strip():
        raise GlmExtractionError("No text was provided to extract from.")

    payload = _build_payload(cv_text, model, provider)
    url = f"{base_url.rstrip('/')}/chat/completions"
    owns_client = client is None
    timeout = (
        httpx.Timeout(timeout_seconds)
        if timeout_seconds is not None
        else httpx.Timeout(
            connect=30.0, read=read_timeout_seconds, write=30.0, pool=30.0,
        )
    )
    http_client = client if client is not None else httpx.Client(timeout=timeout)
    started = monotonic()
    try:
        response = http_client.post(
            url,
            json=payload,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
    except httpx.TimeoutException as exc:
        logger.warning(
            "GLM timeout category=%s elapsed_ms=%.1f connect_timeout_s=%.1f "
            "read_timeout_s=%.1f write_timeout_s=%.1f pool_timeout_s=%.1f input_chars=%d",
            type(exc).__name__, (monotonic() - started) * 1000,
            timeout.connect, timeout.read, timeout.write, timeout.pool,
            len(payload["messages"][1]["content"]),
        )
        raise GlmExtractionError("The extraction service timed out.") from exc
    except httpx.HTTPError as exc:
        logger.warning("GLM network failure category=%s elapsed_ms=%.1f",
                       type(exc).__name__, (monotonic() - started) * 1000)
        raise GlmExtractionError("The extraction service could not be reached.") from exc
    finally:
        if owns_client:
            http_client.close()

    logger.log(
        logging.WARNING if response.status_code >= 400 else logging.INFO,
        "GLM response status=%d elapsed_ms=%.1f input_chars=%d",
        response.status_code, (monotonic() - started) * 1000,
        len(payload["messages"][1]["content"]),
    )
    if response.status_code == 401 or response.status_code == 403:
        logger.warning("GLM request rejected: HTTP %d (check %s)", response.status_code, key_name)
        raise GlmExtractionError("The extraction service rejected the request.")
    if response.status_code >= 400:
        logger.warning("GLM request failed: HTTP %d", response.status_code)
        raise GlmExtractionError(f"The extraction service returned an error (HTTP {response.status_code}).")

    try:
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        logger.warning("GLM response was not usable (%s)", type(exc).__name__)
        raise GlmExtractionError("The extraction service returned an unreadable result.") from exc

    if not isinstance(parsed, dict):
        raise GlmExtractionError("The extraction service returned an unexpected result shape.")

    return GlmExtractionResult(raw_json=parsed)
