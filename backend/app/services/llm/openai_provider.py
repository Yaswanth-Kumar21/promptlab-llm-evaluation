"""
OpenAIProvider — wraps the openai Python SDK.

Handles:
  - Text generation (generate)
  - JSON-mode structured output (generate_structured)
  - Token counting via tiktoken
  - Graceful degradation when the API key is missing
  - Rate-limit and timeout retries (tenacity)
  - Never exposing the API key in logs or responses
"""

import json
import time
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.llm import LLMRequest, LLMResponse, TokenUsage
from app.services.llm.base import BaseLLMProvider

logger = get_logger(__name__)

# Lazy imports — only loaded when the provider is actually used
try:
    import openai
    from openai import AsyncOpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False

try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider using the official openai Python SDK.

    Supports:
      - GPT-4o, GPT-4o-mini, GPT-3.5-turbo
      - Structured output via JSON mode
      - Token counting via tiktoken
      - Retry on rate limits (openai SDK handles this internally)

    Configuration:
      OPENAI_API_KEY=sk-...
      OPENAI_DEFAULT_MODEL=gpt-4o-mini
    """

    provider_id = "openai"
    display_name = "OpenAI"

    def __init__(self):
        self._client: Optional[Any] = None
        self._configured = bool(
            settings.openai_api_key and settings.openai_api_key.strip()
        )
        self._default_model = settings.openai_default_model

        if self._configured and _OPENAI_AVAILABLE:
            self._client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                timeout=60.0,
                max_retries=2,   # auto-retry rate limits
            )

    def _not_configured_response(self, request: LLMRequest, start: float) -> LLMResponse:
        """Return a clean error response when the API key is not set."""
        return LLMResponse(
            content="",
            provider=self.provider_id,
            model=request.model or self._default_model,
            temperature=request.temperature,
            latency_ms=self._elapsed_ms(start),
            usage=TokenUsage(),
            error="provider_not_configured",
            error_message=(
                "OpenAI API key is not configured. "
                "Set OPENAI_API_KEY in your .env file."
            ),
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        start = time.perf_counter()

        if not self._configured or self._client is None:
            return self._not_configured_response(request, start)

        model = request.model.strip() or self._default_model

        messages = []
        if request.system_prompt.strip():
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.user_prompt})

        try:
            completion = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            content = completion.choices[0].message.content or ""
            usage = completion.usage

            latency = self._elapsed_ms(start)
            logger.info(
                "openai_generate",
                model=model,
                input_tokens=usage.prompt_tokens if usage else None,
                output_tokens=usage.completion_tokens if usage else None,
                latency_ms=latency,
            )

            return LLMResponse(
                content=content,
                provider=self.provider_id,
                model=model,
                temperature=request.temperature,
                latency_ms=latency,
                usage=TokenUsage(
                    input_tokens=usage.prompt_tokens if usage else None,
                    output_tokens=usage.completion_tokens if usage else None,
                    total_tokens=usage.total_tokens if usage else None,
                ),
            )

        except Exception as exc:
            latency = self._elapsed_ms(start)
            error_type, error_msg = self._classify_error(exc)

            logger.warning(
                "openai_generate_failed",
                model=model,
                error_type=error_type,
                latency_ms=latency,
                # SECURITY: never log the actual error message as it might contain key fragments
            )

            return LLMResponse(
                content="",
                provider=self.provider_id,
                model=model,
                temperature=request.temperature,
                latency_ms=latency,
                usage=TokenUsage(),
                error=error_type,
                error_message=error_msg,
            )

    async def generate_structured(
        self,
        request: LLMRequest,
        schema: Optional[Type[BaseModel]] = None,
        schema_dict: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Use OpenAI's JSON mode for reliable structured output.
        Falls back to the base class text-then-parse approach if needed.
        """
        start = time.perf_counter()

        if not self._configured or self._client is None:
            return self._not_configured_response(request, start)

        model = request.model.strip() or self._default_model

        # Build schema instruction
        schema_desc = ""
        if schema:
            schema_desc = f"\n\nReturn JSON matching this schema:\n{json.dumps(schema.model_json_schema(), indent=2)}"
        elif schema_dict:
            schema_desc = f"\n\nReturn JSON with this structure:\n{json.dumps(schema_dict, indent=2)}"

        messages = []
        system_content = (request.system_prompt or "You are a helpful assistant.") + schema_desc
        messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": request.user_prompt})

        try:
            completion = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                response_format={"type": "json_object"},  # OpenAI JSON mode
            )

            content = completion.choices[0].message.content or ""
            usage = completion.usage
            latency = self._elapsed_ms(start)

            parsed, json_valid, repair_attempted, original = self._parse_json(content)

            return LLMResponse(
                content=content,
                provider=self.provider_id,
                model=model,
                temperature=request.temperature,
                latency_ms=latency,
                usage=TokenUsage(
                    input_tokens=usage.prompt_tokens if usage else None,
                    output_tokens=usage.completion_tokens if usage else None,
                    total_tokens=usage.total_tokens if usage else None,
                ),
                parsed=parsed,
                json_valid=json_valid,
                json_repair_attempted=repair_attempted,
                original_content=original,
            )

        except Exception as exc:
            latency = self._elapsed_ms(start)
            error_type, error_msg = self._classify_error(exc)
            return LLMResponse(
                content="",
                provider=self.provider_id,
                model=model,
                temperature=request.temperature,
                latency_ms=latency,
                usage=TokenUsage(),
                error=error_type,
                error_message=error_msg,
            )

    def count_tokens(self, text: str) -> int:
        """Use tiktoken for accurate token counting, fall back to heuristic."""
        if not _TIKTOKEN_AVAILABLE:
            return self._estimate_tokens(text)
        try:
            enc = tiktoken.encoding_for_model(self._default_model)
            return len(enc.encode(text))
        except Exception:
            return self._estimate_tokens(text)

    async def health_check(self) -> bool:
        if not self._configured or self._client is None:
            return False
        try:
            # Minimal API call to check connectivity
            await self._client.models.list()
            return True
        except Exception:
            return False

    @staticmethod
    def _classify_error(exc: Exception) -> tuple[str, str]:
        """
        Map SDK exceptions to clean, user-facing error types.
        NEVER include the raw exception message (it may contain key fragments).
        """
        if not _OPENAI_AVAILABLE:
            return "sdk_not_installed", "openai package is not installed."

        exc_type = type(exc).__name__

        if "AuthenticationError" in exc_type:
            return "authentication_error", "Invalid OpenAI API key. Check OPENAI_API_KEY in .env."
        if "RateLimitError" in exc_type:
            return "rate_limit", "OpenAI rate limit exceeded. Please wait and try again."
        if "APITimeoutError" in exc_type or "Timeout" in exc_type:
            return "timeout", "OpenAI request timed out. Try a shorter prompt or increase max_tokens."
        if "BadRequestError" in exc_type:
            return "bad_request", "Invalid request parameters. Check model name and token limits."
        if "APIConnectionError" in exc_type:
            return "connection_error", "Could not connect to OpenAI API. Check your internet connection."
        if "InsufficientQuotaError" in exc_type:
            return "quota_exceeded", "OpenAI quota exceeded. Check your billing settings."

        return "unknown_error", "An unexpected error occurred with the OpenAI provider."
