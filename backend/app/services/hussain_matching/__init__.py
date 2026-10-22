# Vendored verbatim from origin/feature/hussain-matching @ 61373a5 (owner: Hussain).
# Source: services/matching/__init__.py on that branch. Not modified from the original.
"""FuturePath AI matching service (owner: Hussain)."""
from .matcher import Matcher, match
from .normalizer import SkillNormalizer
from .scenarios import get_scenario

__all__ = ["Matcher", "match", "SkillNormalizer", "get_scenario"]
