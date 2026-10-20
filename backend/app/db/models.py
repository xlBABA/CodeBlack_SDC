"""Student profile ORM models — the only persistence surface added in Milestone 2.

No role/skill-catalog/trend/SDG tables here; those belong to Jawad's/Hussain's
domains and are out of scope for backend profile intake.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class StudentProfileORM(Base):
    __tablename__ = "student_profiles"

    profile_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    education_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    degree: Mapped[str | None] = mapped_column(String(200), nullable=True)
    semester: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_role_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    interests: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    projects: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    experience_summary: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    skills: Mapped[list["StudentProfileSkillORM"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="StudentProfileSkillORM.id",
    )


class StudentProfileSkillORM(Base):
    __tablename__ = "student_profile_skills"
    __table_args__ = (UniqueConstraint("profile_id", "skill_id", name="uq_profile_skill"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("student_profiles.profile_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    skill_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    proficiency: Mapped[str | None] = mapped_column(String(20), nullable=True)

    profile: Mapped[StudentProfileORM] = relationship(back_populates="skills")
