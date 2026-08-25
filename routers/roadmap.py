# routers/roadmap.py

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status
from pydantic import BaseModel, Field

from models.roadmap import RoadmapResponse, RoadmapNode, RoadmapStatus
from schemas.roadmap import RoadmapGenerateRequest
from logic.roadmap import generate_roadmap

router = APIRouter(
    prefix="/roadmap",
    tags=["Roadmap"],
    responses={
        404: {"description": "Roadmap or node not found"},
        422: {"description": "Validation error"},
    },
)


# ---------------------------------------------------------------------------
# Response envelopes
# ---------------------------------------------------------------------------


class GenerateRoadmapResponse(BaseModel):
    roadmap: RoadmapResponse
    message: str = Field(
        default="Roadmap generated successfully.",
        description="Human-readable confirmation message.",
    )


class NodeUpdateResponse(BaseModel):
    node_id: str
    new_status: RoadmapStatus
    message: str


class RoadmapSummaryResponse(BaseModel):
    id: str
    topic: str
    total_hours: float
    estimated_weeks: int
    total_nodes: int
    completed_nodes: int
    progress_percent: float


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/generate",
    response_model=GenerateRoadmapResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a personalised learning roadmap",
    description=(
        "Generates a structured, week-by-week learning roadmap tailored to "
        "the user's topic, experience level, pace, and optional target deadline. "
        "Each node in the roadmap contains curated resources and prerequisite links."
    ),
)
async def generate_roadmap_endpoint(
    request: RoadmapGenerateRequest,
) -> GenerateRoadmapResponse:
    try:
        roadmap = generate_roadmap(request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    on_track_msg = (
        "You are on track to meet your target deadline."
        if roadmap.on_track
        else (
            f"Note: at your selected pace this roadmap takes "
            f"{roadmap.estimated_weeks} weeks, which exceeds your target."
        )
    )

    return GenerateRoadmapResponse(
        roadmap=roadmap,
        message=f"Roadmap generated successfully. {on_track_msg}",
    )


@router.get(
    "/{roadmap_id}",
    response_model=RoadmapResponse,
    summary="Retrieve a previously generated roadmap",
    description=(
        "Fetch a roadmap by its unique ID. "
        "This is useful for re-loading a saved plan or sharing a roadmap link."
    ),
)
async def get_roadmap(
    roadmap_id: Annotated[str, Path(description="The roadmap ID returned by /generate")],
) -> RoadmapResponse:
    # NOTE: In production, retrieve from a persistent store (Redis / DB).
    # This stub raises 404 until a storage layer is wired in.
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=(
            f"Roadmap '{roadmap_id}' not found in persistent storage. "
            "Persistent roadmap storage is not yet implemented — "
            "generate a fresh roadmap using POST /roadmap/generate."
        ),
    )


@router.get(
    "/{roadmap_id}/summary",
    response_model=RoadmapSummaryResponse,
    summary="Get roadmap progress summary",
    description="Returns high-level progress stats for a saved roadmap.",
)
async def get_roadmap_summary(
    roadmap_id: Annotated[str, Path(description="The roadmap ID")],
) -> RoadmapSummaryResponse:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Roadmap '{roadmap_id}' not found.",
    )


@router.patch(
    "/{roadmap_id}/nodes/{node_id}/status",
    response_model=NodeUpdateResponse,
    summary="Update a node's completion status",
    description=(
        "Mark a roadmap node as in_progress, completed, or reset it to available. "
        "Prerequisite checks are enforced — you cannot complete a locked node."
    ),
)
async def update_node_status(
    roadmap_id: Annotated[str, Path(description="Parent roadmap ID")],
    node_id: Annotated[str, Path(description="Node ID to update")],
    new_status: Annotated[
        RoadmapStatus,
        Query(description="Target status: available | in_progress | completed"),
    ],
) -> NodeUpdateResponse:
    # Guard: locked nodes cannot be manually set to completed
    if new_status == RoadmapStatus.LOCKED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot manually set a node to 'locked'. Reset to 'available' instead.",
        )

    # NOTE: In production, load roadmap from store, validate prerequisites,
    # mutate node status, and persist the updated roadmap.
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=(
            f"Roadmap '{roadmap_id}' not found. "
            "Persistent storage is required for node status updates."
        ),
    )


@router.get(
    "/{roadmap_id}/nodes",
    response_model=list[RoadmapNode],
    summary="List all nodes for a roadmap",
    description="Returns every node in the roadmap, optionally filtered by status.",
)
async def list_roadmap_nodes(
    roadmap_id: Annotated[str, Path(description="Parent roadmap ID")],
    status_filter: Annotated[
        RoadmapStatus | None,
        Query(alias="status", description="Filter nodes by status"),
    ] = None,
) -> list[RoadmapNode]:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Roadmap '{roadmap_id}' not found.",
    )
