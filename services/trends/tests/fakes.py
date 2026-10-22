"""Offline test doubles: no network, no real sleeping, no wall-clock reads."""
from __future__ import annotations

from services.trends.github_client import GitHubFetchError


class ScriptedTransport:
    """Returns one canned response per call, in order. Raises on overrun so a
    test cannot silently reuse a stale response."""

    def __init__(self, responses: list[dict | Exception]):
        self._responses = list(responses)
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, url: str, headers: dict) -> dict:
        self.calls.append((url, headers))
        if not self._responses:
            raise AssertionError("ScriptedTransport called more times than scripted")
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def github_response(total_count: int, incomplete: bool = False) -> dict:
    return {"total_count": total_count, "incomplete_results": incomplete, "items": []}


def http_error(message: str = "API rate limit exceeded") -> GitHubFetchError:
    return GitHubFetchError(message)


class FakeClock:
    """Returns a fixed, scripted sequence of ISO timestamps (one per call)."""

    def __init__(self, timestamps: list[str]):
        self._timestamps = list(timestamps)

    def __call__(self) -> str:
        if len(self._timestamps) == 1:
            return self._timestamps[0]
        return self._timestamps.pop(0)


def no_sleep(_seconds: float) -> None:
    """Sleep replacement for tests: does nothing, so tests run instantly."""
