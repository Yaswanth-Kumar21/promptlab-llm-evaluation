"""
AnthropicProvider — Claude models.
Full implementation in Phase 10.
Returns a clean "not yet implemented" response for now.
"""

import time
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.llm import LLMRequest, LLMResponse, TokenUsage
from app.services.llm.base import BaseLLMProvider

logger = get_logger(__name__)


class AnthropicProvider(BaseLLMProvider):
    provider_id = "anthropic"
    display_name = "Anthropic Claude"

    def __init__(self):
        self._configured = bool(
            settings.anthropic_api_key and settings.anthropic_api_key.strip()
        )
        self._default_model = settings.anthropic_default_model

    def _stub_response(self, request: LLMRequest, start: float) -> LLMResponse:
        if not self._configured:
            msg = "Anthropic API key is not configured. Set ANTHROPIC_API_KEY in your .env file."
            err = "provider_not_configured"
        else:
            msg = "Anthropic provider is not yet fully implemented. Coming in Phase 10."
            err = "not_implemented"
        return LLMResponse(
            content="", provider=self.provider_id,
            model=request.model or self._default_model,
            temperature=request.temperature,
            latency_ms=self._elapsed_ms(start),
            usage=TokenUsage(), error=err, error_message=msg,
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        return self._stub_response(request, time.perf_counter())

    def count_tokens(self, text: str) -> int:
        return self._estimate_tokens(text)

    async def health_check(self) -> bool:
        return False
