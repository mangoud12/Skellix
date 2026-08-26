"""In-memory assessment session service used by the assessment router."""

from __future__ import annotations

from datetime import datetime, timedelta
import random
from uuid import uuid4

from models.assessment import AssessmentQuestionOut, AssessmentResult, AssessmentSession, AssessmentStatus
from models.question import DifficultyLevel
from .questions import get_questions_for_topic, get_question_record


_SESSIONS: dict[str, AssessmentSession] = {}
_RESULTS: dict[str, AssessmentResult] = {}
_SESSION_TTL = timedelta(hours=2)
_RECENT_QUESTION_IDS: dict[str, list[str]] = {}


def start_assessment_session(topic: str, experience: str, question_count: int, difficulty: str | None = None) -> AssessmentSession:
    requested_difficulty = DifficultyLevel(difficulty) if difficulty else None
    catalogue = get_questions_for_topic(topic, requested_difficulty, limit=10_000)
    if not catalogue:
        raise ValueError(f"No question bank is available for '{topic}'.")
    # A learner gets 8–10 questions per attempt. Prefer unseen questions from
    # recent sessions, then reshuffle once the local catalogue has been used.
    count = min(max(question_count, 8), 10, len(catalogue))
    recent = set(_RECENT_QUESTION_IDS.get(topic.lower(), []))
    unseen = [question for question in catalogue if question.id not in recent]
    pool = unseen if len(unseen) >= count else catalogue
    questions = random.sample(pool, count)
    _RECENT_QUESTION_IDS.setdefault(topic.lower(), []).extend(question.id for question in questions)
    if len(_RECENT_QUESTION_IDS[topic.lower()]) >= len(catalogue):
        _RECENT_QUESTION_IDS[topic.lower()] = [question.id for question in questions]
    session = AssessmentSession(
        id=uuid4().hex,
        topic=topic,
        experience=experience,
        questions=[AssessmentQuestionOut(id=question.id, question_text=question.question_text, options=question.options, difficulty=question.difficulty) for question in questions],
    )
    _SESSIONS[session.id] = session
    return session


def get_session_by_id(session_id: str) -> AssessmentSession | None:
    session = _SESSIONS.get(session_id)
    if session and datetime.utcnow() - session.created_at > _SESSION_TTL and session.status == AssessmentStatus.IN_PROGRESS:
        session.status = AssessmentStatus.EXPIRED
    return session


def submit_assessment_answers(session_id: str, answers: list[object]) -> AssessmentResult:
    session = get_session_by_id(session_id)
    if session is None:
        raise ValueError("Assessment session not found.")
    submitted = {str(answer.question_id): answer.selected_option for answer in answers}
    total = len(session.questions)
    correct = 0
    mistakes: list[dict] = []
    skill_points: dict[str, list[int]] = {session.topic: [0, 0]}
    for question in session.questions:
        record = get_question_record(question.id) or {}
        selected = submitted.get(question.id, "")
        is_correct = selected == record.get("answer")
        skill_points[session.topic][1] += 1
        if is_correct:
            correct += 1
            skill_points[session.topic][0] += 1
        else:
            mistakes.append({
                "question_id": question.id,
                "question": question.question_text,
                "selected_answer": selected or "No answer",
                "correct_answer": record.get("answer", "Unavailable"),
                "explanation": record.get("explanation", "Review this concept and try again."),
            })
    score = round((correct / total * 100) if total else 0.0, 1)
    profile = {skill: round(hits / possible * 100, 1) if possible else 0.0 for skill, (hits, possible) in skill_points.items()}
    result = AssessmentResult(score_percent=score, correct_count=correct, total_questions=total, mistakes=mistakes, skill_profile=profile, feedback=("Strong foundation — keep building projects." if score >= 70 else "Review the concepts below, then take a fresh assessment."))
    session.status = AssessmentStatus.COMPLETED
    _RESULTS[session_id] = result
    return result


def get_assessment_result(session_id: str) -> AssessmentResult | None:
    return _RESULTS.get(session_id)


def expire_stale_sessions() -> None:
    for session_id in list(_SESSIONS):
        get_session_by_id(session_id)
