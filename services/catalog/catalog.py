"""Role catalogue reads (pure: data files in, dicts out, no network).

get_role(role_id) is the data for GET /careers/{role_id}: "role skills,
prerequisites, SDG tags and evidence IDs" (contracts/API_CONTRACT.md). The
contract does not fix field names for this route, so it reuses the names
already in data/roles.json and Hussain's matcher format, which makes each
role dict usable directly by services/matching as well.
"""
from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _load(name: str):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def _role_detail(role: dict, skill_names: dict[str, str], sdg_by_role: dict[str, list[int]]) -> dict:
    detail = dict(role)
    detail["required_skills"] = [
        {
            "skill_id": s["skill_id"],
            "name": skill_names[s["skill_id"]],
            "importance": s["importance"],
            "required": s.get("required", True),
        }
        for s in role["required_skills"]
    ]
    detail["sdg_ids"] = sdg_by_role.get(role["role_id"], [])
    return detail


def get_roles() -> list[dict]:
    """Every role in data/roles.json, with skill names and SDG ids added."""
    skill_names = {s["skill_id"]: s["name"] for s in _load("skills.json")["skills"]}
    sdg_by_role: dict[str, list[int]] = {}
    for m in _load("sdg_mappings.json")["role_sdg_mappings"]:
        sdg_by_role.setdefault(m["role_id"], []).append(m["sdg_id"])
    return [_role_detail(r, skill_names, sdg_by_role) for r in _load("roles.json")]


def get_role(role_id: str) -> dict | None:
    """One role for GET /careers/{role_id}, or None if the role_id is unknown."""
    return next((r for r in get_roles() if r["role_id"] == role_id), None)
