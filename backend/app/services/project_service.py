"""Orchestrates POST /projects/recommend and POST /projects/simulate.

Recommend: filters the (tiny, synthetic) project catalog by role_id, ranks
by overlap with the profile's current missing skills for that role
(via MatchingService.match_role() — never a separate skill-gap
calculation, and never limited to a top-6-ranked result; see Milestone 5
review Finding 1), and truncates to `limit`. Default is 3 when the client
omits it — per API_CONTRACT.md's route-table example
("{profile,role_id,limit?:3}") — even though openapi.yaml's shared
RoleProfileRequest has no schema-level default. That default is resolved
here in Python, never in the contract.

Simulate: baseline and simulated scores both come from the same
MatchingService.match_role()/FixtureMatchingProvider used by
/careers/match, looked up directly in the catalog rather than inferred
from a top-6-ranked result. The profile is never mutated or re-persisted
— only an in-memory copy (profile_id cleared so MatchingService treats it
as fresh inline data, never reloading the original from the database)
with the project's skills grafted on is re-matched.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.errors import AppError
from app.schemas.projects import ProjectSimulationPayload, ProjectSimulationRequest, RecommendedProject
from app.schemas.roadmaps import RoleProfileRequest
from app.services.matching_service import MatchingService
from app.services.project_catalog import ProjectCatalogProvider, ProjectFixture

DEFAULT_RECOMMEND_LIMIT = 3

SIMULATION_DISCLAIMER = (
    "Hypothetical simulation only: assumes this project's associated skills "
    "were gained, not that the project was actually completed. It does not "
    "guarantee employment, an internship, or eligibility — scores are an "
    "estimated profile-alignment change, not a real-world outcome measurement."
)


@dataclass
class ProjectRecommendationOutcome:
    projects: list[RecommendedProject]
    warnings: list[str]


@dataclass
class ProjectSimulationOutcome:
    payload: ProjectSimulationPayload
    warnings: list[str]


def _to_recommended(project: ProjectFixture) -> RecommendedProject:
    return RecommendedProject(
        project_id=project.project_id,
        title=project.title,
        skill_ids=list(project.skill_ids),
        estimated_hours=project.estimated_hours,
        source_ids=list(project.source_ids),
        milestones=list(project.milestones),
    )


class ProjectRecommendationService:
    def __init__(self, matching_service: MatchingService, catalog: ProjectCatalogProvider) -> None:
        self._matching = matching_service
        self._catalog = catalog

    def recommend(self, request: RoleProfileRequest) -> ProjectRecommendationOutcome:
        limit = request.limit if request.limit is not None else DEFAULT_RECOMMEND_LIMIT

        all_projects = self._catalog.list_projects()
        candidates = [p for p in all_projects if p.role_id == request.role_id]
        if not candidates:
            covered_role_count = len({p.role_id for p in all_projects})
            return ProjectRecommendationOutcome(
                projects=[],
                warnings=[
                    f"No portfolio projects are available yet for role_id "
                    f"'{request.role_id}'; portfolio projects currently cover "
                    f"{covered_role_count} role(s) in the catalogue."
                ],
            )

        resolution = self._matching.match_role(request.profile, request.role_id)
        missing_skill_ids = (
            {s.skill_id for s in resolution.role_match.missing_skills} if resolution else set()
        )

        def relevance(project: ProjectFixture) -> tuple[int, str]:
            overlap = len(set(project.skill_ids) & missing_skill_ids)
            return (-overlap, project.project_id)

        ranked = sorted(candidates, key=relevance)[:limit]
        warnings: list[str] = []
        if any(p.hours_basis == "team_estimate" for p in ranked):
            # Milestone 6D-2C: RecommendedProject has no per-project text
            # field to carry this, so it's disclosed at the envelope
            # level instead — never fires for FixtureProjectCatalog
            # projects, whose hours_basis is always None.
            warnings.append(
                "Estimated hours for these recommended projects are team "
                "estimates, not provider-verified durations."
            )
        return ProjectRecommendationOutcome(
            projects=[_to_recommended(p) for p in ranked], warnings=warnings
        )


class ProjectSimulationService:
    def __init__(self, matching_service: MatchingService, catalog: ProjectCatalogProvider) -> None:
        self._matching = matching_service
        self._catalog = catalog

    def simulate(self, request: ProjectSimulationRequest) -> ProjectSimulationOutcome:
        baseline = self._matching.match_role(request.profile, request.role_id)
        if baseline is None:
            raise AppError(
                code="ROLE_NOT_FOUND",
                message=f"No role found with role_id '{request.role_id}'.",
                status_code=404,
            )

        project = self._catalog.get(request.project_id)
        if project is None:
            raise AppError(
                code="PROJECT_NOT_FOUND",
                message=f"No project found with project_id '{request.project_id}'.",
                status_code=404,
            )

        resolved_profile = baseline.profile
        existing_skill_ids = {s.skill_id for s in resolved_profile.skills}
        assumed_skills = [s for s in project.skills if s.skill_id not in existing_skill_ids]

        simulated_profile = resolved_profile.model_copy(
            update={
                "profile_id": None,
                "skills": [*resolved_profile.skills, *assumed_skills],
            }
        )

        # simulated_profile has no profile_id, so this always scores the
        # in-memory hypothetical copy directly — never reloads anything
        # from the database.
        simulated = self._matching.match_role(simulated_profile, request.role_id)

        payload = ProjectSimulationPayload(
            baseline_score=baseline.role_match.score,
            simulated_score=simulated.role_match.score,
            assumed_skill_ids=[s.skill_id for s in assumed_skills],
            disclaimer=SIMULATION_DISCLAIMER,
        )
        warnings = [
            *baseline.warnings,
            "Simulated score is a hypothetical, deterministic recalculation "
            "using whichever matching algorithm /careers/match is currently "
            "configured to use; it is not a validated prediction of "
            "real-world outcomes.",
        ]
        return ProjectSimulationOutcome(payload=payload, warnings=warnings)
