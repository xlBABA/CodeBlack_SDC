"""AI-adoption scenarios and how dated trend signals adjust skill weights.

These are ASSUMPTIONS, not forecasts. A scenario only scales the importance
of skills that have a dated signal with direction rising or falling. The
influence is bounded by the multipliers below.
"""
from __future__ import annotations

SCENARIOS: dict[str, dict] = {
    "moderate": {
        "scenario_id": "moderate",
        "label": "Moderate AI adoption",
        "rising_multiplier": 1.10,
        "falling_multiplier": 0.90,
        "assumptions": [
            "AI tools spread gradually across industries.",
            "Skills with a rising signal gain 10% importance; falling skills lose 10%.",
        ],
    },
    "fast": {
        "scenario_id": "fast",
        "label": "Fast AI adoption",
        "rising_multiplier": 1.25,
        "falling_multiplier": 0.75,
        "assumptions": [
            "AI tools are adopted quickly and change task mixes sooner.",
            "Skills with a rising signal gain 25% importance; falling skills lose 25%.",
        ],
    },
}

UNCERTAINTY_NOTE = (
    "Scenarios are illustrative assumptions applied to dated signals. They are "
    "not predictions of the job market or of any individual's outcome."
)


def get_scenario(scenario_id: str) -> dict:
    if scenario_id not in SCENARIOS:
        raise ValueError(
            f"Unknown scenario_id '{scenario_id}'. Use one of: {sorted(SCENARIOS)}"
        )
    s = SCENARIOS[scenario_id]
    return {
        "scenario_id": s["scenario_id"],
        "label": s["label"],
        "assumptions": list(s["assumptions"]),
        "uncertainty_note": UNCERTAINTY_NOTE,
    }


def skill_weight_adjustments(
    scenario_id: str | None, signals: list[dict] | None
) -> tuple[dict[str, float], list[dict], list[str]]:
    """Return ({skill_id: multiplier}, applied_signals, notes).

    - No scenario: no adjustment.
    - Only signals with direction rising/falling are used.
    - A skill with conflicting directions is left unadjusted and noted.
    """
    notes: list[str] = []
    if scenario_id is None:
        return {}, [], notes
    scenario = SCENARIOS.get(scenario_id)
    if scenario is None:
        get_scenario(scenario_id)  # raises with a clear message
    if not signals:
        notes.append(
            "No dated trend signals were available, so the scenario did not "
            "change any skill weights."
        )
        return {}, [], notes

    directions: dict[str, set[str]] = {}
    by_skill: dict[str, list[dict]] = {}
    for sig in signals:
        direction = sig.get("direction")
        sid = sig.get("skill_id")
        if not sid or direction not in ("rising", "falling"):
            continue
        directions.setdefault(sid, set()).add(direction)
        by_skill.setdefault(sid, []).append(sig)

    multipliers: dict[str, float] = {}
    applied: list[dict] = []
    for sid, dirs in directions.items():
        if len(dirs) > 1:
            notes.append(f"Conflicting signals for {sid}; weight left unchanged.")
            continue
        direction = next(iter(dirs))
        multipliers[sid] = scenario[f"{direction}_multiplier"]
        applied.extend(by_skill[sid])
    return multipliers, applied, notes
