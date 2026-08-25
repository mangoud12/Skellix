# routers/questions.py

from __future__ import annotations

from typing import Annotated, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from models.question import Question, QuestionCategory, DifficultyLevel
from logic.questions import (
    get_questions_for_topic,
    get_question_by_id,
    get_questions_by_category,
    get_random_questions,
)

router = APIRouter(
    prefix="/questions",
    tags=["Questions"],
    responses={
        404: {"description": "Question not found"},
        422: {"description": "Validation error"},
    },
)


# ---------------------------------------------------------------------------
# Response envelopes
# ---------------------------------------------------------------------------


class QuestionListResponse(BaseModel):
    session_id: str = Field(
        default_factory=lambda: uuid4().hex,
        description="Unique ID for this question fetch session.",
    )
    total: int
    questions: list[Question]


class QuestionDetailResponse(BaseModel):
    question: Question


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=QuestionListResponse,
    summary="Fetch questions for a topic",
    description=(
        "Returns a set of assessment questions for the given topic. "
        "Supports filtering by difficulty and category."
    ),
)
async def list_questions(
    topic: Annotated[
        str,
        Query(min_length=2, max_length=120, description="Skill topic to fetch questions for"),
    ],
    difficulty: Annotated[
        Optional[DifficultyLevel],
        Query(description="Filter by difficulty: beginner | intermediate | advanced"),
    ] = None,
    category: Annotated[
        Optional[QuestionCategory],
        Query(description="Filter by question category"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=50, description="Number of questions to return")] = 10,
) -> QuestionListResponse:
    questions = get_questions_for_topic(
        topic=topic,
        difficulty=difficulty,
        category=category,
        limit=limit,
    )
    return QuestionListResponse(total=len(questions), questions=questions)


@router.get(
    "/random",
    response_model=QuestionListResponse,
    summary="Fetch random questions",
    description=(
        "Returns a random selection of questions. "
        "Useful for general knowledge checks and onboarding flows."
    ),
)
async def random_questions(
    topic: Annotated[Optional[str], Query(description="Optional topic scope")] = None,
    count: Annotated[int, Query(ge=1, le=30, description="Number of random questions")] = 5,
    difficulty: Annotated[Optional[DifficultyLevel], Query()] = None,
) -> QuestionListResponse:
    questions = get_random_questions(topic=topic, count=count, difficulty=difficulty)
    return QuestionListResponse(total=len(questions), questions=questions)


@router.get(
    "/category/{category}",
    response_model=QuestionListResponse,
    summary="Fetch questions by category",
    description="Returns all questions belonging to a specific category.",
)
async def questions_by_category(
    category: QuestionCategory,
    limit: Annotated[int, Query(ge=1, le=50)] = 15,
    difficulty: Annotated[Optional[DifficultyLevel], Query()] = None,
) -> QuestionListResponse:
    questions = get_questions_by_category(
        category=category, difficulty=difficulty, limit=limit
    )
    return QuestionListResponse(total=len(questions), questions=questions)


@router.get(
    "/{question_id}",
    response_model=QuestionDetailResponse,
    summary="Get a single question by ID",
    description="Retrieve the full detail of a single question, including all answer options.",
)
async def get_question(question_id: str) -> QuestionDetailResponse:
    question = get_question_by_id(question_id)
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question '{question_id}' not found.",
        )
    return QuestionDetailResponse(question=question)
