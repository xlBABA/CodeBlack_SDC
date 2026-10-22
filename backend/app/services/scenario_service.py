"""Orchestrates POST /scenarios/simulate.

Milestone 10C update: scenario_id CAN now shift matching scores slightly
when CATALOG_MODE=cached and a requested role's required skills include
one with a real, dated, rising/falling trend signal (Hussain's
skill_weight_adjustments(), fed Jawad's cached GitHub developer-activity
signals — see app/services/trend_signal_provider.py). This is still an
illustrative, non-validated assumption-driven adjustment (±10%/±25% on a
skill's weight), never a fabricated numeric disruption index or a
forecast — see FixtureScenarioAssumptions' own uncertainty note and each
affected match's own "Scenario adjusted the weight of..." caveat for the
per-response truth. When no applicable signal exists for a request (no
CATALOG_MODE=cached, or the role's skills have no covered/moving signal),
scores remain identical to the baseline, exactly as before this
milestone.
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
            "Scenario assumptions are illustrative and qualitative only. "
            "Matching scores may shift slightly when a real, dated trend "
            "signal applies to one of the requested role's skills (see any "
            "'Scenario adjusted the weight of...' note on a match) — "
            "otherwise scores are identical to the baseline (non-scenario) "
            "result. Either way, this is not a validated scenario-driven "
            "scoring model or a labor-market forecast.",
        ]
        return ScenarioOutcome(payload=payload, warnings=warnings)
