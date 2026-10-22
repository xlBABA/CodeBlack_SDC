"""Portfolio projects (pure: data/projects.json in, dict out, no network).

get_projects returns the POST /projects/recommend data shape from
contracts/API_CONTRACT.md:
{projects: [{project_id, title, skill_ids, estimated_hours, source_ids, milestones}]}
Each project also keeps its extra fields (role_id, difficulty,
expected_outcome, hours_basis, source_type, ...). Projects are curated, not
"trending" - there is no signal evidence behind their order.
"""
from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _load(name: str):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def get_projects(role_id: str, limit: int = 3) -> dict | None:
    """None if the role_id is unknown; otherwise up to `limit` projects in
    the curated file order."""
    if not any(r["role_id"] == role_id for r in _load("roles.json")):
        return None
    projects = [
        {**p, "estimated_hours": float(p["estimated_hours"])}
        for p in _load("projects.json")["projects"]
        if p["role_id"] == role_id
    ]
    return {"projects": projects[: max(0, limit)]}
