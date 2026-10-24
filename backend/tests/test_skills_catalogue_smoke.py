"""Milestone 12B-4, requirement 5: an offline smoke test that constructs
SkillNormalizer from the FULL real, committed app/data/cached/skills.json
and verifies it has no alias/name collisions across different skill_ids.

Why this matters: role_catalog_cached._validate_skills() only checks for
duplicate skill_ids — it never checks alias uniqueness. Alias-collision
detection only happens lazily, inside SkillNormalizer.__init__
(app/services/hussain_matching/normalizer.py), which raises a bare,
uncaught ValueError on a collision. app/services/cv_extraction_service.py
constructs exactly this SkillNormalizer on every POST /api/v1/cv/parse
request with no try/except around it — so a colliding alias anywhere in
skills.json (e.g. from a future catalogue update, like the proposed CV
aliases referenced in the 12B audit) would crash every CV upload with an
unhandled 500 until caught. This test is the pre-flight check that catches
that *before* any such change is merged, not after a request fails in
production.
"""
from __future__ import annotations

from app.services.hussain_matching.normalizer import SkillNormalizer
from app.services.role_catalog_cached import _load_json


def _load_real_skills_catalogue() -> list[dict]:
    return _load_json("skills.json")["skills"]


def test_full_cached_skills_catalogue_has_no_alias_collisions():
    """The exact construction app/services/cv_extraction_service.py performs
    on every /cv/parse request, against the real committed skills.json —
    must never raise."""
    catalogue = _load_real_skills_catalogue()
    normalizer = SkillNormalizer(catalogue)  # raises ValueError on any collision

    # Sanity: every real skill_id actually round-trips through the
    # normalizer it was built from (proves it loaded, not just "didn't crash").
    for skill in catalogue:
        result = normalizer.normalize(skill["skill_id"])
        assert result.skill_id == skill["skill_id"]


def test_every_alias_and_name_in_the_real_catalogue_maps_to_its_own_skill():
    """A second, explicit pass: every name/alias string in the real
    catalogue, normalized, must resolve back to the skill_id it was
    declared under — never a different skill_id (which is exactly what a
    collision would otherwise mean, if SkillNormalizer's constructor-time
    check were ever loosened or bypassed)."""
    catalogue = _load_real_skills_catalogue()
    normalizer = SkillNormalizer(catalogue)

    for skill in catalogue:
        texts = [skill["name"], skill["skill_id"], *skill.get("aliases", [])]
        for text in texts:
            result = normalizer.normalize(text)
            assert result.skill_id == skill["skill_id"], (
                f"{text!r} (declared under {skill['skill_id']}) resolved to "
                f"{result.skill_id!r} instead"
            )


def test_real_catalogue_has_no_duplicate_skill_ids():
    catalogue = _load_real_skills_catalogue()
    ids = [s["skill_id"] for s in catalogue]
    assert len(ids) == len(set(ids))
