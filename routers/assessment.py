# routers/assessment.py

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Path, status
from pydantic import BaseModel, Field

from models.assessment import (
    AssessmentResult,
    AssessmentSession,
    AssessmentStatus,
)
from schemas.assessment import (
    AssessmentStartRequest,
    AssessmentSubmitRequest,
)
from logic.assessment import (
    start_assessment_session,
    submit_assessment_answers,
    get_assessment_result,
    get_session_by_id,
    expire_stale_sessions,
)

router = APIRouter(
    prefix="/assessment",
    tags=["Assessment"],
    responses={
        404: {"description": "Assessment session not found"},
        409: {"description": "Session state conflict"},
        422: {"description": "Validation error"},
    },
)


# ---------------------------------------------------------------------------
# Response envelopes
# ---------------------------------------------------------------------------


class StartAssessmentResponse(BaseModel):
    session: AssessmentSession
    message: str = "Assessment session created. Answer all questions and submit."


class SubmitAssessmentResponse(BaseModel):
    session_id: str
    status: AssessmentStatus
    result: AssessmentResult
    message: str


class AssessmentStatusResponse(BaseModel):
    session: AssessmentSession
    result: AssessmentResult | None = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/start",
    response_model=StartAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new assessment session",
    description=(
        "Creates a new assessment session for a given topic and experience level. "
        "Returns a session object containing the questions to answer."
    ),
)
async def start_assessment(
    request: AssessmentStartRequest,
    background_tasks: BackgroundTasks,
) -> StartAssessmentResponse:
    session = start_assessment_session(
        topic=request.topic,
        experience=request.experience,
        question_count=request.question_count,
        difficulty=request.difficulty,
    )

    # Schedule background cleanup of any stale/expired sessions
    background_tasks.add_task(expire_stale_sessions)

    return StartAssessmentResponse(session=session)


@router.post(
    "/{session_id}/submit",
    response_model=SubmitAssessmentResponse,
    summary="Submit assessment answers",
    description=(
        "Submit the learner's answers for an active assessment session. "
        "Returns a scored result with per-question feedback and a skill profile."
    ),
)
async def submit_assessment(
    session_id: Annotated[str, Path(description="The session ID returned by /start")],
    request: AssessmentSubmitRequest,
) -> SubmitAssessmentResponse:
    session = get_session_by_id(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment session '{session_id}' not found or has expired.",
        )
    if session.status == AssessmentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This assessment session has already been submitted.",
        )
    if session.status == AssessmentStatus.EXPIRED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This assessment session has expired. Please start a new one.",
        )

    result = submit_assessment_answers(
        session_id=session_id,
        answers=request.answers,
    )

    return SubmitAssessmentResponse(
        session_id=session_id,
        status=AssessmentStatus.COMPLETED,
        result=result,
        message=(
            f"Assessment complete. You scored {result.score_percent:.1f}% "
            f"({result.correct_count}/{result.total_questions} correct)."
        ),
    )


@router.get(
    "/{session_id}",
    response_model=AssessmentStatusResponse,
    summary="Get assessment session status",
    description=(
        "Returns the current state of an assessment session. "
        "If completed, also includes the full scored result."
    ),
)
async def get_assessment_status(
    session_id: Annotated[str, Path(description="The session ID to look up")],
) -> AssessmentStatusResponse:
    session = get_session_by_id(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment session '{session_id}' not found.",
        )

    result: AssessmentResult | None = None
    if session.status == AssessmentStatus.COMPLETED:
        result = get_assessment_result(session_id)

    return AssessmentStatusResponse(session=session, result=result)


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Abandon an assessment session",
    description="Mark an active assessment session as abandoned and remove it from state.",
)
async def abandon_assessment(
    session_id: Annotated[str, Path(description="Session ID to abandon")],
) -> None:
    session = get_session_by_id(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment session '{session_id}' not found.",
        )
    if session.status == AssessmentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot abandon a completed assessment.",
        )
    # Delegate state mutation to logic layer
    session.status = AssessmentStatus.EXPIRED
