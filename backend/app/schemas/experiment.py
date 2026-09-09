"""
Pydantic schemas for Experiment tracking.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class EvaluationResultOut(BaseModel):
    id: str
    metric: str
    score: float
    passed: bool
    reason: str
    evidence: str
    evaluation_method: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ExperimentOut(BaseModel):
    id: str
    name: str
    prompt_id: Optional[str]
    prompt_version_id: Optional[str]
    system_prompt: str
    user_prompt: str
    provider: str
    model: str
    temperature: float
    max_tokens: int
    response: str
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    latency_ms: Optional[int]
    dataset_name: str
    test_case_id: str
    passed: Optional[bool]
    error: str
    created_at: datetime
    evaluation_results: List[EvaluationResultOut] = []

    model_config = {"from_attributes": True}


class ExperimentListOut(BaseModel):
    experiments: List[ExperimentOut]
    total: int
