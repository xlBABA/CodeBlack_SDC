"""FuturePath AI trend signal service (owner: Jawad).

Ingests dated, updatable skill signals from the GitHub Search API and turns
them into contract-shaped TrendSignal dicts. See README.md for the method
and the skill coverage table.
"""
from .queries import COVERED_SKILLS, NOT_COVERED_SKILLS
from .github_client import GitHubTrendClient, GitHubFetchError, WindowCount
from .aggregate import compute_direction, build_trend_signal
from .snapshot import load_snapshot, save_snapshot
from .ingest import get_trends, refresh_all, refresh_skill

__all__ = [
    "COVERED_SKILLS",
    "NOT_COVERED_SKILLS",
    "GitHubTrendClient",
    "GitHubFetchError",
    "WindowCount",
    "compute_direction",
    "build_trend_signal",
    "load_snapshot",
    "save_snapshot",
    "refresh_skill",
    "refresh_all",
    "get_trends",
]
