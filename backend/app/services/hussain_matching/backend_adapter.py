# Imported from origin/feature/hussain-matching @ 61373a5 (owner: Hussain),
# source services/matching/backend_adapter.py, with two Milestone 6C-2A
# compatibility fixes applied (see inline comments below): preserving
# RoleRequirement.required instead of hardcoding True, and excluding
# unmatched optional skills from missing_skills. Everything else
# (scoring.py, matcher.py, normalizer.py, scenarios.py, runpod_client.py,
# embeddings.py) is vendored verbatim and unmodified.
"""Adapter so Rehan's FastAPI backend can use this matcher unchanged.

Rehan's MatchingService calls  provider.match(profile, roles, scenario, signals)
with Pydantic StudentProfile, RoleFixture dataclasses and TrendSignal models,
and expects RoleMatch models back (it reads .score and .missing_skills).

This module does NOT import the backend (services/ stays independent).
Rehan passes his RoleMatch class in:

    from services.matching.backend_adapter import HussainMatchingProvider
    from app.schemas.matching import RoleMatch

    def get_matching_provider() -> MatchingProvider:
        return HussainMatchingProvider(result_model=RoleMatch)
"""
from __future__ import annotations

import dataclasses
import logging
import time
from typing import Any, Callable

from . import scoring
from .matcher import Matcher
from .normalizer import SkillNormalizer
from .runpod_client import RunPodEmbeddingProvider, runpod_configured

logger = logging.getLogger(__name__)

DEGRADED_CAVEAT = "Semantic matching unavailable; exact skill matching only (degraded)"


def _to_dict(obj: Any) -> dict:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):  # Pydantic v2
        return obj.model_dump()
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    raise TypeError(f"Cannot convert {type(obj).__name__} to dict")


def role_to_matcher_format(role: Any) -> dict:
    """Convert a backend RoleFixture (or a dict already in matcher format)."""
    r = _to_dict(role)
    if r.get("required_skills") and "importance" in r["required_skills"][0]:
        return r  # already matcher format (e.g. Jawad's roles.json)
    prerequisites = list(r.get("prerequisites") or [])
    if r.get("min_semester"):
        prerequisites.append({
            "prereq_id": "min_semester",
            "type": "min_semester",
            "value": r["min_semester"],
            "hard": False,
            "description": f"Semester {r['min_semester']} or later",
        })
    return {
        "role_id": r["role_id"],
        "role_title": r["role_title"],
        "verified": r.get("verified", True),
        "data_mode": r.get("data_mode", "fixture"),
        "required_skills": [
            # Milestone 6C-2A fix: preserve RoleRequirement.required (added
            # in 6B-2 to carry Jawad's required/optional distinction)
            # instead of hardcoding True for every skill. Importance still
            # comes only from the real weight — never invented when
            # unavailable (defaults to 1.0, matching the original).
            {"skill_id": s["skill_id"], "importance": s.get("weight", 1.0), "required": s.get("required", True)}
            for s in r["required_skills"]
        ],
        "transferable_skills": list(r.get("transferable_skills") or []),
        "transferable_interests": list(r.get("transferable_interests") or []),
        "prerequisites": prerequisites,
        "evidence_ids": list(r.get("evidence_ids") or []),
    }


def catalogue_from_roles(roles: list[Any], extra_skills: list[dict] | None = None) -> list[dict]:
    """Skill catalogue: Jawad's skills (with aliases) plus any role skill not in it."""
    catalogue = {s["skill_id"]: dict(s) for s in extra_skills or []}
    for role in roles:
        for s in _to_dict(role).get("required_skills") or []:
            if s["skill_id"] not in catalogue:
                catalogue[s["skill_id"]] = {
                    "skill_id": s["skill_id"],
                    "name": s.get("name", s["skill_id"].replace("_", " ").title()),
                    "aliases": [],
                }
    return list(catalogue.values())


class HussainMatchingProvider:
    """Satisfies app.services.interfaces.MatchingProvider."""

    def __init__(
        self,
        result_model: Callable[..., Any] | None = None,
        skills_catalogue: list[dict] | None = None,
        similarity: scoring.SimilarityFn | None = None,
        not_equivalent: list[list[str]] | None = None,
        retry_after_seconds: float = 60.0,
    ):
        """`similarity` wins if given. Otherwise semantic matching uses RunPod when
        RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID are set. If they are missing or the
        call fails, matching continues with exact skills only and every match gets
        DEGRADED_CAVEAT. After a failure RunPod is not tried again for
        `retry_after_seconds`, so a down endpoint does not slow every request."""
        self.result_model = result_model
        self.skills_catalogue = skills_catalogue
        self.similarity = similarity
        self.not_equivalent = not_equivalent or []
        self.retry_after_seconds = retry_after_seconds
        self._providers: dict[tuple, RunPodEmbeddingProvider] = {}
        self._down_until = 0.0

    def _semantic_similarity(self, catalogue: list[dict]) -> tuple[scoring.SimilarityFn | None, bool]:
        """Return (similarity function or None, degraded flag)."""
        if self.similarity is not None:
            return self.similarity, False
        if not runpod_configured() or time.monotonic() < self._down_until:
            return None, True

        key = tuple((s["skill_id"], s["name"], tuple(s.get("aliases", []))) for s in catalogue)
        provider = self._providers.get(key)
        if provider is None:
            ids = {s["skill_id"] for s in catalogue}
            pairs = [p for p in self.not_equivalent if len(p) == 2 and set(p) <= ids]
            provider = RunPodEmbeddingProvider.from_skills(catalogue, not_equivalent=pairs)
        try:
            provider.precompute()  # the only network call; later lookups are local
        except Exception as exc:  # any failure degrades to exact matching
            self._down_until = time.monotonic() + self.retry_after_seconds
            self._providers.pop(key, None)
            logger.warning("Semantic matching unavailable (%s): %s", type(exc).__name__, exc)
            return None, True
        self._providers[key] = provider
        return provider, False

    def match(self, profile: Any, roles: list[Any], scenario: Any, signals: Any) -> list[Any]:
        role_dicts = [role_to_matcher_format(r) for r in roles]
        catalogue = catalogue_from_roles(roles, self.skills_catalogue)
        normalizer = SkillNormalizer(catalogue)
        similarity, degraded = self._semantic_similarity(catalogue)
        signal_dicts = [_to_dict(s) for s in (signals or [])]
        # No limit here: Rehan's MatchingService truncates, and match_role() needs every role.
        data = Matcher(normalizer, similarity).match_roles(
            _to_dict(profile), role_dicts, scenario, signal_dicts, limit=len(role_dicts)
        )
        matches = data["matches"]
        if degraded:
            for m in matches:
                m["caveats"].append(DEGRADED_CAVEAT)
        # Milestone 6C-2A fix: scoring.skills_component() (unmodified,
        # verbatim) puts every unmatched skill into missing_skills
        # regardless of its required flag — it only uses `required` to
        # halve the skill's scoring weight. That's correct for the score
        # itself (methodology untouched here), but presenting an optional,
        # unmatched skill as a missing_skills gap mischaracterizes it as
        # mandatory. Filtered here, at the adapter/presentation layer only
        # — RoleMatch's schema is unchanged, and no score/weight changes.
        roles_by_id = {rd["role_id"]: rd for rd in role_dicts}
        for m in matches:
            role = roles_by_id.get(m["role_id"])
            if role is None:
                continue
            optional_skill_ids = {
                s["skill_id"] for s in role["required_skills"] if not s.get("required", True)
            }
            if optional_skill_ids:
                m["missing_skills"] = [
                    s for s in m["missing_skills"] if s["skill_id"] not in optional_skill_ids
                ]
        if self.result_model is not None:
            return [self.result_model(**m) for m in matches]
        return matches
