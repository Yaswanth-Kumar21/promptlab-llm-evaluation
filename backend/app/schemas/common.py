"""
Common Pydantic schemas shared across multiple endpoints.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response body. Never includes stack traces."""
    error: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable explanation")
    request_id: Optional[str] = Field(None, description="Correlate with server logs")
    detail: Optional[Any] = Field(None, description="Structured detail for validation errors")


class SuccessResponse(BaseModel):
    """Generic success acknowledgement."""
    ok: bool = True
    message: str = ""


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
