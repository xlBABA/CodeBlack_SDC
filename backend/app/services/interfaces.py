"""Adapter interfaces from contracts/API_CONTRACT.md ("Adapter interfaces" section).

These define the shape teammates' real providers (Hussain's matching/RunPod,
Jawad's trends/roadmaps/projects) must satisfy. No implementation lives here —
concrete fixture or real adapters are injected into routers via FastAPI
dependencies. Request/response payloads are left as `Any` because the full
StudentProfile/RoleMatch/TrendSignal DTOs are out of scope for this
foundation milestone.
"""
from typing import Any, Protocol


class MatchingProvider(Protocol):
    def match(
        self,
        profile: Any,
        roles: Any,
        scenario: Any,
        signals: Any,
    ) -> Any:
        """Return ranked RoleMatch results for a profile against the role catalog."""
        ...


class TrendProvider(Protocol):
    def latest(self, role_id: Any = None) -> Any:
        """Return the latest dated TrendSignal set, optionally filtered by role."""
        ...


class LLMProfileProvider(Protocol):
    def extract(self, text: str) -> Any:
        """Extract a validated StudentProfile from free text, with manual fallback."""
        ...


class RoadmapProvider(Protocol):
    def generate(self, profile: Any, role: Any, missing_skills: Any, resources: Any) -> Any:
        """Produce an ordered, resource-linked learning roadmap."""
        ...


class ProjectProvider(Protocol):
    def recommend(self, profile: Any, role: Any, skills: Any) -> Any:
        """Recommend role-relevant portfolio projects."""
        ...


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> Any:
        """Return embedding vectors (RunPod-backed or a deterministic local fallback)."""
        ...
