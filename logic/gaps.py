"""
logic/gaps.py

Skill gap analysis logic.

A 'gap' exists for a skill when the user's current score falls below
the target score required for their chosen career. Gaps are prioritised
by a combination of the shortfall magnitude and the skill's career weight.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .scoring import SkillScore


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_TARGET_SCORE = 75.0   # Target proficiency percentage
HIGH_GAP_THRESHOLD   = 40.0   # Gap >= this is 'high' priority
MEDIUM_GAP_THRESHOLD = 20.0   # Gap >= this is 'medium' priority


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class SkillGap:
    skill_slug: str
    skill_name: str
    current_score: float
    target_score: float
    gap: float                              # target - current (always >= 0)
    priority: Literal["high", "medium", "low"]
    career_weight: float                    # importance weight from career
    priority_score: float                   # composite sort key (higher = do first)


# ---------------------------------------------------------------------------
# Core gap-analysis function
# ---------------------------------------------------------------------------

def identify_skill_gaps(
    skill_scores: list[SkillScore],
    target_scores: dict[str, float] | None = None,
) -> list[SkillGap]:
    """
    Identify and prioritise skill gaps from assessment results.

    Parameters
    ----------
    skill_scores : list[SkillScore]
        Per-skill scoring results from `compute_assessment_score`.
    target_scores : dict[str, float] | None
        Optional mapping of skill_slug -> target percentage.
        Falls back to DEFAULT_TARGET_SCORE for any missing slug.

    Returns
    -------
    list[SkillGap]
        Gaps sorted by priority_score descending (highest priority first).
        Skills that already meet or exceed their target are excluded.
    """

    target_scores = target_scores or {}
    gaps: list[SkillGap] = []

    for skill in skill_scores:
        target = target_scores.get(skill.skill_slug, DEFAULT_TARGET_SCORE)
        gap_value = max(target - skill.score, 0.0)

        # No gap — skip
        if gap_value <= 0.0:
            continue

        priority = _classify_priority(gap_value)
        priority_score = _compute_priority_score(gap_value, skill.weight)

        gaps.append(
            SkillGap(
                skill_slug=skill.skill_slug,
                skill_name=skill.skill_name,
                current_score=skill.score,
                target_score=target,
                gap=round(gap_value, 2),
                priority=priority,
                career_weight=skill.weight,
                priority_score=round(priority_score, 4),
            )
        )

    # Sort: highest priority_score first
    gaps.sort(key=lambda g: g.priority_score, reverse=True)
    return gaps


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify_priority(
    gap: float,
) -> Literal["high", "medium", "low"]:
    """Convert a raw gap value to a priority label."""
    if gap >= HIGH_GAP_THRESHOLD:
        return "high"
    if gap >= MEDIUM_GAP_THRESHOLD:
        return "medium"
    return "low"


def _compute_priority_score(gap: float, weight: float) -> float:
    """
    Composite priority score for sorting.

    Formula: gap * weight
    This ensures a highly-weighted skill with a moderate gap can
    outrank a low-weight skill with a large gap.
    """
    return gap * weight
