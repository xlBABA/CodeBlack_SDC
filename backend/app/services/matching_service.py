"""Orchestrates POST /careers/match: resolves the profile, loads the role
catalog, delegates scoring to the injected MatchingProvider.

Never calls RunPod or any network service directly — only the injected
RoleCatalogProvider / MatchingProvider / TrendProvider abstractions, so
swapping in Hussain's real matcher or Jawad's real catalog later needs no
route change.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.errors import AppError
from app.schemas.matching import CatalogCoverage, MatchPayload, MatchRequest, RoleMatch, ScenarioId
from app.schemas.profile import StudentProfile
from app.services.interfaces import MatchingProvider, TrendProvider
from app.services.profile_service import ProfileService, to_schema
from app.services.role_catalog import RoleCatalogProvider

TOTAL_TARGET_ROLES = 30  # CLAUDE.md: "up to 30 curated roles" — catalog target, not current size.

_FIXTURE_WARNING = (
    "Fixture role catalog and matching logic; full verified 30-role "
    "coverage and real scoring are pending teammate integration."
)


@dataclass
class MatchOutcome:
    payload: MatchPayload
    warnings: list[str]
    # The actually-resolved profile (stored profile if profile_id was given
    # and known, else the inline one). Milestone 5's project simulation
    # reuses this to build an in-memory "what if" copy without a second,
    # duplicated profile_id-resolution implementation.
    profile: StudentProfile


@dataclass
class RoleMatchResolution:
    """Result of match_role() — a single role's score, computed without
    MatchRequest's contract-fixed limit<=6 truncation (see
    match_role's docstring)."""

    profile: StudentProfile
    role_match: RoleMatch
    warnings: list[str]


class MatchingService:
    def __init__(
        self,
        profile_service: ProfileService,
        catalog: RoleCatalogProvider,
        matcher: MatchingProvider,
        trends: TrendProvider,
        matching_mode_warning: str | None = None,
    ) -> None:
        self._profiles = profile_service
        self._catalog = catalog
        self._matcher = matcher
        self._trends = trends
        # None preserves the original fixture-mode text below unchanged
        # (every existing call site that doesn't pass this keeps today's
        # exact behavior). A caller only needs to override it when the
        # injected `matcher` isn't actually FixtureMatchingProvider, since
        # otherwise this text becomes factually wrong (e.g. "real scoring
        # pending teammate integration" while a real matcher is active).
        self._matching_mode_warning = matching_mode_warning or _FIXTURE_WARNING

    def _resolve_profile(self, profile: StudentProfile) -> StudentProfile:
        if profile.profile_id:
            stored = self._profiles.get(profile.profile_id)
            if stored is None:
                raise AppError(
                    code="PROFILE_NOT_FOUND",
                    message=f"No profile found with profile_id '{profile.profile_id}'.",
                    status_code=404,
                )
            return to_schema(stored)
        return profile

    def match(self, request: MatchRequest) -> MatchOutcome:
        profile = self._resolve_profile(request.profile)

        roles = self._catalog.list_roles()
        signals = self._trends.latest()
        matches = self._matcher.match(profile, roles, request.scenario_id, signals)
        matches = matches[: request.limit]

        payload = MatchPayload(
            matches=matches,
            catalog_coverage=CatalogCoverage(verified=len(roles), total_target=TOTAL_TARGET_ROLES),
            methodology_version="v1",
        )
        return MatchOutcome(payload=payload, warnings=[self._matching_mode_warning], profile=profile)

    def match_role(
        self, profile: StudentProfile, role_id: str, scenario_id: ScenarioId | None = None
    ) -> RoleMatchResolution | None:
        """Resolve a profile (identical semantics/precedence to match() —
        profile_id resolution happens first, so an invalid profile_id still
        raises PROFILE_NOT_FOUND before any role lookup) and score exactly
        one role looked up directly in the catalog.

        Unlike match(), this is never truncated by MatchRequest's
        contract-fixed limit<=6 — it's the fix for Milestone 5 review
        Finding 1: callers that need "does this role exist and what's its
        score" (roadmaps, project recommend/simulate) must not infer that
        from membership in a top-6-only result, since a real, catalog-valid
        role can rank outside the top 6 once the catalog grows past 6
        entries. Returns None only when role_id genuinely isn't in the
        catalog. Reuses the same injected MatchingProvider (same 50/25/15/10
        fixture formula) and TrendProvider — no duplicate scoring logic.
        """
        resolved_profile = self._resolve_profile(profile)

        role = next((r for r in self._catalog.list_roles() if r.role_id == role_id), None)
        if role is None:
            return None

        signals = self._trends.latest()
        matches = self._matcher.match(resolved_profile, [role], scenario_id, signals)
        return RoleMatchResolution(
            profile=resolved_profile, role_match=matches[0], warnings=[self._matching_mode_warning]
        )
