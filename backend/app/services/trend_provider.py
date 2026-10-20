"""Null TrendProvider — returns no signals until Jawad's real trend pipeline
(services/trends/**, GET /trends) exists. Satisfies
app.services.interfaces.TrendProvider so MatchingService can be wired today
and swapped for a real provider later with no route changes.
"""
from __future__ import annotations

from typing import Any


class NullTrendProvider:
    def latest(self, role_id: str | None = None) -> list[Any]:
        return []
