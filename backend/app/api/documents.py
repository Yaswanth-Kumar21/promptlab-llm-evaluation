"""
Document upload and management endpoints.
Implemented in Phase 9 (RAG).
"""

from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/documents",
    summary="List documents [Phase 9]",
    tags=["Documents"],
)
async def list_documents() -> dict:
    return {"message": "Document management coming in Phase 9.", "documents": []}
