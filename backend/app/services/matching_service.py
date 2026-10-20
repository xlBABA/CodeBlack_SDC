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
from app.schemas.matching import CatalogCoverage, MatchPayload, MatchRequest
from app.services.interfaces import MatchingProvider, TrendProvider
from app.services.profile_service import ProfileService, to_schema
from app.services.role_catalog import RoleCatalogProvider

TOTAL_TARGET_ROLES = 30  # CLAUDE.md: "up to 30 curated roles" — catalog target, not current size.


@dataclass
class MatchOutcome:
    payload: MatchPayload
    warnings: list[str]


class MatchingService:
    def __init__(
        self,
        profile_service: ProfileService,
        catalog: RoleCatalogProvider,
        matcher: MatchingProvider,
        trends: TrendProvider,
    ) -> None:
        self._profiles = profile_service
        self._catalog = catalog
        self._matcher = matcher
        self._trends = trends

    def match(self, request: MatchRequest) -> MatchOutcome:
        profile = request.profile

        if profile.profile_id:
            stored = self._profiles.get(profile.profile_id)
            if stored is None:
                raise AppError(
                    code="PROFILE_NOT_FOUND",
                    message=f"No profile found with profile_id '{profile.profile_id}'.",
                    status_code=404,
                )
            profile = to_schema(stored)

        roles = self._catalog.list_roles()
        signals = self._trends.latest()
        matches = self._matcher.match(profile, roles, request.scenario_id, signals)
        matches = matches[: request.limit]

        payload = MatchPayload(
            matches=matches,
            catalog_coverage=CatalogCoverage(verified=len(roles), total_target=TOTAL_TARGET_ROLES),
            methodology_version="v1",
        )
        warnings = [
            "Fixture role catalog and matching logic; full verified 30-role "
            "coverage and real scoring are pending teammate integration."
        ]
        return MatchOutcome(payload=payload, warnings=warnings)
