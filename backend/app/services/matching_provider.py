"""Deterministic fixture MatchingProvider — no RunPod, LLM, or network calls.

Satisfies app.services.interfaces.MatchingProvider's
match(profile, roles, scenario, signals) shape. Scoring weights and
heuristics are intentionally simple and fully visible here so judges and
teammates can audit them; they are an explicit placeholder for Hussain's
real scoring model (services/matching/**), not a claim of hiring
probability or eligibility.
"""
from __future__ import annotations

from app.schemas.matching import RoleMatch, ScoreBreakdown
from app.schemas.profile import SkillRef, StudentProfile
from app.services.role_catalog import RoleFixture

# Weighted blend documented here, not hidden in a formula elsewhere.
_SKILLS_WEIGHT = 0.5
_PREREQUISITES_WEIGHT = 0.25
_EXPERIENCE_WEIGHT = 0.15
_TRANSFERABLE_WEIGHT = 0.10


def _skills_score(
    profile_skill_ids: set[str], role: RoleFixture
) -> tuple[float, list[SkillRef], list[SkillRef], list[SkillRef]]:
    # Score formula unchanged: every required_skills entry (required or
    # optional) still contributes its weight to total_weight/matched_weight
    # exactly as before. Only the unmatched-skill *presentation* below is
    # new — split into real gaps vs. optional, not-yet-demonstrated skills.
    total_weight = sum(req.weight for req in role.required_skills) or 1.0
    matched_weight = 0.0
    matched: list[SkillRef] = []
    missing: list[SkillRef] = []
    optional_missing: list[SkillRef] = []

    for req in role.required_skills:
        if req.skill_id in profile_skill_ids:
            matched_weight += req.weight
            matched.append(SkillRef(skill_id=req.skill_id, name=req.name))
        elif req.required:
            missing.append(SkillRef(skill_id=req.skill_id, name=req.name))
        else:
            # Unmatched but optional (RoleRequirement.required=False, e.g.
            # Jawad's cached roles) — not a mandatory gap, so it must not
            # appear in missing_skills (contracts/API_CONTRACT.md's
            # RoleMatch has no field to tag it there as optional). Not
            # discarded either: surfaced via a caveat in _caveats().
            optional_missing.append(SkillRef(skill_id=req.skill_id, name=req.name))

    score = round(100 * matched_weight / total_weight, 1)
    return score, matched, missing, optional_missing


def _experience_score(profile: StudentProfile) -> float:
    # 0 projects -> 40, 1 -> 60, 2 -> 80, 3+ -> 100. Coarse, documented
    # placeholder pending a real experience-weighting model.
    return float(min(100, 40 + 20 * min(len(profile.projects), 3)))


def _prerequisites_score(profile: StudentProfile, role: RoleFixture) -> float:
    if role.min_semester is None:
        # No semester prerequisite in the source data (e.g. Jawad's cached
        # catalog roles, whose prerequisites list is empty) — nothing to
        # satisfy, never an invented semester number.
        return 100.0
    if profile.semester is None:
        return 50.0  # unknown standing — neutral, not penalized
    if profile.semester >= role.min_semester:
        return 100.0
    return float(max(20, round(100 * profile.semester / role.min_semester)))


def _transferable_score(profile: StudentProfile, role: RoleFixture) -> float:
    if not role.transferable_interests:
        return 50.0
    interests = [interest.lower() for interest in profile.interests]
    matched = any(
        keyword.lower() in interest
        for keyword in role.transferable_interests
        for interest in interests
    )
    return 80.0 if matched else 50.0


def _explanation(matched: list[SkillRef], total_required: int) -> str:
    matched_names = ", ".join(skill.name for skill in matched) or "none"
    return (
        f"Estimated alignment based on {len(matched)}/{total_required} required "
        f"skills present ({matched_names}). This is not a hiring prediction or "
        "eligibility determination."
    )


def _caveats(scenario_id: str | None, optional_missing: list[SkillRef]) -> list[str]:
    caveats = [
        "Fixture role catalog and deterministic matching logic; pending "
        "Jawad's verified 30-role dataset and Hussain's real scoring model.",
        "Score is an estimated profile alignment, not a hiring probability.",
    ]
    if optional_missing:
        names = ", ".join(skill.name for skill in optional_missing)
        caveats.append(
            f"Optional (not required) skills not yet demonstrated: {names}. "
            "Not counted as missing-skill gaps."
        )
    if scenario_id:
        caveats.append(
            f"scenario_id '{scenario_id}' was accepted but not yet applied to "
            "scoring; moderate/fast disruption modeling is a future milestone."
        )
    return caveats


class FixtureMatchingProvider:
    """Satisfies app.services.interfaces.MatchingProvider."""

    def match(
        self,
        profile: StudentProfile,
        roles: list[RoleFixture],
        scenario: str | None,
        signals: list,
    ) -> list[RoleMatch]:
        profile_skill_ids = {skill.skill_id for skill in profile.skills}
        results: list[RoleMatch] = []

        for role in roles:
            skills_score, matched, missing, optional_missing = _skills_score(profile_skill_ids, role)
            experience_score = _experience_score(profile)
            prerequisites_score = _prerequisites_score(profile, role)
            transferable_score = _transferable_score(profile, role)
            required_skill_count = sum(1 for req in role.required_skills if req.required)

            overall = round(
                _SKILLS_WEIGHT * skills_score
                + _EXPERIENCE_WEIGHT * experience_score
                + _PREREQUISITES_WEIGHT * prerequisites_score
                + _TRANSFERABLE_WEIGHT * transferable_score,
                1,
            )

            results.append(
                RoleMatch(
                    role_id=role.role_id,
                    role_title=role.role_title,
                    score=overall,
                    matched_skills=matched,
                    missing_skills=missing,
                    score_breakdown=ScoreBreakdown(
                        skills=skills_score,
                        experience=experience_score,
                        prerequisites=prerequisites_score,
                        transferable=transferable_score,
                    ),
                    evidence_ids=list(role.evidence_ids),
                    explanation=_explanation(matched, required_skill_count),
                    caveats=_caveats(scenario, optional_missing),
                )
            )

        # Deterministic stable ranking: score desc, then role_id asc as tie-break.
        results.sort(key=lambda match: (-match.score, match.role_id))
        return results
