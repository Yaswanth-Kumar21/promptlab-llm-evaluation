"""
Experiment tracking endpoints.
Implemented in Phase 6 / Phase 11.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/experiments",
    summary="List experiments [Phase 6]",
    tags=["Experiments"],
)
async def list_experiments() -> dict:
    return {"message": "Experiment tracking coming in Phase 6.", "experiments": []}
