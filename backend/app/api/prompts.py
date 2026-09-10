"""
Prompt management, execution, and versioning endpoints.

Endpoints:
  POST /api/prompts/run                    Run a prompt (Playground)
  POST /api/prompts/run/technique          Run a prompt technique demo
  GET  /api/prompts                        List saved prompts
  POST /api/prompts                        Create a prompt
  GET  /api/prompts/{id}                   Get a prompt with all versions
  PUT  /api/prompts/{id}                   Update prompt metadata
  DELETE /api/prompts/{id}                 Delete a prompt
  POST /api/prompts/{id}/versions          Add a new version
  GET  /api/prompts/{id}/versions          List versions
  PUT  /api/prompts/{id}/versions/{vid}/best  Mark as best version
  POST /api/prompts/{id}/versions/{vid}/duplicate  Duplicate a version
  POST /api/prompts/compare                Compare multiple versions
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.prompt import Prompt, PromptVersion
from app.schemas.llm import RunPromptRequest, RunPromptResponse, TechniqueRunRequest
from app.schemas.prompt import (
    PromptCreate,
    PromptOut,
    PromptUpdate,
    PromptVersionCreate,
    PromptVersionOut,
    PromptWithVersions,
)
from app.services.prompt_service import PromptService
from app.services.technique_service import TechniqueService

router = APIRouter()
logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Run / Playground
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/prompts/run",
    response_model=RunPromptResponse,
    summary="Run a prompt",
    description="""
Execute a prompt against any configured LLM provider.

The result is saved as an Experiment record for tracking and comparison.

**Provider guide:**
- `mock` — works instantly, no API key required.
- `openai` — set `OPENAI_API_KEY` in `.env`.
- `anthropic` — set `ANTHROPIC_API_KEY`.
- `gemini` — set `GEMINI_API_KEY`.
- `mistral` — set `MISTRAL_API_KEY`.

Errors are returned in the response body (error + error_message),
never as HTTP 500 — so the frontend can display them gracefully.
""",
    tags=["Playground"],
)
async def run_prompt(
    request: RunPromptRequest,
    db: AsyncSession = Depends(get_db),
) -> RunPromptResponse:
    service = PromptService(db)
    return await service.run_prompt(request)


@router.post(
    "/prompts/run/technique",
    response_model=RunPromptResponse,
    summary="Run a prompt technique demo",
    description="""
Run a demonstration of a specific prompt engineering technique.

Techniques:
- `zero_shot` — no examples, just instructions
- `few_shot` — 3 labelled examples
- `role` — role/persona prompting
- `structured` — forces JSON output
- `constraint` — explicit word/format constraints
""",
    tags=["Playground"],
)
async def run_technique(
    request: TechniqueRunRequest,
    db: AsyncSession = Depends(get_db),
) -> RunPromptResponse:
    service = TechniqueService(db)
    return await service.run_technique(request)


# ─────────────────────────────────────────────────────────────────────────────
# Prompt CRUD
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/prompts",
    response_model=dict,
    summary="List saved prompts",
    tags=["Prompts"],
)
async def list_prompts(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    stmt = select(Prompt).order_by(Prompt.updated_at.desc())

    if category:
        stmt = stmt.where(Prompt.category == category)
    if search:
        stmt = stmt.where(Prompt.name.ilike(f"%{search}%"))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Paginate
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    prompts = result.scalars().all()

    # Get version counts
    prompt_ids = [p.id for p in prompts]
    version_counts: dict[str, int] = {}
    if prompt_ids:
        vc_stmt = (
            select(PromptVersion.prompt_id, func.count(PromptVersion.id).label("cnt"))
            .where(PromptVersion.prompt_id.in_(prompt_ids))
            .group_by(PromptVersion.prompt_id)
        )
        vc_result = await db.execute(vc_stmt)
        version_counts = {row.prompt_id: row.cnt for row in vc_result}

    out = []
    for p in prompts:
        d = PromptOut(
            id=p.id,
            name=p.name,
            description=p.description,
            category=p.category,
            tags=p.tags,
            created_at=p.created_at,
            updated_at=p.updated_at,
            version_count=version_counts.get(p.id, 0),
        )
        out.append(d.model_dump())

    return {
        "prompts": out,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


@router.post(
    "/prompts",
    response_model=PromptWithVersions,
    summary="Create a prompt",
    status_code=status.HTTP_201_CREATED,
    tags=["Prompts"],
)
async def create_prompt(
    data: PromptCreate,
    db: AsyncSession = Depends(get_db),
) -> PromptWithVersions:
    prompt = Prompt(
        name=data.name,
        description=data.description,
        category=data.category,
        tags=data.tags,
    )
    db.add(prompt)
    await db.flush()  # get the ID before commit

    logger.info("prompt_created", prompt_id=prompt.id, name=prompt.name)

    return PromptWithVersions(
        id=prompt.id,
        name=prompt.name,
        description=prompt.description,
        category=prompt.category,
        tags=prompt.tags,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
        version_count=0,
        versions=[],
    )


@router.get(
    "/prompts/{prompt_id}",
    response_model=PromptWithVersions,
    summary="Get prompt with all versions",
    tags=["Prompts"],
)
async def get_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db),
) -> PromptWithVersions:
    stmt = (
        select(Prompt)
        .where(Prompt.id == prompt_id)
        .options(selectinload(Prompt.versions))
    )
    result = await db.execute(stmt)
    prompt = result.scalar_one_or_none()

    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found.")

    versions_out = [
        PromptVersionOut.model_validate(v)
        for v in sorted(prompt.versions, key=lambda x: x.version_number)
    ]

    return PromptWithVersions(
        id=prompt.id,
        name=prompt.name,
        description=prompt.description,
        category=prompt.category,
        tags=prompt.tags,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
        version_count=len(versions_out),
        versions=versions_out,
    )


@router.put(
    "/prompts/{prompt_id}",
    response_model=PromptOut,
    summary="Update prompt metadata",
    tags=["Prompts"],
)
async def update_prompt(
    prompt_id: str,
    data: PromptUpdate,
    db: AsyncSession = Depends(get_db),
) -> PromptOut:
    result = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found.")

    if data.name is not None:
        prompt.name = data.name
    if data.description is not None:
        prompt.description = data.description
    if data.category is not None:
        prompt.category = data.category
    if data.tags is not None:
        prompt.tags = data.tags

    # Get version count
    vc = await db.execute(
        select(func.count(PromptVersion.id)).where(PromptVersion.prompt_id == prompt_id)
    )
    version_count = vc.scalar_one()

    logger.info("prompt_updated", prompt_id=prompt_id)
    return PromptOut(
        id=prompt.id,
        name=prompt.name,
        description=prompt.description,
        category=prompt.category,
        tags=prompt.tags,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
        version_count=version_count,
    )


@router.delete(
    "/prompts/{prompt_id}",
    summary="Delete a prompt",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Prompts"],
)
async def delete_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found.")

    await db.delete(prompt)
    logger.info("prompt_deleted", prompt_id=prompt_id)


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Versions
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/prompts/{prompt_id}/versions",
    response_model=PromptVersionOut,
    summary="Add a new version to a prompt",
    status_code=status.HTTP_201_CREATED,
    tags=["Versions"],
)
async def create_version(
    prompt_id: str,
    data: PromptVersionCreate,
    db: AsyncSession = Depends(get_db),
) -> PromptVersionOut:
    # Verify prompt exists
    result = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found.")

    # Get next version number
    vc = await db.execute(
        select(func.count(PromptVersion.id)).where(PromptVersion.prompt_id == prompt_id)
    )
    next_version = (vc.scalar_one() or 0) + 1

    version = PromptVersion(
        prompt_id=prompt_id,
        version_number=next_version,
        system_prompt=data.system_prompt,
        user_prompt_template=data.user_prompt_template,
        provider=data.provider,
        model=data.model,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        notes=data.notes,
        author=data.author,
        is_best=False,
    )
    db.add(version)
    await db.flush()

    logger.info(
        "version_created",
        prompt_id=prompt_id,
        version_id=version.id,
        version_number=next_version,
    )
    return PromptVersionOut.model_validate(version)


@router.get(
    "/prompts/{prompt_id}/versions",
    response_model=List[PromptVersionOut],
    summary="List versions of a prompt",
    tags=["Versions"],
)
async def list_versions(
    prompt_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[PromptVersionOut]:
    result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.version_number)
    )
    versions = result.scalars().all()
    return [PromptVersionOut.model_validate(v) for v in versions]


@router.put(
    "/prompts/{prompt_id}/versions/{version_id}/best",
    response_model=PromptVersionOut,
    summary="Mark a version as best",
    description="Clears the best flag on all other versions for this prompt, then sets it on the specified version.",
    tags=["Versions"],
)
async def mark_best_version(
    prompt_id: str,
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> PromptVersionOut:
    # Clear best on all versions for this prompt
    all_versions_result = await db.execute(
        select(PromptVersion).where(PromptVersion.prompt_id == prompt_id)
    )
    for v in all_versions_result.scalars().all():
        v.is_best = False

    # Set best on the target version
    target_result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.id == version_id,
            PromptVersion.prompt_id == prompt_id,
        )
    )
    target = target_result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Version not found.")

    target.is_best = True
    logger.info("version_marked_best", prompt_id=prompt_id, version_id=version_id)
    return PromptVersionOut.model_validate(target)


@router.post(
    "/prompts/{prompt_id}/versions/{version_id}/duplicate",
    response_model=PromptVersionOut,
    summary="Duplicate a version",
    description="Creates a new version with the same content as the source, with a blank notes field.",
    status_code=status.HTTP_201_CREATED,
    tags=["Versions"],
)
async def duplicate_version(
    prompt_id: str,
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> PromptVersionOut:
    result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.id == version_id,
            PromptVersion.prompt_id == prompt_id,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Version not found.")

    vc = await db.execute(
        select(func.count(PromptVersion.id)).where(PromptVersion.prompt_id == prompt_id)
    )
    next_version = (vc.scalar_one() or 0) + 1

    new_version = PromptVersion(
        prompt_id=prompt_id,
        version_number=next_version,
        system_prompt=source.system_prompt,
        user_prompt_template=source.user_prompt_template,
        provider=source.provider,
        model=source.model,
        temperature=source.temperature,
        max_tokens=source.max_tokens,
        notes=f"Duplicated from V{source.version_number}",
        author=source.author,
        is_best=False,
    )
    db.add(new_version)
    await db.flush()

    logger.info(
        "version_duplicated",
        source_id=version_id,
        new_id=new_version.id,
        new_version_number=next_version,
    )
    return PromptVersionOut.model_validate(new_version)
