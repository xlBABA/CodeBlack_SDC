"""Reusable error helpers for future external provider integrations
(Hussain's real matcher, RunPod, an LLM provider). No network or real
provider code exists yet — this module only prepares the error-handling
surface so a future real call has a consistent, contract-compatible way
to report unavailability or timeout, distinct from invalid student input
(which stays a 422 VALIDATION_ERROR via the existing handler) or an
unknown resource (404, e.g. PROFILE_NOT_FOUND). Both helpers return a
plain AppError — they reuse the existing error envelope and exception
handler from app.core.errors, nothing new to register.
"""
from __future__ import annotations

from app.core.errors import AppError


def provider_unavailable(provider_name: str, reason: str) -> AppError:
    """A provider is configured/expected but has no working implementation
    or backing service right now (e.g. real mode requested, no real
    implementation exists). 503: the request itself was valid.

    details stays None (CLAUDE.md's error shape reserves a populated
    details for validation errors; every other AppError call site in this
    codebase — PROFILE_NOT_FOUND, ROLE_NOT_FOUND, PROJECT_NOT_FOUND,
    PROFILE_PERSISTENCE_ERROR — follows the same convention). The provider
    name and reason are carried in `message` instead.
    """
    return AppError(
        code="PROVIDER_UNAVAILABLE",
        message=f"{provider_name} is not available: {reason}",
        status_code=503,
    )


def provider_timeout(provider_name: str, timeout_seconds: float) -> AppError:
    """A provider call exceeded its configured timeout boundary. 504:
    distinct from 503 so callers can tell "down" apart from "too slow".

    details stays None — see provider_unavailable()'s docstring. The
    provider name and timeout value are carried in `message` instead.
    """
    return AppError(
        code="PROVIDER_TIMEOUT",
        message=f"{provider_name} did not respond within {timeout_seconds}s.",
        status_code=504,
    )
