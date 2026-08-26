"""
schemas/assessment.py

Pydantic schemas for assessment session creation, question delivery,
and answer submission.
"""

from pydantic import BaseModel, Field
from typing import Literal


class QuestionOut(BaseModel):
    """A single question delivered to the client (no answer/explanation exposed)."""

    id: str
    slug: str                         # e.g. "py_001"
    skill_slug: str
    difficulty: Literal["beginner", "intermediate", "advanced"]
    points: int = Field(ge=1)
    question_text: str
    options: list[str]

    model_config = {"from_attributes": True}


class AssessmentCreate(BaseModel):
    """Request body for starting a new assessment session."""

    user_id: int
    career_id: int
    skill_slugs: list[str] | None = Field(
        default=None,
        description="Optional subset of skill slugs to assess. Defaults to all skills for the career.",
    )
    questions_per_skill: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of questions to serve per skill topic.",
    )


class AnswerIn(BaseModel):
    """A single submitted answer."""

    question_slug: str
    selected_option: str


class AssessmentSubmit(BaseModel):
    """Request body for submitting a completed assessment."""

    assessment_id: int
    answers: list[AnswerIn] = Field(min_length=1)


class AssessmentStartRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=120)
    experience: Literal["none", "beginner", "intermediate", "advanced"] = "beginner"
    question_count: int = Field(default=8, ge=8, le=10, description="8–10 fresh questions per skill")
    difficulty: Literal["beginner", "intermediate", "advanced"] | None = None


class SubmittedAnswer(BaseModel):
    question_id: str
    selected_option: str


class AssessmentSubmitRequest(BaseModel):
    answers: list[SubmittedAnswer] = Field(min_length=1)
