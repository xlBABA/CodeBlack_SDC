"""GitHub Search API client: counts repositories CREATED within a date window
and tagged with a given topic. One call = one (topic, window) count.

Rate limits (GitHub Search endpoint specifically, not the general API):
unauthenticated ~10 requests/minute, ~30/minute with a token. We throttle to
stay under that; the token (optional) comes from the GITHUB_TOKEN env var
(see .env.example) and is never logged or included in error messages beyond
"token present/absent".

The real HTTP call is isolated in `_default_transport` and injected via the
`transport` parameter, so tests run fully offline with a fake transport.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

SEARCH_URL = "https://api.github.com/search/repositories"
UNAUTH_MIN_INTERVAL_SECONDS = 6.5  # ~9/min, under the ~10/min unauthenticated limit
AUTH_MIN_INTERVAL_SECONDS = 2.1    # ~28/min, under the ~30/min authenticated limit

Transport = Callable[[str, dict], dict]


class GitHubFetchError(Exception):
    """Raised for any failed or unusable GitHub response. Callers must fall
    back to a saved snapshot - never invent a count."""


@dataclass(frozen=True)
class WindowCount:
    topic: str
    start: str  # YYYY-MM-DD, inclusive
    end: str    # YYYY-MM-DD, inclusive
    total_count: int
    incomplete: bool  # GitHub's own "incomplete_results" flag
    retrieved_at: str  # ISO 8601 UTC, e.g. 2026-10-21T12:00:00Z


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_transport(url: str, headers: dict) -> dict:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise GitHubFetchError(f"HTTP {e.code}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise GitHubFetchError(f"network error: {e.reason}") from e
    except json.JSONDecodeError as e:
        raise GitHubFetchError(f"non-JSON response: {e}") from e


class GitHubTrendClient:
    def __init__(
        self,
        token: str | None = None,
        transport: Transport = _default_transport,
        sleep_fn: Callable[[float], None] = time.sleep,
        clock: Callable[[], str] = _utcnow_iso,
    ):
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN")
        self._transport = transport
        self._sleep_fn = sleep_fn
        self._clock = clock
        self._last_call_monotonic: float | None = None

    def _throttle(self) -> None:
        interval = AUTH_MIN_INTERVAL_SECONDS if self.token else UNAUTH_MIN_INTERVAL_SECONDS
        now = time.monotonic()
        if self._last_call_monotonic is not None:
            elapsed = now - self._last_call_monotonic
            if elapsed < interval:
                self._sleep_fn(interval - elapsed)
        self._last_call_monotonic = time.monotonic()

    def fetch_window_count(self, topic: str, start: str, end: str) -> WindowCount:
        """Count repos tagged `topic` created in [start, end] (YYYY-MM-DD)."""
        self._throttle()
        query = f"topic:{topic} created:{start}..{end}"
        url = f"{SEARCH_URL}?q={urllib.parse.quote(query)}&per_page=1"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "futurepath-ai-trends",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        body = self._transport(url, headers)
        if "total_count" not in body:
            raise GitHubFetchError(f"unexpected response: {body.get('message', body)!r}")
        return WindowCount(
            topic=topic,
            start=start,
            end=end,
            total_count=int(body["total_count"]),
            incomplete=bool(body.get("incomplete_results", False)),
            retrieved_at=self._clock(),
        )
