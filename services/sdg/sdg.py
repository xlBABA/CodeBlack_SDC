"""SDG impact for one role (pure: data files in, dict out, no network).

Returns exactly the GET /sdgs/{role_id} data shape from
contracts/API_CONTRACT.md:
{role_sdg_mappings: [{sdg_id, reason}], skill_sdg_mappings: [{skill_id, sdg_id, reason}]}
skill_sdg_mappings covers every skill the role lists, in the role's order.
"""
from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _load(name: str):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def get_sdg_impact(role_id: str) -> dict | None:
    """None if the role_id is unknown (the backend turns that into an empty
    envelope with a warning)."""
    role = next((r for r in _load("roles.json") if r["role_id"] == role_id), None)
    if role is None:
        return None
    sdg = _load("sdg_mappings.json")
    skill_maps: dict[str, list[dict]] = {}
    for m in sdg["skill_sdg_mappings"]:
        skill_maps.setdefault(m["skill_id"], []).append(m)
    return {
        "role_sdg_mappings": [
            {"sdg_id": m["sdg_id"], "reason": m["reason"]}
            for m in sdg["role_sdg_mappings"]
            if m["role_id"] == role_id
        ],
        "skill_sdg_mappings": [
            {"skill_id": m["skill_id"], "sdg_id": m["sdg_id"], "reason": m["reason"]}
            for s in role["required_skills"]
            for m in skill_maps.get(s["skill_id"], [])
        ],
    }
