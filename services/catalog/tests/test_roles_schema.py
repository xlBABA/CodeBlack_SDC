"""Checks data/roles.json, skills.json and sdg_mappings.json are consistent.

Matches the catalogue shape Hussain's matcher expects
(services/matching/README.md, "Data expected from Jawad").

Run: python services/catalog/tests/test_roles_schema.py
No external packages needed (standard library only).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
SOURCE_REGISTER = ROOT / "docs" / "source-register.md"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def registered_source_ids():
    text = SOURCE_REGISTER.read_text(encoding="utf-8")
    return set(re.findall(r"\|\s*(onet_[a-z0-9_]+)\s*\|", text))


def main():
    errors = []

    roles = load("roles.json")
    skills = load("skills.json")["skills"]
    sdg = load("sdg_mappings.json")
    source_ids = registered_source_ids()

    skill_ids = {s["skill_id"] for s in skills}
    if len(skill_ids) != len(skills):
        errors.append("Duplicate skill_id in skills.json")

    role_ids = {r["role_id"] for r in roles}
    if len(role_ids) != len(roles):
        errors.append("Duplicate role_id in roles.json")

    for role in roles:
        rid = role["role_id"]
        if not role.get("verified"):
            errors.append(f"{rid}: not marked verified")
        evidence_ids = role.get("evidence_ids") or []
        if not evidence_ids:
            errors.append(f"{rid}: no evidence_ids")
        for eid in evidence_ids:
            if eid not in source_ids:
                errors.append(f"{rid}: evidence_id '{eid}' not in docs/source-register.md")
        required_skills = role.get("required_skills") or []
        if not required_skills:
            errors.append(f"{rid}: no required_skills listed")
        for s in required_skills:
            if s["skill_id"] not in skill_ids:
                errors.append(f"{rid}: unknown skill_id '{s['skill_id']}'")
            if not (1 <= s.get("importance", 0) <= 5):
                errors.append(f"{rid}: skill '{s['skill_id']}' importance must be 1-5, got {s.get('importance')}")

    role_sdg_ids = {m["role_id"] for m in sdg["role_sdg_mappings"]}
    missing_role_sdg = role_ids - role_sdg_ids
    if missing_role_sdg:
        errors.append(f"Roles missing an SDG mapping: {sorted(missing_role_sdg)}")

    skill_sdg_ids = {m["skill_id"] for m in sdg["skill_sdg_mappings"]}
    missing_skill_sdg = skill_ids - skill_sdg_ids
    if missing_skill_sdg:
        errors.append(f"Skills missing an SDG mapping: {sorted(missing_skill_sdg)}")

    for m in sdg["role_sdg_mappings"] + sdg["skill_sdg_mappings"]:
        if not m.get("reason") or len(m["reason"]) < 10:
            errors.append(f"SDG mapping missing a real reason: {m}")

    if errors:
        print("FAILED:")
        for e in errors:
            print(f" - {e}")
        sys.exit(1)

    print(f"PASSED: {len(roles)} roles, {len(skills)} skills, all SDG-mapped, all sources registered.")


if __name__ == "__main__":
    main()
