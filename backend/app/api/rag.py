"""
RAG endpoints — Phase 9.

POST /api/rag/query      Query the knowledge base with retrieval + LLM
GET  /api/rag/status     Vector store stats
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse
from app.services.rag_service import query_rag
from app.services.vector_store import get_vector_store

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/rag/query",
    response_model=RAGQueryResponse,
    summary="Query the RAG knowledge base",
    description="""
Ask a question answered by your uploaded documents.

**Pipeline:**
1. Embed the question using all-MiniLM-L6-v2
2. Find the top-k most similar document chunks (cosine similarity)
3. Build a context-injected prompt with `<context>` delimiters (injection defence)
4. Call the LLM — it must answer from context only
5. Return the answer with source citations

**If the answer isn't in the documents**, the model says:
"I don't have enough information in the provided context."

This is the hallucination prevention mechanism for RAG.
""",
    tags=["RAG"],
)
async def rag_query(
    request: RAGQueryRequest,
    db: AsyncSession = Depends(get_db),
) -> RAGQueryResponse:
    store = get_vector_store()
    if store.count() == 0:
        return RAGQueryResponse(
            question=request.question,
            answer="No documents have been uploaded yet. Please upload a document first using POST /api/documents/upload.",
            sources=[],
            chunks_retrieved=0,
            provider=request.provider,
            model="",
            latency_ms=0,
        )

    return await query_rag(request=request, db=db)


@router.get(
    "/rag/status",
    summary="Vector store status",
    tags=["RAG"],
)
async def rag_status() -> dict:
    store = get_vector_store()
    return {
        "total_chunks": store.count(),
        "documents_indexed": len(store.list_documents()),
        "document_ids": store.list_documents(),
        "store_type": "local_json",
        "note": "Production: replace LocalVectorStore with ChromaDB or pgvector.",
    }
