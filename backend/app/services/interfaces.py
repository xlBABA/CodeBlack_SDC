"""Adapter interfaces from contracts/API_CONTRACT.md ("Adapter interfaces" section).

These define the shape teammates' real providers (Hussain's matching/RunPod,
Jawad's trends/roadmaps/projects) must satisfy. No implementation lives here
— concrete fixture or real adapters are injected into routers via FastAPI
dependencies. Signatures stay `Any`-typed deliberately: pinning `roles` to
our fixture role_catalog.RoleFixture dataclass (or similar) would wrongly
couple this interface to our own fixture's internal shape, which Jawad's
real catalog has no obligation to match. The concrete expected shape of
each parameter is documented in prose on each method instead.

Milestone 6A status check — which of these are actually wired to a live
call site today (contracts/API_CONTRACT.md DTOs now exist, so this replaces
the earlier "DTOs are out of scope" note):

- MatchingProvider: IMPLEMENTED and consumed (FixtureMatchingProvider, via
  app.api.v1.endpoints.careers.get_matching_provider, reused by
  scenarios/roadmaps/projects).
- TrendProvider: IMPLEMENTED and consumed twice, by two different fixture
  classes — FixtureTrendProvider (GET /trends) and NullTrendProvider
  (used inside MatchingService, always returns no signals).
- RoadmapProvider, ProjectProvider: PROTOCOL MISMATCH — neither is actually
  implemented or called. Milestone 5's RoadmapService/
  ProjectRecommendationService/ProjectSimulationService (see
  app/services/roadmap_service.py, project_service.py) solve
  /roadmaps/generate and /projects/recommend+simulate directly, with their
  own ad hoc catalog Protocols (ResourceCatalogProvider,
  ProjectCatalogProvider) instead of going through these two Protocols at
  all. This was a deliberate Milestone 5 choice (ship the contracted
  routes against the fixture catalogs that actually exist), not an
  oversight, but it means a future real RoadmapProvider/ProjectProvider
  would need either (a) a coordinated refactor of those services to call
  through these Protocols, or (b) these two Protocols being retired in
  favor of the ad hoc ones that are already working. Flagging for Rehan +
  Jawad to decide before building a real roadmap/project backend against
  either shape.
- LLMProfileProvider, EmbeddingProvider: not implemented, no call site —
  CV parsing / LLM extraction and RunPod embeddings are both still
  entirely future work (see members/REHAN_BACKEND_INTEGRATION.md P0 list).
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
        """Return ranked RoleMatch results for a profile against the role catalog.

        profile: app.schemas.profile.StudentProfile (or a duck-typed
            equivalent exposing .skills: list[SkillRef-like], .interests,
            .semester, .projects).
        roles: an iterable of role objects, each exposing at minimum
            .role_id, .role_title, .required_skills (iterable of objects
            with .skill_id/.name/.weight), .min_semester,
            .transferable_interests — see app.services.role_catalog.RoleFixture
            for the fixture's concrete shape; a real catalog need only
            match these attributes, not that exact class.
        scenario: app.schemas.matching.ScenarioId | None
            (Literal["moderate", "fast"] | None).
        signals: an iterable of trend-signal-like objects; the current
            MatchingService always passes an empty list (NullTrendProvider)
            — no real MatchingProvider implementation should assume this
            is ever non-empty today, but must still accept the parameter.
        Returns: list[app.schemas.matching.RoleMatch] — score 0-100,
            score_type literally "profile_alignment_estimate".
        """
        ...


class TrendProvider(Protocol):
    def latest(self, role_id: Any = None) -> Any:
        """Return the latest dated TrendSignal set, optionally filtered by role.

        role_id: str | None.
        Returns: an object exposing .signals (list[TrendSignal-like, each
            with .skill_id/.source_id/.observed_at/.retrieved_at/.direction/
            .role_ids — see app.schemas.trends.TrendSignal),
            .last_successful_refresh_at (datetime | None), .source_status
            ("ok" | "stale" | "unavailable") — see
            app.services.trend_provider.TrendResult for the fixture's
            concrete shape.
        """
        ...


class LLMProfileProvider(Protocol):
    def extract(self, text: str) -> Any:
        """Extract a validated StudentProfile from free text, with manual fallback."""
        ...


class RoadmapProvider(Protocol):
    def generate(self, profile: Any, role: Any, missing_skills: Any, resources: Any) -> Any:
        """Produce an ordered, resource-linked learning roadmap.

        Not currently called — see module docstring's "protocol mismatch"
        note. app.services.roadmap_service.RoadmapService solves this
        route directly today.
        """
        ...


class ProjectProvider(Protocol):
    def recommend(self, profile: Any, role: Any, skills: Any) -> Any:
        """Recommend role-relevant portfolio projects.

        Not currently called — see module docstring's "protocol mismatch"
        note. app.services.project_service.ProjectRecommendationService
        solves this route directly today.
        """
        ...


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> Any:
        """Return embedding vectors (RunPod-backed or a deterministic local fallback)."""
        ...
