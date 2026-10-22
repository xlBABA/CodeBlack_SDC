"""Orchestrates POST /roadmaps/generate.

Reuses MatchingService.match_role() to find the role's missing_skills for
this profile (no separate skill-gap computation is duplicated). Role
existence is determined by match_role()'s direct catalog lookup, never by
whether the role appears in a top-6-ranked result — see Milestone 5 review
Finding 1. Steps are ordered by the role's own documented skill weight
(role_catalog.RoleRequirement.weight, descending; skill_id ascending as a
deterministic tie-break) — the only "prerequisite" signal currently
documented; no separate prerequisite graph exists yet. A missing skill
with no matching resource produces no fabricated step — it's named in
`warnings` instead. budget_limit never excludes anything because every
placeholder resource is free (cost=0); hours_per_week only informs an
estimated-weeks warning, since the contract response has no field to
carry that number.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.schemas.roadmaps import RoadmapPayload, RoadmapStep, RoleProfileRequest
from app.services.matching_service import MatchingService
from app.services.resource_catalog import ResourceCatalogProvider
from app.services.role_catalog import RoleCatalogProvider


@dataclass
class RoadmapOutcome:
    payload: RoadmapPayload
    warnings: list[str]


class RoadmapService:
    def __init__(
        self,
        matching_service: MatchingService,
        catalog: RoleCatalogProvider,
        resources: ResourceCatalogProvider,
    ) -> None:
        self._matching = matching_service
        self._catalog = catalog
        self._resources = resources

    def generate(self, request: RoleProfileRequest) -> RoadmapOutcome:
        resolution = self._matching.match_role(request.profile, request.role_id)

        if resolution is None:
            warnings = [
                f"role_id '{request.role_id}' was not found in the current "
                "placeholder role catalog; no roadmap could be generated."
            ]
            return RoadmapOutcome(
                payload=RoadmapPayload(steps=[], total_estimated_hours=0.0), warnings=warnings
            )

        role_match = resolution.role_match
        warnings = list(resolution.warnings)
        role = next(r for r in self._catalog.list_roles() if r.role_id == request.role_id)
        weight_by_skill = {req.skill_id: req.weight for req in role.required_skills}
        resources_by_skill = {}
        for resource in self._resources.list_resources():
            resources_by_skill.setdefault(resource.skill_id, resource)

        missing_sorted = sorted(
            role_match.missing_skills,
            key=lambda s: (-weight_by_skill.get(s.skill_id, 0.0), s.skill_id),
        )

        steps: list[RoadmapStep] = []
        for skill in missing_sorted:
            resource = resources_by_skill.get(skill.skill_id)
            if resource is None:
                warnings.append(
                    f"No placeholder resource is available yet for skill "
                    f"'{skill.skill_id}'; this gap is omitted rather than fabricated."
                )
                continue
            reason = (
                f"Closes a missing skill for {role.role_title} "
                f"(role-weighted priority {weight_by_skill.get(skill.skill_id, 0.0)})."
            )
            if resource.provenance:
                # Milestone 6D-2B: discloses whether estimated_hours is
                # provider-stated or a team estimate, using the only
                # contract-compatible free-text field RoadmapStep has
                # (no schema change). None for every FixtureResourceCatalog
                # resource today, so this never changes existing output.
                reason = f"{reason} {resource.provenance}"
            steps.append(
                RoadmapStep(
                    skill_id=skill.skill_id,
                    resource_id=resource.resource_id,
                    estimated_hours=resource.estimated_hours,
                    reason=reason,
                )
            )

        total_hours = sum(step.estimated_hours for step in steps)

        if request.budget_limit is not None:
            warnings.append(
                "All placeholder resources are free (cost=0); budget_limit "
                "does not currently constrain this demonstration roadmap."
            )
        if request.hours_per_week and total_hours > 0:
            weeks = total_hours / request.hours_per_week
            warnings.append(
                f"At {request.hours_per_week} hour(s)/week, this plan takes "
                f"approximately {weeks:.1f} week(s)."
            )

        payload = RoadmapPayload(steps=steps, total_estimated_hours=total_hours)
        return RoadmapOutcome(payload=payload, warnings=warnings)
