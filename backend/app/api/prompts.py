"""
Prompt management endpoints.

Implemented in Phase 4 (Prompt Playground) and Phase 6 (Prompt Versioning).
This file is a stub so the router registration in main.py works from Phase 1.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/prompts",
    summary="List prompts [Phase 4]",
    description="Not yet implemented — coming in Phase 4.",
    tags=["Prompts"],
)
async def list_prompts() -> dict:
    return {"message": "Prompt management coming in Phase 4.", "prompts": []}
