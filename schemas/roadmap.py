"""
schemas/roadmap.py

Pydantic schemas for personalised learning roadmaps generated from
assessment gaps.
"""

from pydantic import BaseModel, Field
from typing import Literal


class Resource(BaseModel):
    """A learning resource attached to a roadmap step."""
    url: str
    resource_type: Literal["article", "video", "course", "documentation", "practice"]
    is_free: bool = True
    estimated_hours: float | None = Field(
        default=None,
        ge=0.1,
        description="Estimated hours to complete the resource.",
    )


class RoadmapStep(BaseModel):
    """A single step in the learning roadmap, targeting one skill gap."""

    order: int = Field(ge=1, description="Step order in the roadmap (1-indexed).")
    skill_slug: str
    skill_name: str
    current_score: float = Field(ge=0.0, le=100.0)
    target_score: float = Field(ge=0.0, le=100.0)
    gap: float = Field(
        ge=0.0,
        description="Difference between target and current score.",
    )
    priority: Literal["high", "medium", "low"]
    description: str = Field(
        description="Short explanation of what to learn and why."
    )
    resources: list[Resource] = Field(default_factory=list)
    estimated_total_hours: float | None = Field(
        default=None,
        description="Total estimated hours to close this gap.",
    )


class RoadmapOut(BaseModel):
    """Full personalised roadmap for a user after an assessment."""

    user_id: int
    career_id: int
    career_title: str
    assessment_id: int
    total_steps: int
    total_estimated_hours: float | None = None
    steps: list[RoadmapStep] = Field(default_factory=list)
