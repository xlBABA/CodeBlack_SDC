"""Cached role/skill catalog — Jawad's verified, O*NET-derived dataset
(app/data/cached/roles.json, skills.json; byte-identical copies of
feat/jawad-trends-data:data/roles.json and data/skills.json as of commit
2838340 — see docs/source-register.md on that branch for provenance).

This is a second RoleCatalogProvider (app.services.role_catalog.
RoleCatalogProvider), selected explicitly where wanted — it does not
replace FixtureRoleCatalog, which stays the default for existing
fixture-mode tests and routes. Milestone 6B-1 scope: loading and
validation only. Nothing wires this into matching, roadmaps, projects or
SDGs yet.

Known gaps, preserved rather than invented:
- Every role's `prerequisites` is `[]` in the source data, so
  RoleFixture.min_semester is set to None (see role_catalog.py). Do not
  pass these roles to FixtureMatchingProvider until that is resolved.
- Every role's `transferable_skills`/`transferable_interests` is `[]`.
- The source data's required_skills[].required (true/false) distinction
  is preserved on RoleRequirement.required (see role_catalog.py), but
  nothing reads it yet: app.services.matching_provider._skills_score
  still lists an unmatched optional skill in missing_skills exactly like
  a required one. This is metadata preservation only, not a fix to that
  downstream presentation — that needs a matching-integration change.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.services.role_catalog import RoleFixture, RoleRequirement

_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "cached"

# Functional fields every role/skill must have for conversion into a
# RoleFixture/RoleRequirement to succeed.
_REQUIRED_ROLE_FIELDS = {
    "role_id", "role_title", "verified", "industry_category", "required_skills",
    "transferable_skills", "transferable_interests", "prerequisites", "evidence_ids",
}
_REQUIRED_SKILL_FIELDS = {"skill_id", "name"}
_REQUIRED_ROLE_SKILL_ENTRY_FIELDS = {"skill_id", "importance", "required"}

# O*NET provenance/metadata fields Jawad's data carries for traceability
# (docs/source-register.md) or for Hussain's normalizer (aliases/
# source_ids) — real data, not junk, even though nothing in this module
# reads them yet. Permitted alongside the required fields above; any
# field outside both sets is treated as genuinely unsupported.
_ALLOWED_ROLE_METADATA_FIELDS = {"onet_soc_code", "onet_title", "source_id", "notes", "skills_coverage"}
_ALLOWED_SKILL_METADATA_FIELDS = {"aliases", "source_ids"}


class CachedCatalogError(ValueError):
    """Raised when app/data/cached/*.json fails integrity validation."""


def _load_json(name: str) -> object:
    return json.loads((_DATA_DIR / name).read_text(encoding="utf-8"))


def _require_dict(item: object, context: str) -> dict:
    if not isinstance(item, dict):
        raise CachedCatalogError(f"{context}: expected an object, got {type(item).__name__}")
    return item


def _validate_skills(skills: list) -> dict[str, str]:
    names: dict[str, str] = {}
    seen_ids: list[str] = []
    for index, raw_skill in enumerate(skills):
        skill = _require_dict(raw_skill, f"skills[{index}]")
        missing = _REQUIRED_SKILL_FIELDS - skill.keys()
        if missing:
            raise CachedCatalogError(f"skills[{index}]: missing fields {missing}")
        unsupported = skill.keys() - _REQUIRED_SKILL_FIELDS - _ALLOWED_SKILL_METADATA_FIELDS
        if unsupported:
            raise CachedCatalogError(f"skills[{index}] ({skill['skill_id']}): unsupported fields {unsupported}")
        seen_ids.append(skill["skill_id"])
        names[skill["skill_id"]] = skill["name"]
    if len(set(seen_ids)) != len(seen_ids):
        raise CachedCatalogError("Duplicate skill_id in cached skills.json")
    return names


def _validate_roles(roles: list, skill_names: dict[str, str]) -> None:
    dict_roles = [_require_dict(raw_role, f"roles[{index}]") for index, raw_role in enumerate(roles)]

    role_ids = [role["role_id"] for role in dict_roles if "role_id" in role]
    if len(set(role_ids)) != len(role_ids):
        raise CachedCatalogError("Duplicate role_id in cached roles.json")

    for role in dict_roles:
        missing_keys = _REQUIRED_ROLE_FIELDS - role.keys()
        if missing_keys:
            raise CachedCatalogError(f"{role.get('role_id')}: missing fields {missing_keys}")
        unsupported_keys = role.keys() - _REQUIRED_ROLE_FIELDS - _ALLOWED_ROLE_METADATA_FIELDS
        if unsupported_keys:
            raise CachedCatalogError(f"{role['role_id']}: unsupported fields {unsupported_keys}")
        if not role.get("evidence_ids"):
            raise CachedCatalogError(f"{role['role_id']}: no evidence_ids (unverifiable provenance)")
        if not role.get("required_skills"):
            raise CachedCatalogError(f"{role['role_id']}: no required_skills")
        # Milestone 13C-7: skills_coverage was already an allowed optional
        # metadata field (see _ALLOWED_ROLE_METADATA_FIELDS) but had no
        # value-level check — a typo ("Limited", "partial") would have
        # silently done nothing once the matcher started reading it.
        if "skills_coverage" in role and role["skills_coverage"] not in (None, "limited"):
            raise CachedCatalogError(
                f"{role['role_id']}: skills_coverage must be 'limited' or absent, "
                f"got {role['skills_coverage']!r}"
            )
        for index, raw_skill in enumerate(role["required_skills"]):
            skill = _require_dict(raw_skill, f"{role['role_id']}.required_skills[{index}]")
            missing_skill_keys = _REQUIRED_ROLE_SKILL_ENTRY_FIELDS - skill.keys()
            if missing_skill_keys:
                raise CachedCatalogError(
                    f"{role['role_id']}.required_skills[{index}]: missing fields {missing_skill_keys}"
                )
            if skill["skill_id"] not in skill_names:
                raise CachedCatalogError(
                    f"{role['role_id']}: unknown skill_id '{skill['skill_id']}' "
                    "not present in cached skills.json"
                )
            importance = skill["importance"]
            if not isinstance(importance, int) or isinstance(importance, bool) or not (1 <= importance <= 5):
                raise CachedCatalogError(
                    f"{role['role_id']}: skill '{skill['skill_id']}' importance must be "
                    f"an int 1-5, got {importance!r}"
                )
            if not isinstance(skill["required"], bool):
                raise CachedCatalogError(
                    f"{role['role_id']}: skill '{skill['skill_id']}' 'required' flag must be a bool, "
                    f"got {skill['required']!r}"
                )


def _to_role_fixture(role: dict, skill_names: dict[str, str]) -> RoleFixture:
    return RoleFixture(
        role_id=role["role_id"],
        role_title=role["role_title"],
        category=role["industry_category"],
        min_semester=None,  # no prerequisites in the source data; see module docstring
        required_skills=tuple(
            RoleRequirement(
                skill_id=skill["skill_id"],
                name=skill_names[skill["skill_id"]],
                weight=skill["importance"] / 5.0,
                required=skill["required"],
            )
            for skill in role["required_skills"]
        ),
        transferable_interests=tuple(role["transferable_interests"]),
        evidence_ids=tuple(role["evidence_ids"]),
        verified=role["verified"],
        # Milestone 13C-7: optional metadata (already in
        # _ALLOWED_ROLE_METADATA_FIELDS) — Hussain's review of the
        # 30-role data found 4 roles flagged "limited" with no caveat
        # reaching the student; this is the missing propagation step.
        skills_coverage=role.get("skills_coverage"),
    )


def load_cached_roles() -> list[RoleFixture]:
    """Load, validate and convert app/data/cached/*.json into RoleFixtures.

    Raises CachedCatalogError on any integrity problem (duplicate IDs,
    an unknown skill_id, a malformed importance/required value, or a
    missing required field) rather than silently dropping or guessing.
    """
    skills_doc = _load_json("skills.json")
    if skills_doc.get("data_mode") != "cached":
        raise CachedCatalogError(
            f"cached skills.json data_mode must be 'cached', got {skills_doc.get('data_mode')!r} "
            "(O*NET-derived snapshot data must never be labelled 'live')"
        )
    skill_names = _validate_skills(skills_doc["skills"])

    roles = _load_json("roles.json")
    _validate_roles(roles, skill_names)

    return [_to_role_fixture(role, skill_names) for role in roles]


class CachedRoleCatalog:
    """Satisfies app.services.role_catalog.RoleCatalogProvider.

    Loads and validates on every call (small dataset, no caching needed
    yet) rather than at import time, so a bad data file fails inside a
    request/test, not at interpreter startup.
    """

    def list_roles(self) -> list[RoleFixture]:
        return [role for role in load_cached_roles() if role.verified]
