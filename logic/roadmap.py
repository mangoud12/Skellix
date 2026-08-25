# logic/roadmap.py

from __future__ import annotations

import math
import uuid
from datetime import date, timedelta
from typing import Any

from models.roadmap import (
    DifficultyLevel,
    Resource,
    ResourceType,
    RoadmapNode,
    RoadmapResponse,
    RoadmapStatus,
    WeeklyPlan,
)
from schemas.roadmap import RoadmapGenerateRequest


# ---------------------------------------------------------------------------
# Constants & lookup tables
# ---------------------------------------------------------------------------

# Approximate hours a learner can invest per week per self-reported pace
PACE_HOURS_PER_WEEK: dict[str, float] = {
    "slow": 4.0,
    "moderate": 8.0,
    "fast": 15.0,
    "intensive": 25.0,
}

# Multiplier applied to total hours based on prior experience
EXPERIENCE_MULTIPLIER: dict[str, float] = {
    "none": 1.0,
    "beginner": 0.85,
    "intermediate": 0.65,
    "advanced": 0.40,
}

# Curated resource catalogue (simplified seed data).
# In production this would be fetched from a DB / external API.
_RESOURCE_CATALOGUE: list[dict[str, Any]] = [
    # --- Programming / Python ---
    {
        "id": "res-py-001",
        "title": "Python Official Tutorial",
        "url": "https://docs.python.org/3/tutorial/",
        "type": ResourceType.ARTICLE,
        "tags": ["python", "programming", "beginner"],
        "difficulty": DifficultyLevel.BEGINNER,
        "duration_minutes": 180,
        "free": True,
    },
    {
        "id": "res-py-002",
        "title": "Automate the Boring Stuff with Python",
        "url": "https://automatetheboringstuff.com/",
        "type": ResourceType.BOOK,
        "tags": ["python", "programming", "automation", "beginner"],
        "difficulty": DifficultyLevel.BEGINNER,
        "duration_minutes": 600,
        "free": True,
    },
    {
        "id": "res-py-003",
        "title": "Real Python — Intermediate Topics",
        "url": "https://realpython.com/",
        "type": ResourceType.ARTICLE,
        "tags": ["python", "programming", "intermediate"],
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "duration_minutes": 240,
        "free": False,
    },
    {
        "id": "res-py-004",
        "title": "Python for Everybody — Coursera",
        "url": "https://www.coursera.org/specializations/python",
        "type": ResourceType.COURSE,
        "tags": ["python", "programming", "beginner"],
        "difficulty": DifficultyLevel.BEGINNER,
        "duration_minutes": 1200,
        "free": False,
    },
    # --- Data Science ---
    {
        "id": "res-ds-001",
        "title": "Kaggle — Intro to Machine Learning",
        "url": "https://www.kaggle.com/learn/intro-to-machine-learning",
        "type": ResourceType.COURSE,
        "tags": ["data science", "machine learning", "beginner"],
        "difficulty": DifficultyLevel.BEGINNER,
        "duration_minutes": 480,
        "free": True,
    },
    {
        "id": "res-ds-002",
        "title": "fast.ai Practical Deep Learning",
        "url": "https://course.fast.ai/",
        "type": ResourceType.VIDEO,
        "tags": ["data science", "deep learning", "intermediate"],
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "duration_minutes": 900,
        "free": True,
    },
    {
        "id": "res-ds-003",
        "title": "Hands-On Machine Learning (O'Reilly)",
        "url": "https://www.oreilly.com/library/view/hands-on-machine-learning/9781492032632/",
        "type": ResourceType.BOOK,
        "tags": ["data science", "machine learning", "advanced"],
        "difficulty": DifficultyLevel.ADVANCED,
        "duration_minutes": 1800,
        "free": False,
    },
    # --- Web Development ---
    {
        "id": "res-web-001",
        "title": "MDN Web Docs — HTML & CSS",
        "url": "https://developer.mozilla.org/en-US/docs/Learn",
        "type": ResourceType.ARTICLE,
        "tags": ["web development", "html", "css", "beginner"],
        "difficulty": DifficultyLevel.BEGINNER,
        "duration_minutes": 360,
        "free": True,
    },
    {
        "id": "res-web-002",
        "title": "The Odin Project",
        "url": "https://www.theodinproject.com/",
        "type": ResourceType.COURSE,
        "tags": ["web development", "javascript", "html", "css", "beginner"],
        "difficulty": DifficultyLevel.BEGINNER,
        "duration_minutes": 2400,
        "free": True,
    },
    {
        "id": "res-web-003",
        "title": "Full Stack Open — University of Helsinki",
        "url": "https://fullstackopen.com/en/",
        "type": ResourceType.COURSE,
        "tags": ["web development", "react", "nodejs", "intermediate"],
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "duration_minutes": 3000,
        "free": True,
    },
    # --- General / Practice ---
    {
        "id": "res-gen-001",
        "title": "LeetCode — Easy Problems",
        "url": "https://leetcode.com/problemset/all/?difficulty=Easy",
        "type": ResourceType.EXERCISE,
        "tags": ["programming", "python", "algorithms", "beginner"],
        "difficulty": DifficultyLevel.BEGINNER,
        "duration_minutes": 120,
        "free": True,
    },
    {
        "id": "res-gen-002",
        "title": "LeetCode — Medium Problems",
        "url": "https://leetcode.com/problemset/all/?difficulty=Medium",
        "type": ResourceType.EXERCISE,
        "tags": ["programming", "algorithms", "intermediate"],
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "duration_minutes": 240,
        "free": True,
    },
    {
        "id": "res-gen-003",
        "title": "Project Euler",
        "url": "https://projecteuler.net/",
        "type": ResourceType.EXERCISE,
        "tags": ["programming", "math", "python", "intermediate"],
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "duration_minutes": 300,
        "free": True,
    },
]


# ---------------------------------------------------------------------------
# Topic → subtopic decomposition
# ---------------------------------------------------------------------------

# Maps a broad skill topic keyword → ordered list of subtopics / milestones.
# Each subtopic carries an estimated effort in hours and a difficulty tag.
_TOPIC_CURRICULUM: dict[str, list[dict[str, Any]]] = {
    "python": [
        {"title": "Environment Setup & Syntax Basics", "hours": 3, "difficulty": DifficultyLevel.BEGINNER, "tags": ["python", "programming", "beginner"]},
        {"title": "Data Types, Variables & Operators", "hours": 4, "difficulty": DifficultyLevel.BEGINNER, "tags": ["python", "programming", "beginner"]},
        {"title": "Control Flow: if / for / while", "hours": 5, "difficulty": DifficultyLevel.BEGINNER, "tags": ["python", "programming", "beginner"]},
        {"title": "Functions & Scope", "hours": 6, "difficulty": DifficultyLevel.BEGINNER, "tags": ["python", "programming", "beginner"]},
        {"title": "Data Structures: list, dict, set, tuple", "hours": 6, "difficulty": DifficultyLevel.BEGINNER, "tags": ["python", "programming", "beginner"]},
        {"title": "File I/O & Exception Handling", "hours": 5, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["python", "programming", "intermediate"]},
        {"title": "Modules, Packages & Virtual Environments", "hours": 4, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["python", "programming", "intermediate"]},
        {"title": "Object-Oriented Programming", "hours": 8, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["python", "programming", "intermediate"]},
        {"title": "Comprehensions, Generators & Itertools", "hours": 5, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["python", "programming", "intermediate"]},
        {"title": "Testing with pytest", "hours": 5, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["python", "programming", "intermediate"]},
        {"title": "Concurrency: threading, asyncio", "hours": 7, "difficulty": DifficultyLevel.ADVANCED, "tags": ["python", "programming", "advanced"]},
        {"title": "Packaging & Publishing to PyPI", "hours": 4, "difficulty": DifficultyLevel.ADVANCED, "tags": ["python", "programming", "advanced"]},
    ],
    "data science": [
        {"title": "Python & NumPy Fundamentals", "hours": 6, "difficulty": DifficultyLevel.BEGINNER, "tags": ["data science", "python", "beginner"]},
        {"title": "Data Manipulation with pandas", "hours": 8, "difficulty": DifficultyLevel.BEGINNER, "tags": ["data science", "beginner"]},
        {"title": "Data Visualisation with matplotlib & seaborn", "hours": 6, "difficulty": DifficultyLevel.BEGINNER, "tags": ["data science", "beginner"]},
        {"title": "Statistical Foundations", "hours": 8, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["data science", "intermediate"]},
        {"title": "Intro to Machine Learning (scikit-learn)", "hours": 10, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["data science", "machine learning", "intermediate"]},
        {"title": "Feature Engineering & EDA", "hours": 8, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["data science", "intermediate"]},
        {"title": "Model Evaluation & Hyperparameter Tuning", "hours": 8, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["data science", "machine learning", "intermediate"]},
        {"title": "Deep Learning Basics with PyTorch", "hours": 12, "difficulty": DifficultyLevel.ADVANCED, "tags": ["data science", "deep learning", "advanced"]},
        {"title": "Natural Language Processing Fundamentals", "hours": 10, "difficulty": DifficultyLevel.ADVANCED, "tags": ["data science", "advanced"]},
        {"title": "MLOps & Model Deployment", "hours": 10, "difficulty": DifficultyLevel.ADVANCED, "tags": ["data science", "advanced"]},
    ],
    "web development": [
        {"title": "HTML5 Semantics & Accessibility", "hours": 5, "difficulty": DifficultyLevel.BEGINNER, "tags": ["web development", "html", "beginner"]},
        {"title": "CSS3 Layouts: Flexbox & Grid", "hours": 7, "difficulty": DifficultyLevel.BEGINNER, "tags": ["web development", "css", "beginner"]},
        {"title": "JavaScript Core Language", "hours": 10, "difficulty": DifficultyLevel.BEGINNER, "tags": ["web development", "javascript", "beginner"]},
        {"title": "DOM Manipulation & Browser APIs", "hours": 6, "difficulty": DifficultyLevel.BEGINNER, "tags": ["web development", "javascript", "beginner"]},
        {"title": "Responsive Design & CSS Animations", "hours": 5, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["web development", "css", "intermediate"]},
        {"title": "Version Control with Git & GitHub", "hours": 4, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["web development", "intermediate"]},
        {"title": "React Fundamentals & Hooks", "hours": 12, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["web development", "react", "intermediate"]},
        {"title": "REST APIs & Async JavaScript (fetch / Axios)", "hours": 7, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["web development", "intermediate"]},
        {"title": "Node.js & Express Backend Basics", "hours": 10, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["web development", "nodejs", "intermediate"]},
        {"title": "Databases: SQL & NoSQL", "hours": 8, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["web development", "intermediate"]},
        {"title": "Authentication, Security & Deployment", "hours": 8, "difficulty": DifficultyLevel.ADVANCED, "tags": ["web development", "advanced"]},
        {"title": "Performance Optimisation & Testing", "hours": 7, "difficulty": DifficultyLevel.ADVANCED, "tags": ["web development", "advanced"]},
    ],
}

_FALLBACK_CURRICULUM: list[dict[str, Any]] = [
    {"title": "Foundations & Core Concepts", "hours": 6, "difficulty": DifficultyLevel.BEGINNER, "tags": ["beginner"]},
    {"title": "Intermediate Techniques", "hours": 8, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["intermediate"]},
    {"title": "Applied Practice & Projects", "hours": 10, "difficulty": DifficultyLevel.INTERMEDIATE, "tags": ["intermediate"]},
    {"title": "Advanced Patterns & Best Practices", "hours": 10, "difficulty": DifficultyLevel.ADVANCED, "tags": ["advanced"]},
    {"title": "Real-World Capstone Project", "hours": 12, "difficulty": DifficultyLevel.ADVANCED, "tags": ["advanced"]},
]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _normalise_topic(topic: str) -> str:
    """Return lowercase, stripped topic key for catalogue lookups."""
    return topic.strip().lower()


def _get_curriculum(topic: str) -> list[dict[str, Any]]:
    """
    Return the ordered list of subtopics for *topic*.

    Performs a fuzzy key-match so that 'Python 3' maps to 'python', etc.
    Falls back to a generic curriculum when no specific curriculum exists.
    """
    normalised = _normalise_topic(topic)
    for key, curriculum in _TOPIC_CURRICULUM.items():
        if key in normalised or normalised in key:
            return [dict(subtopic) for subtopic in curriculum]
    return [dict(item) for item in _FALLBACK_CURRICULUM]


def _select_resources(
    tags: list[str],
    difficulty: DifficultyLevel,
    free_only: bool = False,
    max_results: int = 3,
) -> list[Resource]:
    """
    Select the most relevant resources from the catalogue for a given node.

    Scoring strategy
    ----------------
    +2  per catalogue tag that appears in the node's *tags* list
    +1  if the resource difficulty matches *difficulty* exactly
    +0.5 if the resource difficulty is one step below *difficulty* (foundational)
    Resources that require payment are excluded when *free_only* is True.

    Parameters
    ----------
    tags:        Keywords describing the node's topic area.
    difficulty:  Target difficulty of the learning node.
    free_only:   If True, skip paid resources.
    max_results: Maximum number of resources to return.

    Returns
    -------
    A sorted list of :class:`Resource` objects (best match first).
    """
    difficulty_order = [
        DifficultyLevel.BEGINNER,
        DifficultyLevel.INTERMEDIATE,
        DifficultyLevel.ADVANCED,
    ]
    target_idx = difficulty_order.index(difficulty)
    normalised_tags = {t.lower() for t in tags}

    scored: list[tuple[float, dict[str, Any]]] = []
    for item in _RESOURCE_CATALOGUE:
        if free_only and not item["free"]:
            continue

        score: float = 0.0

        # Tag overlap
        item_tags = {t.lower() for t in item["tags"]}
        overlap = normalised_tags & item_tags
        score += len(overlap) * 2

        # Difficulty match
        item_idx = difficulty_order.index(item["difficulty"])
        if item_idx == target_idx:
            score += 1.0
        elif item_idx == target_idx - 1:
            score += 0.5

        if score > 0:
            scored.append((score, item))

    # Sort descending by score, then alphabetically by title for stability
    scored.sort(key=lambda x: (-x[0], x[1]["title"]))

    return [
        Resource(
            id=item["id"],
            title=item["title"],
            url=item["url"],
            type=item["type"],
            duration_minutes=item["duration_minutes"],
            is_free=item["free"],
        )
        for _, item in scored[:max_results]
    ]


def _estimate_total_hours(
    curriculum: list[dict[str, Any]],
    experience_level: str,
) -> float:
    """
    Return adjusted total learning hours factoring in the learner's prior
    experience level.
    """
    raw_hours = sum(item["hours"] for item in curriculum)
    multiplier = EXPERIENCE_MULTIPLIER.get(experience_level.lower(), 1.0)
    return math.ceil(raw_hours * multiplier * 10) / 10  # round up to 1 d.p.


def _build_weekly_plans(
    nodes: list[RoadmapNode],
    hours_per_week: float,
    start_date: date,
) -> list[WeeklyPlan]:
    """
    Distribute roadmap nodes into weekly plans.

    Each node's estimated hours determine how many (fractional) weeks it
    consumes. Nodes are never split across weeks — a node always belongs to
    the week in which it *starts*.

    Parameters
    ----------
    nodes:          Ordered list of roadmap nodes.
    hours_per_week: Learner's available study hours per week.
    start_date:     The Monday on (or after) today when the plan begins.

    Returns
    -------
    A list of :class:`WeeklyPlan` objects, one per calendar week.
    """
    weeks: list[WeeklyPlan] = []
    current_week_nodes: list[str] = []
    accumulated_hours: float = 0.0
    week_number: int = 1
    week_start: date = start_date

    for node in nodes:
        node_hours = node.estimated_hours
        current_week_nodes.append(node.id)
        accumulated_hours += node_hours

        # When the current week is "full", seal it and start a new one
        if accumulated_hours >= hours_per_week:
            weeks.append(
                WeeklyPlan(
                    week_number=week_number,
                    start_date=week_start,
                    end_date=week_start + timedelta(days=6),
                    node_ids=list(current_week_nodes),
                    total_hours=round(accumulated_hours, 1),
                )
            )
            week_number += 1
            week_start += timedelta(weeks=1)
            current_week_nodes = []
            accumulated_hours = 0.0

    # Flush remaining nodes into a final (potentially shorter) week
    if current_week_nodes:
        weeks.append(
            WeeklyPlan(
                week_number=week_number,
                start_date=week_start,
                end_date=week_start + timedelta(days=6),
                node_ids=list(current_week_nodes),
                total_hours=round(accumulated_hours, 1),
            )
        )

    return weeks


def _next_monday(from_date: date) -> date:
    """Return the nearest coming Monday (inclusive of today if today is Monday)."""
    days_ahead = (7 - from_date.weekday()) % 7
    return from_date + timedelta(days=days_ahead)


# ---------------------------------------------------------------------------
# Primary public function
# ---------------------------------------------------------------------------


def generate_roadmap(request: RoadmapGenerateRequest) -> RoadmapResponse:
    """
    Generate a personalised learning roadmap for the given skill topic.

    Algorithm overview
    ------------------
    1. Resolve the topic to an ordered curriculum (subtopics + hour estimates).
    2. Apply an experience multiplier to scale down redundant content.
    3. Build :class:`RoadmapNode` objects, each carrying:
       - Unique ID
       - Title & description
       - Estimated hours (post-multiplier)
       - Difficulty level
       - Curated resources matched by tag & difficulty
       - Prerequisite IDs (linear chain)
    4. Compute the total duration in weeks based on the learner's pace.
    5. Assemble the nodes into a calendar-aware weekly schedule.
    6. Return a :class:`RoadmapResponse` with all metadata populated.

    Parameters
    ----------
    request : RoadmapGenerateRequest
        Validated incoming request payload containing:
        - topic         : str              — The skill to learn
        - experience    : str              — none / beginner / intermediate / advanced
        - pace          : str              — slow / moderate / fast / intensive
        - free_only     : bool             — Restrict resources to free-only
        - goal          : str | None       — Optional end goal description
        - target_weeks  : int | None       — Optional hard deadline in weeks

    Returns
    -------
    RoadmapResponse
        Fully populated roadmap including nodes, weekly plan, and metadata.

    Raises
    ------
    ValueError
        If *pace* or *experience* values are not recognised.
    """
    # ------------------------------------------------------------------
    # 0. Validate inputs
    # ------------------------------------------------------------------
    pace = request.pace.lower()
    experience = request.experience.lower()

    if pace not in PACE_HOURS_PER_WEEK:
        raise ValueError(
            f"Unrecognised pace '{pace}'. "
            f"Valid options: {list(PACE_HOURS_PER_WEEK.keys())}"
        )
    if experience not in EXPERIENCE_MULTIPLIER:
        raise ValueError(
            f"Unrecognised experience level '{experience}'. "
            f"Valid options: {list(EXPERIENCE_MULTIPLIER.keys())}"
        )

    hours_per_week: float = PACE_HOURS_PER_WEEK[pace]

    # ------------------------------------------------------------------
    # 1. Resolve curriculum
    # ------------------------------------------------------------------
    raw_curriculum = _get_curriculum(request.topic)

    # ------------------------------------------------------------------
    # 2. Apply experience multiplier — skip early nodes for advanced users
    # ------------------------------------------------------------------
    multiplier = EXPERIENCE_MULTIPLIER[experience]

    # For experienced users, trim beginner-difficulty nodes proportionally
    filtered_curriculum: list[dict[str, Any]] = []
    beginner_nodes = [n for n in raw_curriculum if n["difficulty"] == DifficultyLevel.BEGINNER]
    non_beginner_nodes = [n for n in raw_curriculum if n["difficulty"] != DifficultyLevel.BEGINNER]

    # Number of beginner nodes to KEEP (decreases as experience increases)
    beginner_keep_ratio = {
        "none": 1.0,
        "beginner": 0.75,
        "intermediate": 0.25,
        "advanced": 0.0,
    }
    keep_count = math.ceil(len(beginner_nodes) * beginner_keep_ratio[experience])
    filtered_curriculum = beginner_nodes[:keep_count] + non_beginner_nodes

    # Guard: always keep at least 3 nodes
    if len(filtered_curriculum) < 3:
        filtered_curriculum = raw_curriculum

    # ------------------------------------------------------------------
    # 3. Build RoadmapNode objects
    # ------------------------------------------------------------------
    nodes: list[RoadmapNode] = []
    node_ids: list[str] = []

    for idx, subtopic in enumerate(filtered_curriculum):
        node_id = f"node-{uuid.uuid4().hex[:8]}"
        node_ids.append(node_id)

        # Scale node hours by multiplier (ensure minimum of 1 h)
        adjusted_hours = max(1.0, round(subtopic["hours"] * multiplier, 1))

        # Prerequisites: each node depends on its immediate predecessor
        prerequisites: list[str] = [node_ids[idx - 1]] if idx > 0 else []

        resources = _select_resources(
            tags=subtopic["tags"],
            difficulty=subtopic["difficulty"],
            free_only=request.free_only,
            max_results=3,
        )

        node = RoadmapNode(
            id=node_id,
            order=idx + 1,
            title=subtopic["title"],
            description=(
                f"Master the fundamentals of {subtopic['title'].lower()} "
                f"as part of your {request.topic} learning journey."
            ),
            difficulty=subtopic["difficulty"],
            estimated_hours=adjusted_hours,
            resources=resources,
            prerequisites=prerequisites,
            status=RoadmapStatus.LOCKED if idx > 0 else RoadmapStatus.AVAILABLE,
            tags=subtopic["tags"],
        )
        nodes.append(node)

    # ------------------------------------------------------------------
    # 4. Compute duration metadata
    # ------------------------------------------------------------------
    total_hours = sum(n.estimated_hours for n in nodes)
    estimated_weeks_raw = total_hours / hours_per_week
    estimated_weeks = math.ceil(estimated_weeks_raw)

    # If user specified a hard deadline, note when we exceed it
    on_track: bool = True
    if request.target_weeks is not None:
        on_track = estimated_weeks <= request.target_weeks

    # ------------------------------------------------------------------
    # 5. Build weekly schedule
    # ------------------------------------------------------------------
    start_date = _next_monday(date.today())
    weekly_plans = _build_weekly_plans(nodes, hours_per_week, start_date)
    completion_date = start_date + timedelta(weeks=estimated_weeks)

    # ------------------------------------------------------------------
    # 6. Assemble and return response
    # ------------------------------------------------------------------
    return RoadmapResponse(
        id=f"roadmap-{uuid.uuid4().hex[:12]}",
        topic=request.topic,
        goal=request.goal,
        experience_level=experience,
        pace=pace,
        total_hours=round(total_hours, 1),
        estimated_weeks=estimated_weeks,
        start_date=start_date,
        completion_date=completion_date,
        on_track=on_track,
        nodes=nodes,
        weekly_plans=weekly_plans,
        free_only=request.free_only,
    )
