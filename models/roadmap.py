"""Pydantic contracts for the generated (non-persisted) roadmap API."""

from __future__ import annotations

import enum
from datetime import date

from pydantic import BaseModel, Field


class DifficultyLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ResourceType(str, enum.Enum):
    ARTICLE = "article"
    VIDEO = "video"
    COURSE = "course"
    BOOK = "book"
    EXERCISE = "exercise"


class RoadmapStatus(str, enum.Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Resource(BaseModel):
    id: str
    title: str
    url: str
    type: ResourceType
    duration_minutes: int = Field(ge=1)
    is_free: bool


class RoadmapNode(BaseModel):
    id: str
    order: int = Field(ge=1)
    title: str
    description: str
    difficulty: DifficultyLevel
    estimated_hours: float = Field(ge=0)
    resources: list[Resource] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    status: RoadmapStatus
    tags: list[str] = Field(default_factory=list)


class WeeklyPlan(BaseModel):
    week_number: int = Field(ge=1)
    start_date: date
    end_date: date
    node_ids: list[str]
    total_hours: float = Field(ge=0)


class RoadmapResponse(BaseModel):
    id: str
    topic: str
    goal: str | None = None
    experience_level: str
    pace: str
    total_hours: float
    estimated_weeks: int
    start_date: date
    completion_date: date
    on_track: bool
    nodes: list[RoadmapNode]
    weekly_plans: list[WeeklyPlan]
    free_only: bool
