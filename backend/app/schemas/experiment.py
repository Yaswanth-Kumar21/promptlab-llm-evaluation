"""
Pydantic schemas for Experiment responses.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ExperimentOut(BaseModel):
    id: str
    name: str
    provider: str
    model: str
    temperature: float
    system_prompt: str
    user_prompt: str
    response: str
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    latency_ms: Optional[int]
    passed: Optional[bool]
    error: Optional[str]
    created_at: Optional[datetime]
    prompt_version_id: Optional[str]

    model_config = {"from_attributes": True}
