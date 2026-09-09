"""
Pydantic schemas for RAG pipeline.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    error_message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RAGQueryRequest(BaseModel):
    """POST /api/rag/query"""
    question: str = Field(..., min_length=1, max_length=4_000)
    provider: str = Field(default="mock")
    model: str = Field(default="")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=8_192)
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    document_ids: Optional[List[str]] = Field(
        default=None,
        description="Limit retrieval to specific documents. None = search all.",
    )


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    content: str
    page_number: Optional[int]
    similarity_score: float


class RAGQueryResponse(BaseModel):
    answer: str
    sources: List[RetrievedChunk]
    provider: str
    model: str
    latency_ms: int
    retrieval_latency_ms: int
    generation_latency_ms: int
    chunks_retrieved: int
