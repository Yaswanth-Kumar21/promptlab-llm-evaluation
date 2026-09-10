"""Pydantic schemas for RAG endpoints."""

from typing import List, Optional
from pydantic import BaseModel, Field


class RAGSource(BaseModel):
    document_id: str
    chunk_id: str
    filename: str
    page: Optional[int]
    chunk_index: int
    relevance_score: float
    content_preview: str


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    provider: str = Field(default="mock")
    model: str = Field(default="")
    top_k: int = Field(default=5, ge=1, le=20)
    document_id: Optional[str] = Field(
        default=None,
        description="If set, restrict retrieval to one document."
    )


class RAGQueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[RAGSource]
    chunks_retrieved: int
    provider: str
    model: str
    latency_ms: int
    error: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    chunk_count: int
    message: str


class DocumentOut(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    error_message: str

    model_config = {"from_attributes": True}
