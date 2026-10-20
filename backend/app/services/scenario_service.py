"""Orchestrates POST /scenarios/simulate.

Per Milestone 4 scope: scenario_id does NOT alter matching scores — there is
no validated disruption-modeling methodology yet (IMPLEMENTATION_PLAN.md
lists "Scenario assumptions/match recompute" as future Hussain/Jawad/Rehan
work). This service reuses MatchingService verbatim for "same matches" (the
contract's own wording) and layers purely qualitative, clearly-labeled
illustrative assumptions on top — never a fabricated numeric disruption
index. Moderate vs fast are distinguished by wording, not by changing any
score, so there is no contradiction between "scenario accepted" and
"scores unchanged."
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.schemas.matching import MatchRequest
from app.schemas.scenarios import ScenarioPayload, ScenarioRequest
from app.services.matching_service import MatchingService


class ScenarioAssumptionProvider(Protocol):
    def assumptions_for(self, scenario_id: str) -> list[str]:
        """Illustrative, qualitative assumptions for this scenario_id."""
        ...

    def uncertainty_note(self) -> str:
        """Disclaimer describing what these assumptions are not."""
        ...


class FixtureScenarioAssumptions:
    """Deterministic, qualitative-only placeholder pending a real,
    validated scenario methodology."""

    _ASSUMPTIONS: dict[str, list[str]] = {
        "moderate": [
            "Illustrative assumption: skill relevance and tooling change "
            "gradually; currently matched skills remain useful over the "
            "near term.",
            "Illustrative assumption: adoption of new AI tooling in this "
            "field is incremental, giving more time to acquire missing "
            "skills.",
        ],
        "fast": [
            "Illustrative assumption: tooling and task automation change "
            "rapidly; some currently matched skills may need refreshing "
            "sooner.",
            "Illustrative assumption: emerging, currently-missing skills "
            "gain relative importance faster than in the moderate scenario.",
        ],
    }

    _UNCERTAINTY_NOTE = (
        "This scenario is an illustrative, non-validated assumption set for "
        "demonstration purposes. It is not a labor-market forecast, "
        "employment displacement probability, or hiring prediction."
    )

    def assumptions_for(self, scenario_id: str) -> list[str]:
        return list(self._ASSUMPTIONS[scenario_id])

    def uncertainty_note(self) -> str:
        return self._UNCERTAINTY_NOTE


@dataclass
class ScenarioOutcome:
    payload: ScenarioPayload
    warnings: list[str]


class ScenarioService:
    def __init__(
        self,
        matching_service: MatchingService,
        assumptions: ScenarioAssumptionProvider,
    ) -> None:
        self._matching = matching_service
        self._assumptions = assumptions

    def simulate(self, request: ScenarioRequest) -> ScenarioOutcome:
        match_outcome = self._matching.match(
            MatchRequest(profile=request.profile, scenario_id=request.scenario_id)
        )

        payload = ScenarioPayload(
            matches=match_outcome.payload.matches,
            scenario_id=request.scenario_id,
            assumptions=self._assumptions.assumptions_for(request.scenario_id),
            uncertainty_note=self._assumptions.uncertainty_note(),
        )
        warnings = [
            *match_outcome.warnings,
            "Scenario assumptions are illustrative and qualitative only; "
            "matching scores are identical to the baseline (non-scenario) "
            "result — no validated scenario-driven scoring model exists yet.",
        ]
        return ScenarioOutcome(payload=payload, warnings=warnings)
