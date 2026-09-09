"""
Prompt management and execution endpoints.

Implemented endpoints (Phase 2/3):
  POST /api/prompts/run       ← Run a prompt against any configured provider
  GET  /api/prompts           ← List saved prompts (stub — Phase 4)
  POST /api/prompts           ← Create a prompt (stub — Phase 4)

The /run endpoint is the core of the Playground feature.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.schemas.llm import RunPromptRequest, RunPromptResponse
from app.services.prompt_service import PromptService

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/prompts/run",
    response_model=RunPromptResponse,
    summary="Run a prompt",
    description="""
Execute a prompt against any configured LLM provider.

The result is saved as an Experiment record for history and comparison.

**Provider selection:**
- Use `provider: "mock"` for instant results without any API key.
- Set `OPENAI_API_KEY` (or other provider keys) in `.env` to use real models.
- Unconfigured providers return a clear error — they never silently fail.

**Temperature guide:**
- `0.0` → deterministic, best for classification / extraction / JSON
- `0.7` → balanced default
- `1.0` → creative, more varied
""",
    tags=["Prompts"],
    status_code=status.HTTP_200_OK,
)
async def run_prompt(
    request: RunPromptRequest,
    db: AsyncSession = Depends(get_db),
) -> RunPromptResponse:
    """
    Run a prompt and return the LLM response with metadata.

    Always returns 200. LLM errors are encoded in the response body
    (error + error_message fields) rather than raising HTTP exceptions —
    this lets the frontend display the error gracefully without crashing.
    """
    service = PromptService(db)
    return await service.run_prompt(request)


@router.get(
    "/prompts",
    summary="List prompts",
    description="List all saved prompts. Full implementation in Phase 4.",
    tags=["Prompts"],
)
async def list_prompts(db: AsyncSession = Depends(get_db)) -> dict:
    """Returns saved prompts. Full CRUD coming in Phase 4."""
    return {
        "prompts": [],
        "total": 0,
        "message": "Prompt library coming in Phase 4.",
    }


@router.post(
    "/prompts",
    summary="Create a prompt",
    description="Save a new named prompt. Full implementation in Phase 4.",
    tags=["Prompts"],
    status_code=status.HTTP_201_CREATED,
)
async def create_prompt(db: AsyncSession = Depends(get_db)) -> dict:
    return {"message": "Prompt creation coming in Phase 4."}
