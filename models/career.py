# models/career.py
# ─────────────────────────────────────────────────────────────────────────────
# Career and CareerSkill models.
# Career: A target role (e.g., "AI Engineer", "Full Stack Developer")
# CareerSkill: Junction table linking careers to required skills,
#              with weight and core-status metadata.
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy import (
    Column, Integer, String, Text,
    Boolean, Float, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base


class Career(Base):
    __tablename__ = "careers"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), nullable=False)
    # slug is used in URLs: /api/careers/ai-engineer
    # UNIQUE ensures no two careers share the same URL segment
    slug        = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    # icon: stores an icon identifier or URL for Adam's UI
    icon        = Column(String(255), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    # back_populates creates a bidirectional link:
    #   career.career_skills  → list of CareerSkill rows for this career
    #   career_skill.career   → the parent Career object
    career_skills = relationship(
        "CareerSkill",
        back_populates="career",
        cascade="all, delete-orphan",  # Deleting a career removes its skill links
        lazy="select",
    )
    assessments = relationship(
        "Assessment",
        back_populates="career",
        lazy="select",
    )

    def __repr__(self):
        return f"<Career id={self.id} slug='{self.slug}'>"


class CareerSkill(Base):
    """
    Junction table between Career and Skill.
    
    This is NOT a simple many-to-many — it carries important metadata:
      - is_core:      Is this skill mandatory for the career? (vs. nice-to-have)
      - weight:       How much does this skill influence the readiness score?
      - display_order: The order this skill appears in the roadmap
    
    Ahmed Ali's scoring engine reads 'weight' and 'is_core' from this table
    to compute the overall career readiness score.
    """
    __tablename__ = "career_skills"

    # Composite primary key: a career-skill pair must be unique
    career_id     = Column(Integer, ForeignKey("careers.id", ondelete="CASCADE"),
                          primary_key=True)
    skill_id      = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"),
                          primary_key=True)

    # Core skills are required; non-core are bonuses
    is_core       = Column(Boolean, default=True, nullable=False)

    # Weight: importance of this skill in the overall readiness score.
    # All weights for a given career should sum to 1.0 (enforced by seeding logic)
    weight        = Column(Float, default=1.0, nullable=False)

    # Ordering for roadmap display — lower number = higher priority
    display_order = Column(Integer, default=0, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    career = relationship("Career", back_populates="career_skills")
    skill  = relationship("Skill", back_populates="career_skills")

    # Explicit unique constraint (redundant with PK but documents intent clearly)
    __table_args__ = (
        UniqueConstraint("career_id", "skill_id", name="uq_career_skill"),
    )

    def __repr__(self):
        return (
            f"<CareerSkill career_id={self.career_id} "
            f"skill_id={self.skill_id} weight={self.weight}>"
        )
