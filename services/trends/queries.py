"""Skill -> GitHub topic map. Every topic here was checked live (real, non-zero
30-day repo counts) on 2026-10-21 before being added - see README.md for the
exact numbers. Skills with no clear, honest GitHub correlate are listed in
NOT_COVERED_SKILLS with the reason instead of being guessed.
"""
from __future__ import annotations

# skill_id -> GitHub topic (used as `topic:<value>` in the search query)
COVERED_SKILLS: dict[str, str] = {
    "sql": "sql",
    "python": "python",
    "matlab": "matlab",
    "data_visualization": "data-visualization",
    "excel": "excel",
    "vba": "vba",
    "cad_software": "cad",
    "financial_analysis_software": "financial-analysis",
}

# skill_id -> why it is NOT scored (never guessed a topic to fill the gap)
NOT_COVERED_SKILLS: dict[str, str] = {
    "critical_thinking": (
        "Cognitive/soft skill; no GitHub topic represents 'use of critical "
        "thinking' the way a topic can represent adoption of a tool."
    ),
    "mathematics": (
        "A 'mathematics' topic exists (~613 new repos/30d, checked "
        "2026-10-21) but it tags repos about math content/algorithms, not "
        "use of mathematics as a workplace skill - too indirect a proxy, so "
        "left unscored rather than guessed."
    ),
    "complex_problem_solving": "Cognitive/soft skill; no GitHub topic correlate.",
    "systems_analysis": "Cognitive/soft skill; no GitHub topic correlate.",
    "attention_to_detail": (
        "Cognitive/soft skill (an O*NET Work Style, not a tool); no GitHub "
        "topic correlate."
    ),
    "analytical_scientific_software": (
        "Covers SPSS/SAS/Stata collectively. Each has its own GitHub topic "
        "but at very low, noisy volume (checked 2026-10-21: spss 24, stata "
        "30, sas 33 new repos/30d) and no single topic represents all three "
        "without arbitrarily picking one."
    ),
}
