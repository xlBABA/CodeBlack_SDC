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
from .matcher import DEGRADED_CAVEAT, Matcher
from .normalizer import SkillNormalizer
from .runpod_client import RunPodEmbeddingProvider, runpod_configured

logger = logging.getLogger(__name__)


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
        # RoleFixture (ours and Jawad's cached roles) has no data_mode: omit rather than guess,
        # so the matcher's "Fixture role for testing" caveat does not fire for cached roles.
        "data_mode": r.get("data_mode"),
        "required_skills": [
            {"skill_id": s["skill_id"], "importance": s.get("weight", 1.0),
             "required": s.get("required", True)}
            for s in r["required_skills"]
        ],
        "transferable_skills": list(r.get("transferable_skills") or []),
        "transferable_interests": list(r.get("transferable_interests") or []),
        "prerequisites": prerequisites,
        "evidence_ids": list(r.get("evidence_ids") or []),
        "skills_coverage": r.get("skills_coverage"),  # "limited" when the catalogue misses the role's main tools
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

    def _applicable_pairs(self, catalogue: list[dict]) -> list[list[str]]:
        """not_equivalent pairs whose two skill_ids are both in the catalogue.

        A pair that cannot be applied is skipped with a warning naming it, so a list
        written for another catalogue does not silently protect nothing."""
        ids = {s["skill_id"] for s in catalogue}
        pairs = []
        for pair in self.not_equivalent:
            if len(pair) == 2 and set(pair) <= ids:
                pairs.append(pair)
            else:
                unknown = sorted(set(pair) - ids) if len(pair) == 2 else []
                reason = (f"skill_id(s) not in the catalogue: {', '.join(unknown)}" if unknown
                          else "not a pair of two skill_ids")
                logger.warning("Ignoring not_equivalent pair %s (%s)", list(pair), reason)
        return pairs

    def _semantic_similarity(self, catalogue: list[dict]) -> tuple[scoring.SimilarityFn | None, bool]:
        """Return (similarity function or None, degraded flag)."""
        if self.similarity is not None:
            return self.similarity, False
        if not runpod_configured() or time.monotonic() < self._down_until:
            return None, True

        key = tuple((s["skill_id"], s["name"], tuple(s.get("aliases", []))) for s in catalogue)
        provider = self._providers.get(key)
        if provider is None:
            provider = RunPodEmbeddingProvider.from_skills(
                catalogue, not_equivalent=self._applicable_pairs(catalogue))
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
                if DEGRADED_CAVEAT not in m["caveats"]:
                    m["caveats"].append(DEGRADED_CAVEAT)
        # skills_component() lists every unmatched role skill as missing (it only halves the weight of
        # optional ones); an optional skill is not a mandatory gap, so it is not reported as missing.
        optional_by_role = {
            rd["role_id"]: {s["skill_id"] for s in rd["required_skills"] if not s.get("required", True)}
            for rd in role_dicts
        }
        for m in matches:
            optional = optional_by_role.get(m["role_id"])
            if optional:
                m["missing_skills"] = [s for s in m["missing_skills"] if s["skill_id"] not in optional]
        if self.result_model is not None:
            return [self.result_model(**m) for m in matches]
        return matches
