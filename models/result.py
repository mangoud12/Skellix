# models/result.py
# ─────────────────────────────────────────────────────────────────────────────
# Result: The computed output of a completed assessment.
# Roadmap: The personalized learning plan generated from the result.
#
# KEY DESIGN: ai_feedback is NULLABLE — the app works fully without it.
# Ahmed Ali's logic engine populates the deterministic fields.
# The AI service optionally enriches ai_feedback and roadmap.ai_enhanced.
# ─────────────────────────────────────────────────────────────────────────────

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
    """
    Overall career readiness classification.
    Ahmed Ali's scoring engine determines which level to assign
    based on the overall_score and skill_scores.
    """
    BEGINNER     = "beginner"      # 0–40%
    INTERMEDIATE = "intermediate"  # 41–65%
    ADVANCED     = "advanced"      # 66–85%
    READY        = "ready"         # 86–100%


class Result(Base):
    __tablename__ = "results"

    id            = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(
        Integer,
        ForeignKey("assessments.id", ondelete="CASCADE"),
        unique=True,           # One result per assessment — enforced at DB level
        nullable=False,
        index=True,
    )

    # ── Deterministic Fields (set by Ahmed Ali's Logic Engine) ────────────────

    # Weighted average score across all assessed skills (0.0 to 100.0)
    overall_score = Column(Float, nullable=False)

    # Per-skill scores: {"python": 85.0, "machine_learning": 60.0, ...}
    skill_scores  = Column(JSON, nullable=False, default=dict)

    # Arrays of skill slugs
    strengths     = Column(JSON, nullable=False, default=list)  # Score >= threshold
    weaknesses    = Column(JSON, nullable=False, default=list)  # Score < threshold

    # Skills in the career that the user was tested on but scored poorly,
    # OR skills they have not been tested on yet
    skill_gaps    = Column(JSON, nullable=False, default=list)

    level = Column(
        SAEnum(ReadinessLevel),
        nullable=False,
        default=ReadinessLevel.BEGINNER,
    )

    # ── AI-Enhanced Fields (nullable — fallback = None) ───────────────────────
    # Populated asynchronously by ai_service.py AFTER the result is saved.
    # If AI fails: these remain NULL and the frontend shows default text.
    # Frontend should handle NULL gracefully: "AI insights unavailable."
    ai_feedback = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    assessment = relationship("Assessment", back_populates="result")
    roadmap    = relationship(
        "Roadmap",
        back_populates="result",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return (
            f"<Result id={self.id} assessment_id={self.assessment_id} "
            f"overall_score={self.overall_score} level='{self.level}'>"
        )


class Roadmap(Base):
    """
    Personalized learning roadmap generated from the assessment result.
    
    steps JSON structure (array of step objects):
    [
        {
            "order": 1,
            "skill_slug": "deep_learning",
            "title": "Master Deep Learning Fundamentals",
            "priority": "high",
            "reason": "Core skill gap identified — scored 30%",
            "resources": [],        # Future: populated from a resources table
            "ai_tip": null          # Populated by AI service if available
        },
        ...
    ]
    """
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

    # Ordered array of roadmap step objects (see docstring above)
    steps         = Column(JSON, nullable=False, default=list)

    # Was AI used to enrich the roadmap steps with ai_tip values?
    ai_enhanced   = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    result = relationship("Result", back_populates="roadmap")
    career = relationship("Career")

    def __repr__(self):
        return (
            f"<Roadmap id={self.id} assessment_id={self.assessment_id} "
            f"ai_enhanced={self.ai_enhanced}>"
        )
