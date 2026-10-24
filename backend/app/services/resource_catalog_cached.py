"""Cached learning-resource dataset — Jawad's verified resources.json
(app/data/cached/resources.json; byte-identical copy of
feat/jawad-trends-data:data/resources.json as of commit 2838340 — see
docs/source-register.md on that branch for provenance).

Milestone 6D-2A added import and validation (load_cached_resources(),
skills_without_resource()). Milestone 6D-2B adds CachedResourceCatalog,
satisfying app.services.resource_catalog.ResourceCatalogProvider —
still not wired into any route or DI, and never mixes in anything from
FixtureResourceCatalog (see CachedResourceCatalog's own docstring).

Known, honestly-disclosed gaps, preserved rather than invented:
- 4 of the 14 canonical skills have no verified resource yet
  (skills_without_resource(), each with a stated reason) — this is not
  an error, it is Jawad's own data.
- estimated_hours is null for any resource where the provider states no
  duration; team_estimate_hours/team_estimate_basis carries the
  team's own labelled estimate in that case instead, never silently
  substituted for a provider-stated number.
"""
from __future__ import annotations

from app.services.resource_catalog import ResourceFixture
from app.services.role_catalog_cached import CachedCatalogError, _load_json, _require_dict

_REQUIRED_RESOURCE_FIELDS = {
    "resource_id", "source_id", "skill_ids", "title", "provider", "url", "level",
    "price", "estimated_hours", "hours_source", "prerequisites", "checked_at", "checked_by",
}
# Metadata fields some (not all) resources carry — real data, not junk.
_ALLOWED_RESOURCE_METADATA_FIELDS = {
    "rank", "team_estimate_basis", "team_estimate_hours", "title_note", "topics", "url_note",
}


def _canonical_skill_ids() -> set[str]:
    skills_doc = _load_json("skills.json")
    return {s["skill_id"] for s in skills_doc["skills"]}


def _validate_resources(resources: list, skill_ids: set[str], skill_gap_ids: set[str]) -> None:
    dict_resources = [_require_dict(r, f"resources[{i}]") for i, r in enumerate(resources)]

    seen_ids = [r["resource_id"] for r in dict_resources if "resource_id" in r]
    if len(set(seen_ids)) != len(seen_ids):
        raise CachedCatalogError("Duplicate resource_id in cached resources.json")

    covered_skill_ids: set[str] = set()
    for resource in dict_resources:
        missing = _REQUIRED_RESOURCE_FIELDS - resource.keys()
        if missing:
            raise CachedCatalogError(f"{resource.get('resource_id')}: missing fields {missing}")
        unsupported = resource.keys() - _REQUIRED_RESOURCE_FIELDS - _ALLOWED_RESOURCE_METADATA_FIELDS
        if unsupported:
            raise CachedCatalogError(f"{resource['resource_id']}: unsupported fields {unsupported}")

        if not resource.get("skill_ids"):
            raise CachedCatalogError(f"{resource['resource_id']}: no skill_ids")
        for skill_id in resource["skill_ids"]:
            if skill_id not in skill_ids:
                raise CachedCatalogError(
                    f"{resource['resource_id']}: unknown skill_id '{skill_id}' not present in cached skills.json"
                )
            covered_skill_ids.add(skill_id)

        estimated_hours = resource["estimated_hours"]
        if estimated_hours is not None and (
            not isinstance(estimated_hours, (int, float))
            or isinstance(estimated_hours, bool)
            or estimated_hours < 0
        ):
            raise CachedCatalogError(
                f"{resource['resource_id']}: estimated_hours must be null or a non-negative number, "
                f"got {estimated_hours!r}"
            )
        if estimated_hours is None and "team_estimate_hours" not in resource:
            raise CachedCatalogError(
                f"{resource['resource_id']}: estimated_hours is null but no team_estimate_hours is given "
                "(no documented basis for this resource's duration)"
            )
        if not isinstance(resource.get("hours_source"), str) or not resource["hours_source"].strip():
            raise CachedCatalogError(f"{resource['resource_id']}: hours_source must be a non-empty string")

        if not isinstance(resource.get("url"), str) or not resource["url"].startswith("https://"):
            raise CachedCatalogError(f"{resource['resource_id']}: url must be a real https:// URL")

        prerequisites = resource.get("prerequisites")
        if not isinstance(prerequisites, dict) or "skill_ids" not in prerequisites:
            raise CachedCatalogError(f"{resource['resource_id']}: malformed prerequisites")
        for prereq_skill_id in prerequisites["skill_ids"]:
            if prereq_skill_id not in skill_ids:
                raise CachedCatalogError(
                    f"{resource['resource_id']}: unknown prerequisite skill_id '{prereq_skill_id}'"
                )

    # The honestly-disclosed gap list must not claim "no resource" for a
    # skill that actually has one, and must only name real skill_ids.
    for gap_skill_id in skill_gap_ids:
        if gap_skill_id not in skill_ids:
            raise CachedCatalogError(f"skills_without_resource: unknown skill_id '{gap_skill_id}'")
    contradicted = skill_gap_ids & covered_skill_ids
    if contradicted:
        raise CachedCatalogError(
            f"skills_without_resource claims no resource exists for skills that DO have one: {contradicted}"
        )


def load_cached_resources() -> list[dict]:
    """Load, validate and return app/data/cached/resources.json's resource
    records as plain dicts. Raises CachedCatalogError on any integrity
    problem rather than silently dropping or guessing."""
    doc = _load_json("resources.json")
    if doc.get("data_mode") != "cached":
        raise CachedCatalogError(
            f"cached resources.json data_mode must be 'cached', got {doc.get('data_mode')!r} "
            "(must never be labelled 'live')"
        )
    skill_ids = _canonical_skill_ids()
    resources = doc.get("resources") or []
    skill_gap_ids = set((doc.get("skills_without_resource") or {}).keys())
    _validate_resources(resources, skill_ids, skill_gap_ids)
    return resources


def skills_without_resource() -> dict[str, str]:
    """The honestly-disclosed skill_id -> reason map for canonical skills
    with no verified resource yet. Never invented, never silently
    treated as covered."""
    doc = _load_json("resources.json")
    return doc.get("skills_without_resource") or {}


def _provenance_text(resource: dict) -> str:
    """Which number is used and why — never silently blended. If the
    provider states a duration, hours_source already says so in full
    ("Provider-stated: 345 minutes ..."); otherwise estimated_hours is
    null and team_estimate_basis (required by _validate_resources
    whenever estimated_hours is null) explains the team's own estimate.
    A resource with a price status of "not_stated" (e.g.
    mathworks_matlab_onramp) is not claimed as free — that nuance lives
    only here in the text, since ResourceFixture.cost has no caller
    today (RoadmapService never reads it) and no "unknown" state to
    carry even if it did; see the 6D-2B report."""
    if resource["estimated_hours"] is not None:
        basis = resource["hours_source"]
    else:
        basis = resource.get("team_estimate_basis") or resource["hours_source"]
    if resource["price"]["status"] == "not_stated":
        basis = f"{basis} Price not stated by provider."
    return basis


def _to_resource_fixtures(resource: dict) -> list[ResourceFixture]:
    """One ResourceFixture per skill_id — handles a resource covering
    multiple skills without duplicating the underlying record (today
    every cached resource lists exactly one skill_id, but the source
    schema allows more; this fans out correctly either way)."""
    hours = resource["estimated_hours"]
    if hours is None:
        hours = resource["team_estimate_hours"]
    provenance = _provenance_text(resource)
    return [
        ResourceFixture(
            resource_id=resource["resource_id"],
            skill_id=skill_id,
            title=resource["title"],
            estimated_hours=float(hours),
            cost=0.0,
            verified=True,
            url=resource["url"],
            provenance=provenance,
        )
        for skill_id in resource["skill_ids"]
    ]


class CachedResourceCatalog:
    """Satisfies app.services.resource_catalog.ResourceCatalogProvider
    using Jawad's real, cached learning-resource dataset exclusively —
    never mixes in anything from FixtureResourceCatalog. Loads and
    validates on every call (same reasoning as CachedRoleCatalog: a bad
    data file fails inside a request/test, not at interpreter startup).
    Not wired into any route or FastAPI dependency yet (Milestone 6D-2B
    scope: adapter implementation and testing only)."""

    def list_resources(self) -> list[ResourceFixture]:
        resources = load_cached_resources()
        return [fixture for resource in resources for fixture in _to_resource_fixtures(resource)]
