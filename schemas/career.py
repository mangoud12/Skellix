"""
schemas/career.py

Pydantic schemas for Career and Skill responses.
"""

from pydantic import BaseModel, Field
from typing import Literal


class SkillBrief(BaseModel):
    """Compact skill representation embedded in career responses."""

    id: int
    name: str
    slug: str
    category: str
    importance: Literal["required", "recommended", "optional"]
    weight: float = Field(ge=0.0, le=1.0)

    model_config = {"from_attributes": True}


class CareerBase(BaseModel):
    """Shared fields for career schemas."""

    id: int
    description: str
    category: str

    model_config = {"from_attributes": True}


class CareerOut(CareerBase):
    """Flat career representation — used in list endpoints."""
    pass


class CareerWithSkills(CareerBase):
    """Career with its associated skills — used in detail endpoints."""

    skills: list[SkillBrief] = Field(default_factory=list)
