"""
schemas/__init__.py

Re-exports all public Pydantic schemas for convenient importing:
    from schemas import CareerOut, AssessmentCreate, ResultOut, RoadmapOut
"""

from .career import CareerBase, CareerOut, CareerWithSkills, SkillBrief
from .assessment import (
    QuestionOut,
    AssessmentCreate,
    AssessmentSubmit,
    AnswerIn,
)
from .result import SkillResult, AssessmentResultOut
from .roadmap import RoadmapStep, RoadmapOut

__all__ = [
    # Career
    "CareerBase",
    "CareerOut",
    "CareerWithSkills",
    "SkillBrief",
    # Assessment
    "QuestionOut",
    "AssessmentCreate",
    "AssessmentSubmit",
    "AnswerIn",
    # Result
    "SkillResult",
    "AssessmentResultOut",
    # Roadmap
    "RoadmapStep",
    "RoadmapOut",
]
