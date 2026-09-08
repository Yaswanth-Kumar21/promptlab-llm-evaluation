"""
Evaluation engine endpoints.
Implemented in Phase 7.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/evaluations",
    summary="List evaluations [Phase 7]",
    tags=["Evaluations"],
)
async def list_evaluations() -> dict:
    return {"message": "Evaluation engine coming in Phase 7.", "evaluations": []}
