# models/result.py

import enum
from sqlalchemy import (
    Column, Integer, String, Float, Text,
    Boolean, DateTime, ForeignKey, JSON,
    Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class ReadinessLevel(str, enum.Enum):
    BEGINNER     = "beginner"     # 0–40%
    INTERMEDIATE = "intermediate" # 41–65%
    ADVANCED     = "advanced"     # 66–85%
    READY        = "ready"        # 86–100%


class Result(Base):
    __tablename__ = "results"

    id            = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(
        Integer,
        ForeignKey("assessments.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    overall_score = Column(Float, nullable=False)
    skill_scores  = Column(JSON, nullable=False, default=dict)
    strengths     = Column(JSON, nullable=False, default=list)
    weaknesses    = Column(JSON, nullable=False, default=list)
    skill_gaps    = Column(JSON, nullable=False, default=list)

    level = Column(
        SAEnum(ReadinessLevel),
        nullable=False,
        default=ReadinessLevel.BEGINNER,
    )

    ai_feedback = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    assessment = relationship("Assessment", back_populates="result")
    
    # تم تعديل الربط ليعتمد على assessment_id كربط غير مباشر
    roadmap = relationship(
        "Roadmap",
        primaryjoin="Result.assessment_id == Roadmap.assessment_id",
        foreign_keys="[Roadmap.assessment_id]",
        uselist=False,
        viewonly=True,
    )

    def __repr__(self):
        return (
            f"<Result id={self.id} assessment_id={self.assessment_id} "
            f"overall_score={self.overall_score} level='{self.level}'>"
        )


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id            = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(
        Integer,
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    career_id     = Column(
        Integer,
        ForeignKey("careers.id", ondelete="CASCADE"),
        nullable=False,
    )

    steps       = Column(JSON, nullable=False, default=list)
    ai_enhanced = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    result = relationship(
        "Result",
        primaryjoin="Roadmap.assessment_id == Result.assessment_id",
        foreign_keys="[Result.assessment_id]",
        uselist=False,
        viewonly=True,
    )
    career = relationship("Career")

    def __repr__(self):
        return (
            f"<Roadmap id={self.id} assessment_id={self.assessment_id} "
            f"ai_enhanced={self.ai_enhanced}>"
        )