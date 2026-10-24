"""Synthetic, fictional demonstration profiles — no real people, no protected data.

StudentProfile (per contracts/openapi.yaml) has no name/email field by design
(CLAUDE.md: "No protected personal data"), so these fixtures only use the
fields the contract actually defines. Used by tests only; nothing here is
inserted into any database automatically on application startup.
"""
from app.schemas.profile import SkillRef, StudentProfile

SAMPLE_PROFILES: dict[str, StudentProfile] = {
    "cs_undergrad_data": StudentProfile(
        education_level="undergraduate",
        degree="Computer Science",
        semester=4,
        interests=["analytics", "data engineering"],
        skills=[
            SkillRef(skill_id="sql", name="SQL", proficiency="intermediate"),
            SkillRef(skill_id="python", name="Python", proficiency="intermediate"),
        ],
        projects=["Fictional course project: sales dashboard with SQL + Python"],
        experience_summary="Fictional demo profile for contract/testing purposes only.",
    ),
    "business_finance_student": StudentProfile(
        education_level="undergraduate",
        degree="Business Administration",
        semester=6,
        interests=["fintech", "financial analysis"],
        skills=[
            SkillRef(skill_id="excel", name="Excel", proficiency="advanced"),
            SkillRef(skill_id="accounting", name="Accounting", proficiency="beginner"),
        ],
        projects=["Fictional case study: budget forecasting model"],
        experience_summary="Fictional demo profile for contract/testing purposes only.",
    ),
    "engineering_fresh_grad": StudentProfile(
        education_level="fresh_graduate",
        degree="Mechanical Engineering",
        semester=8,
        interests=["robotics", "renewable energy"],
        skills=[
            SkillRef(skill_id="cad", name="CAD", proficiency="advanced"),
            SkillRef(skill_id="python", name="Python", proficiency="beginner"),
        ],
        projects=["Fictional capstone: small-scale solar tracker prototype"],
        experience_summary="Fictional demo profile for contract/testing purposes only.",
    ),
}
