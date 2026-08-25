# models/question.py
# ─────────────────────────────────────────────────────────────────────────────
# Question and QuestionOption models.
#
# SECURITY NOTE: QuestionOption.is_correct is NEVER included in any API
# response schema. It is only read server-side during answer validation.
# The Pydantic response schemas (in /schemas/) enforce this boundary.
# ─────────────────────────────────────────────────────────────────────────────

import enum
from sqlalchemy import (
    Column, Integer, String, Text,
    Boolean, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from database import Base


class QuestionType(str, enum.Enum):
    """
    Supported question types.
    MVP focuses on MCQ only — other types are seeded but not actively served.
    Using Python enums + SAEnum ensures DB and code stay in sync.
    """
    MCQ          = "mcq"           # Multiple choice (4 options, 1 correct)
    TRUE_FALSE   = "true_false"    # Binary choice
    CODE_SNIPPET = "code_snippet"  # Future: code-based questions


class DifficultyLevel(str, enum.Enum):
    """
    Three-tier difficulty system.
    Ahmed Ali's assessment engine uses this to select questions based on
    the user's declared skill level during onboarding.
    """
    BEGINNER     = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED     = "advanced"


class Question(Base):
    __tablename__ = "questions"

    id          = Column(Integer, primary_key=True, index=True)
    skill_id    = Column(
        Integer,
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text        = Column(Text, nullable=False)
    type        = Column(
        SAEnum(QuestionType),
        nullable=False,
        default=QuestionType.MCQ,
    )
    difficulty  = Column(
        SAEnum(DifficultyLevel),
        nullable=False,
        default=DifficultyLevel.INTERMEDIATE,
    )
    # Points awarded for a correct answer — used in score calculation
    # Beginner=1, Intermediate=2, Advanced=3 is a sensible default
    points      = Column(Integer, default=1, nullable=False)

    # Explanation shown to the user AFTER they answer
    # This is safe to expose — it's educational, not a spoiler
    explanation = Column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    skill   = relationship("Skill", back_populates="questions")
    options = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="select",
    )
    assessment_questions = relationship(
        "AssessmentQuestion",
        back_populates="question",
        lazy="select",
    )
    responses = relationship(
        "UserResponse",
        back_populates="question",
        lazy="select",
    )

    def __repr__(self):
        return (
            f"<Question id={self.id} skill_id={self.skill_id} "
            f"difficulty='{self.difficulty}'>"
        )


class QuestionOption(Base):
    """
    Represents a single answer option for a Question.
    
    ⚠️  SECURITY BOUNDARY:
    The `is_correct` field MUST NOT appear in any schema that is serialized
    and sent to the frontend. It is only accessed in:
      services/assessment_service.py → validate_answer()
    """
    __tablename__ = "question_options"

    id          = Column(Integer, primary_key=True, index=True)
    question_id = Column(
        Integer,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text        = Column(Text, nullable=False)

    # ⚠️  NEVER expose this field in API responses
    is_correct  = Column(Boolean, default=False, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    question  = relationship("Question", back_populates="options")
    responses = relationship("UserResponse", back_populates="selected_option")

    def __repr__(self):
        return (
            f"<QuestionOption id={self.id} question_id={self.question_id} "
            f"is_correct={self.is_correct}>"
        )
