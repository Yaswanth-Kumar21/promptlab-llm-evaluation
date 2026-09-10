"""
Evaluation Engine API — Phases 7 & 8.

Endpoints:
  POST /api/evaluations/run           Evaluate a response directly
  POST /api/evaluations/dataset       Run a test case from a dataset file
  GET  /api/evaluations               List stored evaluation results
  POST /api/evaluations/safety        Run a safety test (Phase 8)
  POST /api/evaluations/bias          Run a bias comparison (Phase 8)
  GET  /api/evaluations/datasets      List available datasets and their cases
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.evaluation import EvaluationResult as EvalResultModel
from app.models.experiment import Experiment
from app.schemas.evaluation import (
    BiasTestRequest, BiasTestResult,
    EvaluationReport, EvaluationResult,
    EvaluationResultOut, RunDatasetEvaluationRequest,
    RunEvaluationRequest, SafetyTestRequest, SafetyTestResult,
)
from app.services.evaluation_service import evaluate_response
from app.services.llm.registry import get_provider
from app.services.safety_service import run_bias_test, run_safety_test
from app.schemas.llm import LLMRequest

router = APIRouter()
logger = get_logger(__name__)

# Path to the evaluation datasets directory
_DATASETS_DIR = Path(__file__).parent.parent.parent.parent / "evaluation" / "datasets"


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/evaluations/run
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/evaluations/run",
    response_model=EvaluationResultOut,
    summary="Evaluate a response",
    description="""
Evaluate an LLM response on the requested metrics.

**Metrics available:**
- `accuracy`     — keyword/exact match against expected output (requires expected_output)
- `relevance`    — key-term overlap between prompt and response
- `tone`         — detected vs expected tone (formal/informal/positive/negative/neutral)
- `json_validity`— validates JSON structure and schema
- `groundedness` — checks response claims against context chunks (RAG)
- `safety`       — injection markers, PII patterns, system prompt leaks

All checks are **deterministic**. No LLM-as-judge is used here.
""",
    tags=["Evaluation"],
)
async def run_evaluation(
    request: RunEvaluationRequest,
    db: AsyncSession = Depends(get_db),
) -> EvaluationResultOut:
    report = evaluate_response(
        response=request.response,
        user_prompt=request.user_prompt,
        system_prompt=request.system_prompt,
        expected_output=request.expected_output,
        expected_tone=request.expected_tone,
        expected_json_schema=request.expected_json_schema,
        context_chunks=request.context_chunks,
        metrics=request.metrics,
    )

    # Persist each metric result
    experiment_id = str(uuid.uuid4())
    try:
        for r in report.results:
            row = EvalResultModel(
                experiment_id=experiment_id,
                metric=r.metric,
                score=r.score,
                passed=r.passed,
                reason=r.reason,
                evidence=r.evidence,
                evaluation_method=r.evaluation_method,
            )
            db.add(row)
    except Exception as e:
        logger.warning("eval_persist_failed", error=type(e).__name__)

    logger.info(
        "evaluation_complete",
        metrics=report.metrics_run,
        overall_score=report.overall_score,
        passed=report.overall_passed,
    )

    return EvaluationResultOut(
        experiment_id=experiment_id,
        user_prompt=request.user_prompt,
        response=request.response,
        provider="direct",
        model="direct",
        latency_ms=0,
        evaluation=report,
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/evaluations/dataset
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/evaluations/dataset",
    response_model=EvaluationResultOut,
    summary="Run a test case from an evaluation dataset",
    description="""
Load a specific test case from one of the evaluation datasets, run the LLM,
then evaluate the response.

Available datasets: `classification`, `summarization`, `extraction`, `rag`, `safety`
""",
    tags=["Evaluation"],
)
async def run_dataset_evaluation(
    request: RunDatasetEvaluationRequest,
    db: AsyncSession = Depends(get_db),
) -> EvaluationResultOut:
    # Load dataset
    dataset_path = _DATASETS_DIR / f"{request.dataset}.json"
    if not dataset_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{request.dataset}' not found. Available: classification, summarization, extraction, rag, safety",
        )

    try:
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load dataset: {type(e).__name__}")

    # Find the test case
    cases = dataset.get("cases", [])
    case = next((c for c in cases if c["id"] == request.test_case_id), None)
    if not case:
        ids = [c["id"] for c in cases[:5]]
        raise HTTPException(
            status_code=404,
            detail=f"Test case '{request.test_case_id}' not found in '{request.dataset}'. First IDs: {ids}",
        )

    # Determine the prompt
    user_prompt = case.get("input") or case.get("question", "")
    system_prompt = case.get("system_prompt", "You are a helpful, accurate assistant.")
    if not user_prompt:
        raise HTTPException(status_code=422, detail="Test case has no 'input' or 'question' field.")

    # Prepend context for RAG/safety test cases
    context = case.get("context", "")
    if context:
        user_prompt = f"Context:\n{context}\n\nQuestion: {user_prompt}"

    # Run LLM
    import time
    start = time.perf_counter()
    try:
        provider_obj = get_provider(request.provider)
        llm_req = LLMRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=512,
        )
        llm_resp = await provider_obj.generate(llm_req)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM call failed: {type(e).__name__}: {e}")

    latency_ms = round((time.perf_counter() - start) * 1000)

    # Determine metrics and expected values
    expected_output = case.get("expected_output")
    if expected_output == "not_in_context":
        expected_output = None   # handled as refusal check

    # For safety/hallucination — check refusal behaviour
    expected_behavior = case.get("expected_behavior", "")
    metrics = ["relevance", "safety"]
    if expected_output:
        metrics.append("accuracy")
    if request.dataset == "extraction":
        metrics.append("json_validity")

    report = evaluate_response(
        response=llm_resp.content,
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        expected_output=expected_output,
        metrics=metrics,
    )

    # If this is a refusal case, add a pass/fail for the refusal check
    if expected_behavior == "refuse_with_not_in_context":
        from app.services.safety_service import _REFUSAL_PHRASES
        lower = llm_resp.content.lower()
        refused = any(p in lower for p in _REFUSAL_PHRASES)
        report.results.append(EvaluationResult(
            metric="hallucination_refusal",
            score=100.0 if refused else 0.0,
            passed=refused,
            reason="Model correctly refused (context gap)." if refused else "Model answered without refusing — possible hallucination.",
            evidence=llm_resp.content[:200],
            evaluation_method="deterministic",
        ))
        report.metrics_run.append("hallucination_refusal")
        # Recalculate overall
        if report.results:
            report.overall_score = round(sum(r.score for r in report.results) / len(report.results), 1)
            report.overall_passed = all(r.passed for r in report.results)

    # Persist
    experiment_id = str(uuid.uuid4())
    try:
        exp = Experiment(
            id=experiment_id,
            name=f"dataset-{request.dataset}-{request.test_case_id}",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            provider=request.provider,
            model=llm_resp.model,
            temperature=request.temperature,
            response=llm_resp.content,
            latency_ms=latency_ms,
            dataset_name=request.dataset,
            test_case_id=request.test_case_id,
            passed=report.overall_passed,
        )
        db.add(exp)
        for r in report.results:
            db.add(EvalResultModel(
                experiment_id=experiment_id,
                metric=r.metric,
                score=r.score,
                passed=r.passed,
                reason=r.reason,
                evidence=r.evidence,
                evaluation_method=r.evaluation_method,
            ))
    except Exception as e:
        logger.warning("dataset_eval_persist_failed", error=type(e).__name__)

    logger.info(
        "dataset_eval_complete",
        dataset=request.dataset,
        case_id=request.test_case_id,
        score=report.overall_score,
        passed=report.overall_passed,
    )

    return EvaluationResultOut(
        experiment_id=experiment_id,
        user_prompt=user_prompt,
        response=llm_resp.content,
        provider=request.provider,
        model=llm_resp.model,
        latency_ms=latency_ms,
        evaluation=report,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/evaluations
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/evaluations",
    summary="List stored evaluation results",
    tags=["Evaluation"],
)
async def list_evaluations(
    metric: Optional[str] = Query(None, description="Filter by metric name"),
    passed: Optional[bool] = Query(None, description="Filter by pass/fail"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from sqlalchemy import func
    stmt = select(EvalResultModel).order_by(desc(EvalResultModel.created_at))
    if metric:
        stmt = stmt.where(EvalResultModel.metric == metric)
    if passed is not None:
        stmt = stmt.where(EvalResultModel.passed == passed)

    count = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    rows = (await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))).scalars().all()

    return {
        "evaluations": [
            {
                "id": r.id,
                "experiment_id": r.experiment_id,
                "metric": r.metric,
                "score": r.score,
                "passed": r.passed,
                "reason": r.reason,
                "evaluation_method": r.evaluation_method,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": count,
        "page": page,
        "pages": max(1, (count + page_size - 1) // page_size),
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/evaluations/datasets
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/evaluations/datasets",
    summary="List available evaluation datasets",
    tags=["Evaluation"],
)
async def list_datasets() -> dict:
    datasets = []
    for name in ["classification", "summarization", "extraction", "rag", "safety"]:
        path = _DATASETS_DIR / f"{name}.json"
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                meta = data.get("_meta", {})
                cases = data.get("cases", [])
                datasets.append({
                    "name": name,
                    "description": meta.get("description", ""),
                    "case_count": len(cases),
                    "case_ids": [c["id"] for c in cases],
                    "categories": list({c.get("category", "") for c in cases}),
                })
            except Exception:
                datasets.append({"name": name, "error": "Could not load"})
    return {"datasets": datasets, "total": len(datasets)}


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/evaluations/safety  (Phase 8)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/evaluations/safety",
    response_model=SafetyTestResult,
    summary="Run a safety test",
    description="""
Run a prompt injection, hallucination, or PII test.

The attack input is sent to the LLM and the response is evaluated against
the expected behavior.

**Expected behaviors:**
- `refuse_and_continue_task` — model ignores attack, continues task
- `refuse_to_reveal_system_prompt` — model does not leak system prompt
- `treat_as_plain_text` — injected content treated as data
- `refuse_with_not_in_context` — model refuses to answer (hallucination test)
- `answer_from_context` — positive control: model should answer

All evaluation is **rule-based** — no LLM judge.
""",
    tags=["Safety"],
)
async def run_safety_test_endpoint(
    request: SafetyTestRequest,
    db: AsyncSession = Depends(get_db),
) -> SafetyTestResult:
    import time
    start = time.perf_counter()

    try:
        provider_obj = get_provider(request.provider)
        llm_req = LLMRequest(
            system_prompt=request.system_prompt,
            user_prompt=request.attack_input,
            provider=request.provider,
            model=request.model,
            temperature=0.0,   # deterministic for safety tests
            max_tokens=512,
        )
        llm_resp = await provider_obj.generate(llm_req)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM call failed: {type(e).__name__}")

    latency_ms = round((time.perf_counter() - start) * 1000)

    result = run_safety_test(
        attack_input=request.attack_input,
        response=llm_resp.content,
        system_prompt=request.system_prompt,
        expected_behavior=request.expected_behavior,
        attack_category=request.attack_category,
        provider=request.provider,
        model=llm_resp.model,
        latency_ms=latency_ms,
    )

    logger.info(
        "safety_test_endpoint",
        category=request.attack_category,
        passed=result.passed,
        provider=request.provider,
    )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/evaluations/bias  (Phase 8)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/evaluations/bias",
    response_model=BiasTestResult,
    summary="Run a bias comparison test",
    description="""
Compare two responses to prompts that are identical except for one
non-job-relevant demographic attribute.

A high difference score indicates potential bias.

**Disclaimer:** Bias evaluation is experimental and does not constitute
a comprehensive fairness audit.
""",
    tags=["Safety"],
)
async def run_bias_test_endpoint(
    request: BiasTestRequest,
    db: AsyncSession = Depends(get_db),
) -> BiasTestResult:
    import time

    try:
        provider_obj = get_provider(request.provider)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Run both prompts
    async def _run(user_prompt: str) -> str:
        start = time.perf_counter()
        resp = await provider_obj.generate(LLMRequest(
            system_prompt=request.system_prompt,
            user_prompt=user_prompt,
            provider=request.provider,
            model=request.model,
            temperature=0.0,
            max_tokens=512,
        ))
        return resp.content

    response_a = await _run(request.prompt_a)
    response_b = await _run(request.prompt_b)

    result = run_bias_test(
        response_a=response_a,
        response_b=response_b,
        pair_id=request.pair_id,
    )

    logger.info(
        "bias_test_endpoint",
        pair_id=request.pair_id,
        bias_detected=result.bias_detected,
        difference_score=result.difference_score,
    )
    return result
