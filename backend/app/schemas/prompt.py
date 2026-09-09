"""
Pydantic schemas for Prompt and PromptVersion CRUD.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ── Prompt ────────────────────────────────────────────────────────────────────

class PromptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=2_000)
    category: str = Field(default="general", max_length=100)
    tags: str = Field(default="", description="Comma-separated tags")


class PromptUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None


class PromptOut(BaseModel):
    id: str
    name: str
    description: str
    category: str
    tags: str
    created_at: datetime
    updated_at: datetime
    version_count: int = 0

    model_config = {"from_attributes": True}


# ── PromptVersion ─────────────────────────────────────────────────────────────

class PromptVersionCreate(BaseModel):
    system_prompt: str = Field(default="", max_length=32_000)
    user_prompt_template: str = Field(..., min_length=1, max_length=32_000)
    provider: str = Field(default="mock", max_length=50)
    model: str = Field(default="", max_length=100)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=16_384)
    notes: str = Field(default="", max_length=2_000)
    author: str = Field(default="", max_length=100)


class PromptVersionOut(BaseModel):
    id: str
    prompt_id: str
    version_number: int
    system_prompt: str
    user_prompt_template: str
    provider: str
    model: str
    temperature: float
    max_tokens: int
    notes: str
    author: str
    is_best: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PromptWithVersions(PromptOut):
    versions: List[PromptVersionOut] = []
