"""Learning roadmap (pure: data files in, dict out, no network).

get_roadmap returns the POST /roadmaps/generate data shape from
contracts/API_CONTRACT.md:
{steps: [{skill_id, resource_id, estimated_hours, reason}], total_estimated_hours}
plus `warnings` (for the backend to put in the response envelope) and, per
step, `hours_basis`: "provider_stated" or "team_estimate". estimated_hours is
always a number >= 0 (Rehan's RoadmapStep requires it).

Order: a skill that another step's resource lists as a prerequisite comes
first; otherwise required before optional, then higher importance first.
"""
from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _load(name: str):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def _skill_id(item) -> str:
    return item["skill_id"] if isinstance(item, dict) else item


def get_roadmap(profile: dict, role_id: str, missing_skills: list) -> dict | None:
    """missing_skills: skill_ids or SkillRef dicts (e.g. RoleMatch.missing_skills).
    Returns None if role_id is unknown."""
    role = next((r for r in _load("roles.json") if r["role_id"] == role_id), None)
    if role is None:
        return None
    res_data = _load("resources.json")
    resource_for: dict[str, dict] = {}  # skill_id -> preferred resource (lowest rank, then file order)
    for res in res_data["resources"]:
        for sid in res["skill_ids"]:
            if sid not in resource_for or res.get("rank", 1) < resource_for[sid].get("rank", 1):
                resource_for[sid] = res
    role_skill = {s["skill_id"]: s for s in role["required_skills"]}
    held = {_skill_id(s) for s in profile.get("skills") or []}

    missing = list(dict.fromkeys(_skill_id(s) for s in missing_skills))
    warnings: list[str] = []
    no_resource = [sid for sid in missing if sid not in resource_for]
    if no_resource:
        warnings.append(
            "No verified free/low-cost resource yet for: " + ", ".join(no_resource)
            + ". These skills are not in the plan."
        )
    plannable = [sid for sid in missing if sid in resource_for]

    def priority(sid: str):
        rs = role_skill.get(sid, {})
        return (0 if rs.get("required", True) else 1, -rs.get("importance", 0), sid)

    ordered: list[str] = []

    def visit(sid: str, trail: tuple = ()) -> None:
        if sid in ordered or sid in trail:
            return
        for pre in sorted(resource_for[sid]["prerequisites"]["skill_ids"], key=priority):
            if pre in plannable:
                visit(pre, trail + (sid,))
            elif pre not in held:
                warnings.append(
                    f"The resource for {sid} assumes {pre}, which is not in your "
                    "profile or this plan."
                )
        ordered.append(sid)

    for sid in sorted(plannable, key=priority):
        visit(sid)

    steps = []
    team_estimated = []
    for sid in ordered:
        res = resource_for[sid]
        rs = role_skill.get(sid)
        kind = ("required" if rs.get("required", True) else "optional") if rs else "extra"
        importance = f", importance {rs['importance']}/5" if rs else ""
        if res["estimated_hours"] is not None:
            hours, basis = res["estimated_hours"], "provider_stated"
        else:
            hours, basis = res["team_estimate_hours"], "team_estimate"
            team_estimated.append(f"{sid} ({hours} h)")
        steps.append({
            "skill_id": sid,
            "resource_id": res["resource_id"],
            "estimated_hours": float(hours),
            "reason": (
                f"Missing {kind} skill for {role['role_title']}{importance}. "
                f"Resource: {res['title']} ({res['provider']})."
            ),
            "hours_basis": basis,
        })
    if team_estimated:
        warnings.append(
            "Hours for these steps are team estimates, not provider-stated: "
            + ", ".join(team_estimated) + ". They are included in total_estimated_hours."
        )

    return {
        "steps": steps,
        "total_estimated_hours": round(sum(s["estimated_hours"] for s in steps), 2),
        "warnings": warnings,
    }
