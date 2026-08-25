# models/response.py
# ─────────────────────────────────────────────────────────────────────────────
# UserResponse: Records a single answer submission.
# is_correct is computed SERVER-SIDE at submission time by comparing
# selected_option_id against QuestionOption.is_correct — never trusted from client.
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy import (
    Column, Integer, Boolean,
    DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class UserResponse(Base):
    __tablename__ = "user_responses"

    id                 = Column(Integer, primary_key=True, index=True)
    assessment_id      = Column(
        Integer,
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id        = Column(
        Integer,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    selected_option_id = Column(
        Integer,
        ForeignKey("question_options.id", ondelete="SET NULL"),
        nullable=True,  # NULL = question was skipped (future feature)
    )

    # Computed and stored at answer submission time — never client-provided
    is_correct         = Column(Boolean, nullable=False, default=False)

    # Optional: useful for future adaptive difficulty or analytics
    # How long the user spent on this question (in seconds)
    time_taken_seconds = Column(Integer, nullable=True)

    answered_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    assessment      = relationship("Assessment", back_populates="responses")
    question        = relationship("Question", back_populates="responses")
    selected_option = relationship("QuestionOption", back_populates="responses")

    def __repr__(self):
        return (
            f"<UserResponse assessment_id={self.assessment_id} "
            f"question_id={self.question_id} is_correct={self.is_correct}>"
        )
