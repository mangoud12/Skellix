"""Question catalogue helpers for the public question endpoints."""

from __future__ import annotations

import json
import random
from pathlib import Path

from models.question import DifficultyLevel, QuestionCategory
from schemas.assessment import QuestionOut


_QUESTION_DIR = Path(__file__).resolve().parent.parent / "data" / "questions"


def _questions() -> list[QuestionOut]:
    result: list[QuestionOut] = []
    for file in _QUESTION_DIR.glob("*.json"):
        with file.open(encoding="utf-8") as handle:
            for item in json.load(handle):
                result.append(QuestionOut(id=str(item["id"]), slug=str(item["id"]), skill_slug=item["skill_slug"], difficulty=item.get("difficulty", "intermediate"), points=item.get("points", 1), question_text=item.get("question") or item.get("text", ""), options=item.get("options", [])))
    return result


def get_question_record(question_id: str) -> dict | None:
    """Return the internal question record, including the answer and explanation.

    This deliberately stays in the service layer: public question endpoints only
    ever expose ``QuestionOut`` and therefore cannot leak answers to the browser.
    """
    for file in _QUESTION_DIR.glob("*.json"):
        with file.open(encoding="utf-8") as handle:
            for item in json.load(handle):
                if str(item["id"]) == question_id:
                    return item
    return None


def get_questions_for_topic(topic: str, difficulty: DifficultyLevel | None = None, category: QuestionCategory | None = None, limit: int = 10) -> list[QuestionOut]:
    result = [question for question in _questions() if question.skill_slug.lower() == topic.lower()]
    if difficulty:
        result = [question for question in result if question.difficulty == difficulty.value]
    return result[:limit]


def get_question_by_id(question_id: str) -> QuestionOut | None:
    return next((question for question in _questions() if question.id == question_id), None)


def get_questions_by_category(category: QuestionCategory, difficulty: DifficultyLevel | None = None, limit: int = 15) -> list[QuestionOut]:
    return get_random_questions(count=limit, difficulty=difficulty)


def get_random_questions(topic: str | None = None, count: int = 5, difficulty: DifficultyLevel | None = None) -> list[QuestionOut]:
    result = get_questions_for_topic(topic, difficulty=difficulty, limit=10_000) if topic else _questions()
    if difficulty and not topic:
        result = [question for question in result if question.difficulty == difficulty.value]
    return random.sample(result, min(count, len(result)))
