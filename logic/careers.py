"""Read-only career catalogue helpers used by the API router."""

from __future__ import annotations

import json
from pathlib import Path

from models.career import CareerPath, CareerSummary


_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "careers.json"


def _catalogue() -> list[CareerSummary]:
    with _DATA_FILE.open(encoding="utf-8") as handle:
        items = json.load(handle)
    return [
        CareerSummary(
            id=str(item["id"]),
            title=item.get("title") or item.get("name", "Untitled career"),
            slug=item.get("slug") or (item.get("title") or item.get("name", "career")).lower().replace(" ", "-"),
            description=item.get("description", ""),
            category=item.get("category", "General"),
        )
        for item in items
    ]


def get_all_careers(category: str | None = None, experience_level: str | None = None, limit: int = 20, offset: int = 0) -> list[CareerSummary]:
    careers = _catalogue()
    if category:
        careers = [career for career in careers if career.category.lower() == category.lower()]
    return careers[offset : offset + limit]


def get_career_by_id(career_id: str) -> CareerPath | None:
    summary = next((career for career in _catalogue() if career.id == str(career_id)), None)
    return CareerPath(**summary.model_dump()) if summary else None


def get_career_by_slug(slug: str) -> CareerPath | None:
    summary = next((career for career in _catalogue() if career.slug == slug), None)
    return CareerPath(**summary.model_dump()) if summary else None


def search_careers(query: str, limit: int = 10) -> list[CareerSummary]:
    needle = query.lower()
    return [career for career in _catalogue() if needle in f"{career.title} {career.description} {career.category}".lower()][:limit]


def get_related_careers(career_id: str, limit: int = 4) -> list[CareerSummary]:
    current = get_career_by_id(career_id)
    if not current:
        return []
    return [career for career in _catalogue() if career.id != current.id and career.category == current.category][:limit]
