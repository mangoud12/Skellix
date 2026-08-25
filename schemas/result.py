"""
schemas/result.py

Pydantic schemas for assessment results and per-skill scoring.
"""

from pydantic import BaseModel, Field
from datetime import datetime


class SkillResult(BaseModel):
    """Score breakdown for a single skill."""

    skill_slug: str
    skill_name: str
    score: float = Field(
        ge=0.0,
        le=100.0,
        description="Percentage score for this skill (0–100).",
    )
    correct: int = Field(ge=0, description="Number of correct answers.")
    total: int = Field(ge=0, description="Total questions answered for this skill.")
    level: str = Field(
        description="Derived proficiency level: 'beginner', 'intermediate', or 'advanced'."
    )

    model_config = {"from_attributes": True}


class AssessmentResultOut(BaseModel):
    """Full assessment result returned after submission."""

    assessment_id: int
    user_id: int
    career_id: int
    career_title: str
    overall_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Weighted overall score across all assessed skills (0–100).",
    )
    skill_results: list[SkillResult]
    completed_at: datetime
    passed: bool = Field(
        description="True if overall_score >= passing threshold (default 60)."
    )

    model_config = {"from_attributes": True}
