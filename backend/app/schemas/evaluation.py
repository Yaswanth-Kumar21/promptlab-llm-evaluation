"""
Pydantic schemas for the Evaluation Engine (Phase 7) and Safety Lab (Phase 8).
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Per-metric result ─────────────────────────────────────────────────────────

class EvaluationResult(BaseModel):
    """Result of one evaluator for one response."""
    metric: str
    score: float = Field(..., ge=0.0, le=100.0)
    passed: bool
    reason: str
    evidence: str
    evaluation_method: str   # deterministic | schema_check | semantic | llm_judge


# ── Composite report ──────────────────────────────────────────────────────────

class EvaluationReport(BaseModel):
    """Composite result from running multiple evaluators on one response."""
    results: List[EvaluationResult]
    overall_score: float
    overall_passed: bool
    metrics_run: List[str]


# ── API request / response ────────────────────────────────────────────────────

class RunEvaluationRequest(BaseModel):
    """POST /api/evaluations/run — evaluate a response directly."""
    user_prompt: str = Field(..., min_length=1, max_length=32_000)
    response: str    = Field(..., min_length=1, max_length=32_000)
    system_prompt: str = Field(default="")
    expected_output: Optional[str]            = None
    expected_tone: Optional[str]              = None
    expected_json_schema: Optional[Dict[str, Any]] = None
    context_chunks: Optional[List[str]]       = None
    metrics: List[str] = Field(
        default=["accuracy", "relevance", "tone", "safety"],
        description="Which metrics to run. Options: accuracy relevance tone json_validity groundedness safety"
    )


class RunDatasetEvaluationRequest(BaseModel):
    """POST /api/evaluations/dataset — run a test case from a JSON dataset file."""
    dataset: str         = Field(..., description="Dataset name: classification | summarization | extraction | rag | safety")
    test_case_id: str    = Field(..., description="Case ID from the dataset file, e.g. cls_001")
    provider: str        = Field(default="mock")
    model: str           = Field(default="")
    temperature: float   = Field(default=0.0, ge=0.0, le=2.0)
    prompt_version_id: Optional[str] = None


class EvaluationResultOut(BaseModel):
    """API response for a single evaluation run."""
    experiment_id: str
    user_prompt: str
    response: str
    provider: str
    model: str
    latency_ms: int
    evaluation: EvaluationReport


# ── Safety schemas ────────────────────────────────────────────────────────────

class SafetyTestRequest(BaseModel):
    """POST /api/evaluations/safety — run a safety test case."""
    attack_input: str  = Field(..., min_length=1, max_length=16_000)
    system_prompt: str = Field(default="You are a helpful assistant.")
    provider: str      = Field(default="mock")
    model: str         = Field(default="")
    expected_behavior: str = Field(
        default="refuse_and_continue_task",
        description="Expected behavior: refuse_and_continue_task | refuse_to_reveal_system_prompt | treat_as_plain_text | answer_from_context | refuse"
    )
    attack_category: str = Field(default="prompt_injection")


class SafetyTestResult(BaseModel):
    """Result of one safety test."""
    attack_input: str
    response: str
    passed: bool
    score: float
    attack_category: str
    expected_behavior: str
    detected_issues: List[str]
    explanation: str
    latency_ms: int
    provider: str
    model: str


class BiasTestRequest(BaseModel):
    """POST /api/evaluations/bias — compare two prompts that differ by one demographic attribute."""
    prompt_a: str  = Field(..., min_length=1)
    prompt_b: str  = Field(..., min_length=1)
    system_prompt: str = Field(default="You are a fair, unbiased assistant.")
    provider: str  = Field(default="mock")
    model: str     = Field(default="")
    pair_id: Optional[str] = None


class BiasTestResult(BaseModel):
    """Result of a bias comparison test."""
    pair_id: Optional[str]
    response_a: str
    response_b: str
    score_a: Optional[float]
    score_b: Optional[float]
    bias_detected: bool
    difference_score: float    # 0.0 – 1.0
    explanation: str
    disclaimer: str = (
        "Bias evaluation is experimental and does not constitute "
        "a comprehensive fairness audit."
    )
