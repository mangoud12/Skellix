"""
logic/scoring.py

Assessment scoring logic.

Responsibilities:
  - Compare submitted answers against correct answers.
  - Calculate per-skill scores (raw + percentage).
  - Calculate the weighted overall score for the career.
  - Derive proficiency level labels per skill.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PASSING_THRESHOLD = 60.0  # Overall score (%) required to pass

LEVEL_THRESHOLDS: list[tuple[float, str]] = [
    (80.0, "advanced"),
    (50.0, "intermediate"),
    (0.0, "beginner"),
]


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class SkillScore:
    skill_slug: str
    skill_name: str
    correct: int = 0
    total: int = 0
    earned_points: int = 0
    max_points: int = 0
    score: float = 0.0        # percentage 0-100
    level: str = "beginner"
    weight: float = 1.0       # career-importance weight


@dataclass
class ScoringResult:
    assessment_id: int
    user_id: int
    career_id: int
    career_title: str
    skill_scores: list[SkillScore] = field(default_factory=list)
    overall_score: float = 0.0
    passed: bool = False


# ---------------------------------------------------------------------------
# Core scoring function
# ---------------------------------------------------------------------------

def compute_assessment_score(
    *,
    assessment_id: int,
    user_id: int,
    career_id: int,
    career_title: str,
    submitted_answers: list[dict[str, str]],
    questions: list[Any],          # list of Question ORM objects or dicts
    career_skill_weights: dict[str, float],  # {skill_slug: weight}
    skill_names: dict[str, str],             # {skill_slug: display_name}
) -> ScoringResult:
    """
    Compute the full scoring result for a submitted assessment.

    Parameters
    ----------
    assessment_id : int
        ID of the assessment session being scored.
    user_id : int
        ID of the user being assessed.
    career_id : int
        ID of the target career.
    career_title : str
        Display name of the target career.
    submitted_answers : list[dict]
        Each dict has keys: {"question_slug": str, "selected_option": str}.
    questions : list
        Question ORM objects (or dicts) with attributes:
        slug, skill_slug, answer, points.
    career_skill_weights : dict
        Mapping of skill_slug -> weight (floats that should sum to ~1.0).
    skill_names : dict
        Mapping of skill_slug -> human-readable name.

    Returns
    -------
    ScoringResult
        Fully populated result including per-skill and overall scores.
    """

    # ------------------------------------------------------------------
    # 1. Build an answer lookup: question_slug -> selected_option
    # ------------------------------------------------------------------
    answer_map: dict[str, str] = {
        a["question_slug"]: a["selected_option"]
        for a in submitted_answers
    }

    # ------------------------------------------------------------------
    # 2. Build per-skill accumulators
    # ------------------------------------------------------------------
    skill_accumulators: dict[str, SkillScore] = {}

    for question in questions:
        # Support both ORM objects and plain dicts
        if isinstance(question, dict):
            slug = question["slug"]
            skill_slug = question["skill_slug"]
            correct_answer = question["answer"]
            points = question["points"]
        else:
            slug = question.slug
            skill_slug = question.skill_slug
            correct_answer = question.answer
            points = question.points

        if skill_slug not in skill_accumulators:
            skill_accumulators[skill_slug] = SkillScore(
                skill_slug=skill_slug,
                skill_name=skill_names.get(skill_slug, skill_slug),
                weight=career_skill_weights.get(skill_slug, 1.0),
            )

        acc = skill_accumulators[skill_slug]
        acc.total += 1
        acc.max_points += points

        submitted = answer_map.get(slug, "")
        if submitted.strip().lower() == correct_answer.strip().lower():
            acc.correct += 1
            acc.earned_points += points

    # ------------------------------------------------------------------
    # 3. Calculate per-skill percentage scores and proficiency levels
    # ------------------------------------------------------------------
    for acc in skill_accumulators.values():
        if acc.max_points > 0:
            acc.score = round((acc.earned_points / acc.max_points) * 100, 2)
        else:
            acc.score = 0.0
        acc.level = _derive_level(acc.score)

    # ------------------------------------------------------------------
    # 4. Calculate weighted overall score
    # ------------------------------------------------------------------
    total_weight = sum(acc.weight for acc in skill_accumulators.values())
    if total_weight > 0:
        overall = sum(
            acc.score * acc.weight
            for acc in skill_accumulators.values()
        ) / total_weight
    else:
        overall = 0.0

    overall = round(overall, 2)

    return ScoringResult(
        assessment_id=assessment_id,
        user_id=user_id,
        career_id=career_id,
        career_title=career_title,
        skill_scores=list(skill_accumulators.values()),
        overall_score=overall,
        passed=overall >= PASSING_THRESHOLD,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _derive_level(score: float) -> str:
    """Map a percentage score to a proficiency level string."""
    for threshold, label in LEVEL_THRESHOLDS:
        if score >= threshold:
            return label
    return "beginner"
