# models/assessment.py
# ─────────────────────────────────────────────────────────────────────────────
# Assessment: A single test session for a user targeting a specific career.
# AssessmentQuestion: Tracks which questions were served to which assessment
#                     (prevents repeats + enables progress tracking).
# ─────────────────────────────────────────────────────────────────────────────

import enum
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column, Integer, String, Text,
    DateTime, ForeignKey, JSON,
    Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class AssessmentStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"
    ABANDONED   = "abandoned"  # Future: timeout/exit tracking
    EXPIRED     = "expired"


# API session contracts live alongside the persisted SQLAlchemy models.  The
# distinct names avoid conflating transient API sessions with DB rows.
class AssessmentQuestionOut(BaseModel):
    id: str
    question_text: str
    options: list[str]
    difficulty: str


class AssessmentSession(BaseModel):
    id: str
    topic: str
    experience: str
    status: AssessmentStatus = AssessmentStatus.IN_PROGRESS
    questions: list[AssessmentQuestionOut] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AssessmentResult(BaseModel):
    score_percent: float
    correct_count: int
    total_questions: int
    feedback: str = ""
    mistakes: list[dict] = Field(default_factory=list)
    skill_profile: dict[str, float] = Field(default_factory=dict)


class Assessment(Base):
    __tablename__ = "assessments"

    id         = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        String(36),
        ForeignKey("users.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    career_id  = Column(
        Integer,
        ForeignKey("careers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # user_skills: the skills the user CLAIMED to have at the start.
    # Stored as JSON array of skill slugs: ["python", "machine_learning"]
    # This is an input, not a computed result — important distinction.
    user_skills = Column(JSON, nullable=False, default=list)

    status = Column(
        SAEnum(AssessmentStatus),
        nullable=False,
        default=AssessmentStatus.IN_PROGRESS,
    )

    created_at   = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,  # NULL until the user finishes
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user   = relationship("User", back_populates="assessments")
    career = relationship("Career", back_populates="assessments")

    served_questions = relationship(
        "AssessmentQuestion",
        back_populates="assessment",
        cascade="all, delete-orphan",
        lazy="select",
    )
    responses = relationship(
        "UserResponse",
        back_populates="assessment",
        cascade="all, delete-orphan",
        lazy="select",
    )
    result = relationship(
        "Result",
        back_populates="assessment",
        uselist=False,              # One assessment → exactly one result
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return (
            f"<Assessment id={self.id} career_id={self.career_id} "
            f"status='{self.status}'>"
        )


class AssessmentQuestion(Base):
    """
    Tracks every question that has been served to a specific assessment.
    
    Purpose:
    1. Prevent the same question from being served twice in one assessment
    2. Enable progress tracking (X of Y questions answered)
    3. Audit trail for result verification
    """
    __tablename__ = "assessment_questions"

    id            = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(
        Integer,
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id      = Column(
        Integer,
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id   = Column(
        Integer,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    served_at     = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    assessment = relationship("Assessment", back_populates="served_questions")
    skill      = relationship("Skill")
    question   = relationship("Question", back_populates="assessment_questions")

    def __repr__(self):
        return (
            f"<AssessmentQuestion assessment_id={self.assessment_id} "
            f"question_id={self.question_id}>"
        )
