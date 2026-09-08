"""
RAG (Retrieval-Augmented Generation) endpoints.
Implemented in Phase 9.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/rag",
    summary="RAG status [Phase 9]",
    tags=["RAG"],
)
async def rag_status() -> dict:
    return {"message": "RAG pipeline coming in Phase 9."}
