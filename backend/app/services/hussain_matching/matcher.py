"""Role matcher: profile + roles (+ scenario + signals) -> ranked RoleMatch[].

Output follows contracts/API_CONTRACT.md (RoleMatch, matches response data).
Only roles with verified == True are ranked.
"""
from __future__ import annotations

from . import scoring
from .normalizer import Interpretation, SkillNormalizer
from .scenarios import skill_weight_adjustments

DEFAULT_LIMIT = 6
TOTAL_TARGET_ROLES = 30
# What a trend signal measures, by its `signal_type`; named in the scenario caveat so a
# developer-activity signal is never read as job demand.
SIGNAL_TYPE_LABELS = {
    "developer_activity": "GitHub developer-activity (not job demand)",
}
LIMITED_COVERAGE_CAVEAT = (
    "Limited skills coverage: part of what this role asks for is not in our skill catalogue, "
    "so this score reflects only the skills we can assess."
)
NO_SKILLS_CAVEAT = "No recognised skills in the profile; skill coverage is 0."
DEGRADED_CAVEAT = "Semantic matching unavailable; exact skill matching only (degraded)"


class Matcher:
    def __init__(self, normalizer: SkillNormalizer, similarity: scoring.SimilarityFn | None = None):
        self.normalizer = normalizer
        self.similarity = similarity

    def match_roles(
        self,
        profile: dict,
        roles: list[dict],
        scenario_id: str | None = None,
        signals: list[dict] | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> dict:
        """Full response data for POST /careers/match, plus warnings for the envelope."""
        interpretation_failed: list[bool] = []
        profile_skills, warnings, interpreted = self.normalizer.interpret_profile_skills(
            profile.get("skills") or [], self._interpreter(interpretation_failed)
        )
        multipliers, applied_signals, scenario_notes = skill_weight_adjustments(
            scenario_id, signals
        )

        verified = [r for r in roles if r.get("verified") is True]
        seen: set[str] = set()
        for r in verified:
            if r["role_id"] in seen:
                raise ValueError(f"Duplicate role_id: {r['role_id']}")
            seen.add(r["role_id"])

        if not profile_skills:
            warnings.append("No recognised skills in the profile; skill coverage is 0.")
        if len(verified) < limit:
            warnings.append(
                f"Only {len(verified)} verified roles are available, so fewer "
                f"than {limit} matches may be shown."
            )

        matches = [
            self._score_role(profile, profile_skills, role, multipliers,
                             applied_signals, scenario_notes, interpreted)
            for role in verified
        ]
        if interpretation_failed:  # unknown skills could not be interpreted: say so on every match
            for m in matches:
                m["caveats"].append(DEGRADED_CAVEAT)
        matches.sort(key=lambda m: (-m["score"], m["role_id"]))
        return {
            "matches": matches[: max(0, limit)],
            "catalog_coverage": {"verified": len(verified), "total_target": TOTAL_TARGET_ROLES},
            "methodology_version": scoring.METHODOLOGY_VERSION,
            "warnings": warnings,
        }

    def _interpreter(self, failed: list[bool]):
        """Names -> (skill_id, similarity) | None, if the similarity provider can read free text.

        A failing call is recorded in `failed` and re-raised; the normalizer then drops the
        unknown skills as before."""
        interpret = getattr(self.similarity, "interpret", None)
        if not callable(interpret):
            return None

        def interpreter(names):
            try:
                return interpret(names, threshold=scoring.SIMILARITY_THRESHOLD)
            except Exception:
                failed.append(True)
                raise
        return interpreter

    def _score_role(self, profile, profile_skills, role, multipliers, applied_signals, scenario_notes,
                    interpreted: dict[str, Interpretation] | None = None) -> dict:
        n = self.normalizer
        interpreted = interpreted or {}
        s, matched, missing, skill_notes = scoring.skills_component(
            profile_skills, role, multipliers, n.name_of, self.similarity, interpreted
        )
        e, exp_notes = scoring.experience_component(profile, role, n.find_in_text)
        q, prereq_caveats = scoring.prerequisites_component(profile, role)
        t = scoring.transferable_component(profile_skills, role, profile.get("interests"), interpreted)

        breakdown = {"skills": s, "experience": e, "prerequisites": q, "transferable": t}
        total = scoring.combine(breakdown)

        role_skill_ids = {r["skill_id"] for r in role["required_skills"]}
        role_signals = [sig for sig in applied_signals if sig["skill_id"] in role_skill_ids]

        used = role_skill_ids | set(role.get("transferable_skills") or [])
        interpretation_notes = [i.message() for sid, i in interpreted.items() if sid in used]

        caveats = list(prereq_caveats) + interpretation_notes + skill_notes + exp_notes + scenario_notes
        if role_signals:
            names = sorted({n.name_of(sig["skill_id"]) for sig in role_signals})
            kinds = sorted({
                SIGNAL_TYPE_LABELS.get(sig.get("signal_type"), sig.get("signal_type") or "unspecified-type")
                for sig in role_signals
            })
            caveats.append(
                "Scenario adjusted the weight of: " + ", ".join(names)
                + f" (based on dated {' and '.join(kinds)} signals; an assumption, not a forecast)."
            )
        if role.get("skills_coverage") == "limited":
            caveats.append(LIMITED_COVERAGE_CAVEAT)
        if not profile_skills:
            caveats.append(NO_SKILLS_CAVEAT)
        if role.get("data_mode") == "fixture":
            caveats.append("Fixture role for testing; not verified occupational data.")

        required = [r for r in role["required_skills"] if r.get("required", True)]
        required_held = sum(1 for r in required
                            if r["skill_id"] in profile_skills and r["skill_id"] not in interpreted)
        required_interpreted = sum(1 for r in required if r["skill_id"] in interpreted)
        explanation = (
            f"You have {required_held} of {len(required)} core skills for "
            f"{role['role_title']}"
            + (f" (plus {required_interpreted} interpreted from your wording, partial credit)"
               if required_interpreted else "")
            + f". Skill coverage {round(s)}/100, experience "
            f"{round(e)}/100, "
            + (f"prerequisites {round(q)}/100" if q is not None else "prerequisites not assessed")
            + (f", transferable skills {round(t)}/100" if t is not None else "")
            + ". This is an estimated profile alignment, not a hiring prediction."
        )

        evidence_ids = list(role.get("evidence_ids") or [])
        for sig in role_signals:
            if sig.get("source_id") and sig["source_id"] not in evidence_ids:
                evidence_ids.append(sig["source_id"])

        return {
            "role_id": role["role_id"],
            "role_title": role["role_title"],
            "score": total,
            "score_type": scoring.SCORE_TYPE,
            "matched_skills": matched,
            "missing_skills": missing,
            "score_breakdown": {
                "skills": round(s),
                "experience": round(e),
                # contract requires a number; None means "not defined for this role"
                "prerequisites": round(q) if q is not None else 0,
                # contract requires a number; None means "not defined for this role"
                "transferable": round(t) if t is not None else 0,
            },
            "evidence_ids": evidence_ids,
            "explanation": explanation,
            "caveats": caveats,
        }


def match(profile, roles, scenario=None, signals=None, *, normalizer: SkillNormalizer,
          similarity=None, limit: int = DEFAULT_LIMIT) -> list[dict]:
    """Adapter interface from the contract: MatchingProvider.match(...) -> RoleMatch[]."""
    return Matcher(normalizer, similarity).match_roles(
        profile, roles, scenario, signals, limit
    )["matches"]
