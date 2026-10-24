"""Persistence service for StudentProfile — the only DB-backed feature in Milestone 2.

No matching/trend/roadmap logic here; this layer only creates, looks up and
updates rows per the contract's single POST /profile/analyze endpoint.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models import StudentProfileORM, StudentProfileSkillORM
from app.schemas.profile import SkillRef, StudentProfile


def _new_profile_id() -> str:
    return f"profile_{uuid.uuid4().hex}"


def to_schema(model: StudentProfileORM) -> StudentProfile:
    return StudentProfile(
        profile_id=model.profile_id,
        education_level=model.education_level,
        degree=model.degree,
        semester=model.semester,
        target_role_id=model.target_role_id,
        interests=list(model.interests or []),
        skills=[
            SkillRef(skill_id=s.skill_id, name=s.name, proficiency=s.proficiency)
            for s in model.skills
        ],
        projects=list(model.projects or []),
        experience_summary=model.experience_summary,
    )


class ProfileService:
    """Repository/service layer for student_profiles. No routing or business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, profile_id: str) -> StudentProfileORM | None:
        return self.db.get(StudentProfileORM, profile_id)

    def upsert(self, payload: StudentProfile) -> tuple[StudentProfileORM, bool]:
        """Create a profile, or update one whose profile_id already exists.

        The contract defines no separate create/update routes, so intent is
        inferred here: no profile_id -> create; a known profile_id -> update;
        an unknown, client-supplied profile_id -> 404 (never silently created).
        """
        now = datetime.now(timezone.utc)

        if payload.profile_id:
            existing = self.get(payload.profile_id)
            if existing is None:
                raise AppError(
                    code="PROFILE_NOT_FOUND",
                    message=f"No profile found with profile_id '{payload.profile_id}'.",
                    status_code=404,
                )
            self._apply(existing, payload, now)
            created = False
        else:
            existing = StudentProfileORM(profile_id=_new_profile_id(), created_at=now)
            self._apply(existing, payload, now)
            self.db.add(existing)
            created = True

        try:
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise AppError(
                code="PROFILE_PERSISTENCE_ERROR",
                message="Could not save the student profile.",
                status_code=500,
            ) from None

        self.db.refresh(existing)
        return existing, created

    def _apply(self, model: StudentProfileORM, payload: StudentProfile, now: datetime) -> None:
        model.education_level = payload.education_level
        model.degree = payload.degree
        model.semester = payload.semester
        model.target_role_id = payload.target_role_id
        model.interests = list(payload.interests)
        model.projects = list(payload.projects)
        model.experience_summary = payload.experience_summary
        model.updated_at = now

        # Flushing the delete-orphan removals before re-adding avoids a
        # transient unique-constraint collision when a skill_id is kept
        # across an update (clear+append in one flush can insert the new
        # row before the old one's delete is applied).
        model.skills.clear()
        self.db.flush()
        for skill in payload.skills:
            model.skills.append(
                StudentProfileSkillORM(
                    skill_id=skill.skill_id,
                    name=skill.name,
                    proficiency=skill.proficiency,
                )
            )
