"""Deterministic profile-alignment scoring (methodology v1).

R = 0.50*S + 0.20*E + 0.15*Q + 0.15*T, every component 0..100.

All weights and points below are INITIAL TEAM CHOICES, not research results.
They are kept here in one place so they can be reviewed and tuned.
The score is an estimate of profile alignment, never a hiring probability.
"""
from __future__ import annotations

from typing import Callable

METHODOLOGY_VERSION = "v1"
SCORE_TYPE = "profile_alignment_estimate"

WEIGHTS = {"skills": 0.50, "experience": 0.20, "prerequisites": 0.15, "transferable": 0.15}

# Student-reported proficiency, not verified. Unspecified is treated as intermediate.
PROFICIENCY_FACTOR = {"beginner": 0.60, "intermediate": 0.85, "advanced": 1.00, None: 0.85}
OPTIONAL_SKILL_FACTOR = 0.5  # optional skills count half as much as required ones

# Semantic similarity (embedding model) gives partial credit only.
SIMILARITY_THRESHOLD = 0.75
RELATED_CREDIT = 0.5

# Experience: relevant projects and a relevant experience summary.
POINTS_PER_RELEVANT_PROJECT = 35
MAX_PROJECT_POINTS = 70
EXPERIENCE_SUMMARY_POINTS = 30

UNKNOWN_PREREQUISITE_CREDIT = 0.5

SimilarityFn = Callable[[str, str], float]


def skills_component(
    profile_skills: dict[str, str | None],
    role: dict,
    weight_multipliers: dict[str, float],
    name_of: Callable[[str], str],
    similarity: SimilarityFn | None = None,
) -> tuple[float, list[dict], list[dict], list[str]]:
    """Weighted skill coverage S. Returns (S, matched, missing, notes)."""
    total_weight = 0.0
    earned = 0.0
    matched: list[dict] = []
    missing: list[dict] = []
    notes: list[str] = []

    for req in role["required_skills"]:
        sid = req["skill_id"]
        weight = float(req["importance"])
        if not req.get("required", True):
            weight *= OPTIONAL_SKILL_FACTOR
        weight *= weight_multipliers.get(sid, 1.0)
        total_weight += weight

        if sid in profile_skills:
            prof = profile_skills[sid]
            earned += weight * PROFICIENCY_FACTOR[prof]
            ref = {"skill_id": sid, "name": name_of(sid)}
            if prof:
                ref["proficiency"] = prof
            matched.append(ref)
            continue

        best = None
        if similarity is not None:
            for held in profile_skills:
                sim = similarity(held, sid)
                if sim >= SIMILARITY_THRESHOLD and (best is None or sim > best[1]):
                    best = (held, sim)
        if best:
            earned += weight * RELATED_CREDIT
            notes.append(
                f"{name_of(best[0])} counted as related to {name_of(sid)} "
                f"(similarity {best[1]:.2f}); partial credit only."
            )
        missing.append({"skill_id": sid, "name": name_of(sid)})

    score = 100.0 * earned / total_weight if total_weight else 0.0
    return score, matched, missing, notes


def experience_component(
    profile: dict, role: dict, find_in_text: Callable[[str], set[str]]
) -> tuple[float, list[str]]:
    relevant = {r["skill_id"] for r in role["required_skills"]}
    relevant_projects = sum(
        1 for p in profile.get("projects") or [] if find_in_text(p) & relevant
    )
    points = min(MAX_PROJECT_POINTS, relevant_projects * POINTS_PER_RELEVANT_PROJECT)
    summary = profile.get("experience_summary") or ""
    if find_in_text(summary) & relevant:
        points += EXPERIENCE_SUMMARY_POINTS
    notes = []
    if relevant_projects == 0:
        notes.append("No project mentions a skill this role needs.")
    return float(min(100, points)), notes


def prerequisites_component(profile: dict, role: dict) -> tuple[float, list[str]]:
    prereqs = role.get("prerequisites") or []
    if not prereqs:
        return 100.0, []
    caveats: list[str] = []
    credit = 0.0
    for pre in prereqs:
        if pre["type"] == "min_semester":
            semester = profile.get("semester")
            needed = int(pre["value"])
            if semester is None:
                credit += UNKNOWN_PREREQUISITE_CREDIT
                caveats.append(f"Not provided: {pre['description']}.")
            elif semester >= needed:
                credit += 1.0
            else:
                credit += semester / needed
                caveats.append(f"Usually expected: {pre['description']}.")
            continue
        field = "education_level" if pre["type"] == "education_level" else "degree"
        value = (profile.get(field) or "").strip().lower()
        allowed = [a.lower() for a in pre["allowed"]]
        if not value:
            credit += UNKNOWN_PREREQUISITE_CREDIT
            caveats.append(f"Not provided: {pre['description']}.")
        elif any(a == value or a in value for a in allowed):
            credit += 1.0
        elif pre.get("hard"):
            caveats.append(f"Essential requirement not met: {pre['description']}.")
        else:
            caveats.append(f"Usually expected: {pre['description']}.")
    return 100.0 * credit / len(prereqs), caveats


def transferable_component(
    profile_skills: dict[str, str | None], role: dict, interests: list[str] | None = None
) -> float | None:
    """Share of the role's transferable items the student shows: transferable
    skills they hold plus interest keywords found in their stated interests."""
    skills = role.get("transferable_skills") or []
    keywords = role.get("transferable_interests") or []
    if not skills and not keywords:
        return None  # weight is redistributed
    lowered = [i.lower() for i in interests or []]
    held = sum(1 for sid in skills if sid in profile_skills)
    held += sum(1 for kw in keywords if any(kw.lower() in i for i in lowered))
    return 100.0 * held / (len(skills) + len(keywords))


def combine(breakdown: dict[str, float | None]) -> int:
    """Weighted total. Components that are None are skipped and their weight
    redistributed proportionally."""
    used = {k: v for k, v in breakdown.items() if v is not None}
    weight_sum = sum(WEIGHTS[k] for k in used)
    total = sum(WEIGHTS[k] * v for k, v in used.items()) / weight_sum
    return int(min(100, max(0, total)) + 0.5)
