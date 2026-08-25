# models/skill.py
# ─────────────────────────────────────────────────────────────────────────────
# Skill model: represents a single assessable skill (e.g., "Python", "SQL").
# Skills exist independently of careers — one skill can belong to many careers.
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base


class Skill(Base):
    __tablename__ = "skills"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), nullable=False)
    slug        = Column(String(100), unique=True, index=True, nullable=False)

    # Category helps group skills in the UI (e.g., "Programming", "AI/ML", "DevOps")
    category    = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    career_skills = relationship(
        "CareerSkill",
        back_populates="skill",
        cascade="all, delete-orphan",
        lazy="select",
    )
    questions = relationship(
        "Question",
        back_populates="skill",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<Skill id={self.id} slug='{self.slug}'>"
