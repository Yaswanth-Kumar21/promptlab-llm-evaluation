"""
Experiment tracking endpoints.

Endpoints:
  GET  /api/experiments              List experiments with pagination & filters
  GET  /api/experiments/{id}         Get a single experiment with details
  GET  /api/experiments/stats        Aggregate stats for the dashboard
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.experiment import Experiment

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/experiments",
    summary="List experiments",
    description="Returns all recorded prompt runs with pagination and optional provider/prompt filters.",
    tags=["Experiments"],
)
async def list_experiments(
    provider: Optional[str] = Query(None),
    prompt_version_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    stmt = select(Experiment).order_by(desc(Experiment.created_at))

    if provider:
        stmt = stmt.where(Experiment.provider == provider)
    if prompt_version_id:
        stmt = stmt.where(Experiment.prompt_version_id == prompt_version_id)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    experiments = result.scalars().all()

    def _to_dict(e: Experiment) -> dict:
        return {
            "id": e.id,
            "name": e.name,
            "provider": e.provider,
            "model": e.model,
            "temperature": e.temperature,
            "system_prompt": e.system_prompt[:200] + "…" if len(e.system_prompt) > 200 else e.system_prompt,
            "user_prompt": e.user_prompt[:200] + "…" if len(e.user_prompt) > 200 else e.user_prompt,
            "response": e.response[:300] + "…" if len(e.response) > 300 else e.response,
            "input_tokens": e.input_tokens,
            "output_tokens": e.output_tokens,
            "latency_ms": e.latency_ms,
            "passed": e.passed,
            "error": e.error or None,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }

    return {
        "experiments": [_to_dict(e) for e in experiments],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get(
    "/experiments/stats",
    summary="Dashboard stats",
    description="Aggregate counts and averages for the dashboard.",
    tags=["Experiments"],
)
async def get_stats(db: AsyncSession = Depends(get_db)) -> dict:
    from app.models.prompt import Prompt, PromptVersion

    total_experiments = (await db.execute(select(func.count(Experiment.id)))).scalar_one()
    total_prompts = (await db.execute(select(func.count(Prompt.id)))).scalar_one()
    total_versions = (await db.execute(select(func.count(PromptVersion.id)))).scalar_one()

    avg_latency_result = await db.execute(
        select(func.avg(Experiment.latency_ms)).where(Experiment.latency_ms.isnot(None))
    )
    avg_latency = avg_latency_result.scalar_one()

    # Provider breakdown
    provider_result = await db.execute(
        select(Experiment.provider, func.count(Experiment.id).label("cnt"))
        .group_by(Experiment.provider)
        .order_by(desc("cnt"))
    )
    provider_counts = [
        {"provider": row.provider, "count": row.cnt}
        for row in provider_result
    ]

    return {
        "total_experiments": total_experiments,
        "total_prompts": total_prompts,
        "total_versions": total_versions,
        "avg_latency_ms": round(avg_latency) if avg_latency else None,
        "provider_breakdown": provider_counts,
    }


@router.get(
    "/experiments/{experiment_id}",
    summary="Get a single experiment",
    tags=["Experiments"],
)
async def get_experiment(
    experiment_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")

    return {
        "id": exp.id,
        "name": exp.name,
        "provider": exp.provider,
        "model": exp.model,
        "temperature": exp.temperature,
        "max_tokens": exp.max_tokens,
        "system_prompt": exp.system_prompt,
        "user_prompt": exp.user_prompt,
        "response": exp.response,
        "input_tokens": exp.input_tokens,
        "output_tokens": exp.output_tokens,
        "latency_ms": exp.latency_ms,
        "dataset_name": exp.dataset_name,
        "test_case_id": exp.test_case_id,
        "passed": exp.passed,
        "error": exp.error or None,
        "created_at": exp.created_at.isoformat() if exp.created_at else None,
        "prompt_version_id": exp.prompt_version_id,
    }
