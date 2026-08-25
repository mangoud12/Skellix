# models/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Exports all models from a single entry point.
# This ensures SQLAlchemy's Base.metadata knows about ALL models
# when create_all() is called — regardless of import order elsewhere.
# ─────────────────────────────────────────────────────────────────────────────

from models.career import Career, CareerSkill
from models.skill import Skill
from models.question import Question, QuestionOption
from models.user import User
from models.assessment import Assessment, AssessmentQuestion
from models.response import UserResponse
from models.result import Result, Roadmap

__all__ = [
    "Career",
    "CareerSkill",
    "Skill",
    "Question",
    "QuestionOption",
    "User",
    "Assessment",
    "AssessmentQuestion",
    "UserResponse",
    "Result",
    "Roadmap",
]
