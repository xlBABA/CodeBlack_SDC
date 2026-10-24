"""Milestone 11B: RunPod GLM-5.3 client (OpenAI-compatible chat completions).

Deliberately separate from app/services/hussain_matching/runpod_client.py
— that module is Hussain's embedding provider (RUNPOD_ENDPOINT_ID=
f0phohhegtydji) and is never touched or imported here. This module only
ever reads RUNPOD_API_KEY and the two new RUNPOD_GLM_* settings
(app/core/config.py) — or, with LLM_PROVIDER=openrouter, whatever
LLM_API_KEY/LLM_BASE_URL/LLM_MODEL cv_extraction_service.py passes in
(the same OpenAI-compatible request; see _build_payload for the two
providers' differences).

The API key is read fresh from Settings for each call (never cached on
an instance, never logged, never included in any exception message or
log line below — only exception *type names* and bounded, generic
messages are logged). The request body (which contains the extracted
CV text) is likewise never logged.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

# Bounded input: a CV's extracted text is truncated before it ever
# reaches the prompt — requirement 2's "bounded input length". ~12k
# characters is generous for any real one-to-three-page CV while
# keeping the request small and the cost/latency predictable.
MAX_INPUT_CHARS = 12_000
MAX_OUTPUT_TOKENS = 1_200
# OpenRouter's z-ai/glm-5.3-flashx always reasons before answering; even at
# low effort it needs headroom so a long CV's JSON isn't cut off.
OPENROUTER_MAX_OUTPUT_TOKENS = 2_500
REQUEST_TIMEOUT_SECONDS = 30.0

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


_JSON_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)


def _strip_json_fence(content: str) -> str:
    """Models sometimes wrap a JSON reply in a ```json ... ``` markdown
    fence despite being asked not to; unwrap it rather than discarding an
    otherwise valid reply. Anything else (including a non-string, e.g. a
    null content) is returned unchanged for json.loads to reject."""
    if not isinstance(content, str):
        return content
    stripped = content.strip()
    match = _JSON_FENCE.match(stripped)
    return match.group(1) if match else stripped


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
        # OpenRouter's own reasoning control (not reasoning_effort): low
        # effort keeps reasoning tokens from crowding out the JSON answer.
        payload["reasoning"] = {"effort": "low"}
        payload["max_tokens"] = OPENROUTER_MAX_OUTPUT_TOKENS
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
    client: httpx.Client | None = None,
    timeout: float = REQUEST_TIMEOUT_SECONDS,
    provider: str = "runpod",
    key_name: str = "RUNPOD_API_KEY",
) -> GlmExtractionResult:
    """Calls RunPod's OpenAI-compatible GLM-5.3 endpoint. Raises
    GlmExtractionError (never a raw httpx/JSON exception) on any
    timeout, network error, non-2xx response, or malformed/non-JSON
    reply — the caller (cv_extraction_service.py) treats every one of
    these identically: fall back to manual review, never fabricate a
    result (requirement 6)."""
    if not api_key:
        raise GlmExtractionError("RunPod API key is not configured.")
    if not cv_text.strip():
        raise GlmExtractionError("No text was provided to extract from.")

    payload = _build_payload(cv_text, model, provider)
    url = f"{base_url.rstrip('/')}/chat/completions"
    owns_client = client is None
    http_client = client or httpx.Client(timeout=timeout)
    try:
        response = http_client.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
    except httpx.TimeoutException as exc:
        logger.warning("GLM request timed out after %.0fs", timeout)
        raise GlmExtractionError("The extraction service timed out.") from exc
    except httpx.HTTPError as exc:
        logger.warning("GLM request failed (%s)", type(exc).__name__)
        raise GlmExtractionError("The extraction service could not be reached.") from exc
    finally:
        if owns_client:
            http_client.close()

    if response.status_code == 401 or response.status_code == 403:
        logger.warning("GLM request rejected: HTTP %d (check %s)", response.status_code, key_name)
        raise GlmExtractionError("The extraction service rejected the request.")
    if response.status_code >= 400:
        logger.warning("GLM request failed: HTTP %d", response.status_code)
        raise GlmExtractionError(f"The extraction service returned an error (HTTP {response.status_code}).")

    try:
        body = response.json()
        choice = body["choices"][0]
        if choice.get("finish_reason") == "length":
            logger.warning("GLM reply was cut off at max_tokens (finish_reason=length)")
        content = choice["message"]["content"]
        parsed = json.loads(_strip_json_fence(content))
    except (KeyError, IndexError, TypeError, ValueError, AttributeError) as exc:
        logger.warning("GLM response was not usable (%s)", type(exc).__name__)
        raise GlmExtractionError("The extraction service returned an unreadable result.") from exc

    if not isinstance(parsed, dict):
        raise GlmExtractionError("The extraction service returned an unexpected result shape.")

    return GlmExtractionResult(raw_json=parsed)
