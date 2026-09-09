"""
Pydantic schemas for the Evaluation Engine.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvaluationMetricResult(BaseModel):
    """
    Result of one evaluator for one response.
    Every evaluator returns this shape.
    """
    metric: str
    score: float = Field(..., ge=0.0, le=100.0)
    passed: bool
    reason: str
    evidence: str
    evaluation_method: str  # deterministic | schema_check | semantic | llm_judge


class EvaluationRunRequest(BaseModel):
    """POST /api/evaluations/run"""
    experiment_id: str
    metrics: List[str] = Field(
        default=["accuracy", "relevance", "json_validity"],
        description="Which metrics to run",
    )
    expected_output: Optional[str] = None
    expected_schema: Optional[Dict[str, Any]] = None


class EvaluationRunResponse(BaseModel):
    experiment_id: str
    metrics_run: List[str]
    results: List[EvaluationMetricResult]
    overall_passed: bool
    average_score: float
