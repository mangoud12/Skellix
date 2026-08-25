# routers/careers.py

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from models.career import CareerPath, CareerSummary
from logic.careers import (
    get_all_careers,
    get_career_by_id,
    get_career_by_slug,
    search_careers,
    get_related_careers,
)

router = APIRouter(
    prefix="/careers",
    tags=["Careers"],
    responses={
        404: {"description": "Career not found"},
        422: {"description": "Validation error"},
    },
)


# ---------------------------------------------------------------------------
# Response envelopes
# ---------------------------------------------------------------------------


class CareerListResponse(BaseModel):
    total: int
    results: list[CareerSummary]


class CareerDetailResponse(BaseModel):
    career: CareerPath
    related: list[CareerSummary] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=CareerListResponse,
    summary="List all career paths",
    description=(
        "Returns a paginated list of all available career paths. "
        "Optionally filter by category or experience level."
    ),
)
async def list_careers(
    category: Annotated[
        Optional[str],
        Query(description="Filter by career category (e.g. 'engineering', 'design')"),
    ] = None,
    experience_level: Annotated[
        Optional[str],
        Query(description="Filter by entry experience level: none | beginner | intermediate | advanced"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Max results to return")] = 20,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
) -> CareerListResponse:
    careers = get_all_careers(
        category=category,
        experience_level=experience_level,
        limit=limit,
        offset=offset,
    )
    return CareerListResponse(total=len(careers), results=careers)


@router.get(
    "/search",
    response_model=CareerListResponse,
    summary="Search career paths",
    description="Full-text search across career titles, descriptions, and required skills.",
)
async def search_career_paths(
    q: Annotated[str, Query(min_length=2, max_length=120, description="Search query string")],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> CareerListResponse:
    results = search_careers(query=q, limit=limit)
    return CareerListResponse(total=len(results), results=results)


@router.get(
    "/{career_id}",
    response_model=CareerDetailResponse,
    summary="Get career by ID",
    description="Retrieve full details for a single career path by its unique ID.",
)
async def get_career(
    career_id: str,
    include_related: Annotated[
        bool,
        Query(description="Include related career suggestions"),
    ] = True,
) -> CareerDetailResponse:
    career = get_career_by_id(career_id)
    if career is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Career with id '{career_id}' not found.",
        )
    related: list[CareerSummary] = []
    if include_related:
        related = get_related_careers(career_id=career_id, limit=4)

    return CareerDetailResponse(career=career, related=related)


@router.get(
    "/slug/{slug}",
    response_model=CareerDetailResponse,
    summary="Get career by slug",
    description="Retrieve full career details using a human-readable URL slug.",
)
async def get_career_by_slug_route(
    slug: str,
    include_related: bool = True,
) -> CareerDetailResponse:
    career = get_career_by_slug(slug)
    if career is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Career with slug '{slug}' not found.",
        )
    related: list[CareerSummary] = []
    if include_related:
        related = get_related_careers(career_id=career.id, limit=4)

    return CareerDetailResponse(career=career, related=related)
