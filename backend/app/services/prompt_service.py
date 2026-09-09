"""
PromptService — core business logic for running prompts.

Responsibilities:
  1. Validate the request
  2. Select the appropriate provider
  3. Call the provider
  4. Persist the result as an Experiment record
  5. Return a structured response

This service is intentionally thin — it orchestrates other services
rather than implementing logic directly.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.experiment import Experiment
from app.schemas.llm import LLMRequest, RunPromptRequest, RunPromptResponse, TokenUsage
from app.services.llm.registry import get_provider

logger = get_logger(__name__)


class PromptService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_prompt(self, request: RunPromptRequest) -> RunPromptResponse:
        """
        Execute a prompt against an LLM provider and persist the result.

        Steps:
          1. Get provider from registry
          2. Build LLMRequest
          3. Call provider.generate()
          4. Save experiment to database
          5. Return RunPromptResponse

        Errors from the LLM are recorded in the experiment but do NOT
        raise HTTP exceptions — the caller sees a structured error response.
        """
        experiment_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # 1. Get provider
        try:
            provider = get_provider(request.provider)
        except ValueError as exc:
            # Unknown provider — return clean error without saving experiment
            logger.warning("unknown_provider", provider=request.provider)
            return RunPromptResponse(
                experiment_id=experiment_id,
                content="",
                provider=request.provider,
                model=request.model,
                temperature=request.temperature,
                latency_ms=0,
                usage=TokenUsage(),
                error="unknown_provider",
                error_message=str(exc),
                timestamp=timestamp,
            )

        # 2. Build provider request
        llm_request = LLMRequest(
            system_prompt=request.system_prompt,
            user_prompt=request.user_prompt,
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # 3. Call provider
        logger.info(
            "prompt_run_start",
            experiment_id=experiment_id,
            provider=request.provider,
            model=request.model or "(default)",
            temperature=request.temperature,
        )
        llm_response = await provider.generate(llm_request)

        # 4. Persist experiment (best-effort — a DB error must not fail the prompt run)
        try:
            experiment = Experiment(
                id=experiment_id,
                name=f"playground-{request.provider}",
                prompt_version_id=request.prompt_version_id,
                system_prompt=request.system_prompt,
                user_prompt=request.user_prompt,
                provider=request.provider,
                model=llm_response.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                response=llm_response.content,
                response_raw=llm_response.content,
                input_tokens=llm_response.usage.input_tokens,
                output_tokens=llm_response.usage.output_tokens,
                latency_ms=llm_response.latency_ms,
                dataset_name=request.dataset_name or "",
                test_case_id=request.test_case_id or "",
                passed=None,
                error=llm_response.error_message or "",
            )
            self.db.add(experiment)
            # session.commit() is handled by the get_db dependency
        except Exception as db_exc:
            # Log but don't fail — the LLM response is the primary value
            logger.warning(
                "experiment_save_failed",
                experiment_id=experiment_id,
                error=type(db_exc).__name__,
            )

        logger.info(
            "prompt_run_complete",
            experiment_id=experiment_id,
            provider=request.provider,
            model=llm_response.model,
            latency_ms=llm_response.latency_ms,
            success=llm_response.succeeded,
        )

        # 5. Build response
        return RunPromptResponse(
            experiment_id=experiment_id,
            content=llm_response.content,
            provider=llm_response.provider,
            model=llm_response.model,
            temperature=llm_response.temperature,
            latency_ms=llm_response.latency_ms,
            usage=llm_response.usage,
            json_valid=llm_response.json_valid,
            parsed=llm_response.parsed,
            error=llm_response.error,
            error_message=llm_response.error_message,
            timestamp=timestamp,
        )
