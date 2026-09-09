"""
GeminiProvider — Google Gemini models.
Full implementation in Phase 10.
"""

import time
from app.core.config import settings
from app.schemas.llm import LLMRequest, LLMResponse, TokenUsage
from app.services.llm.base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    provider_id = "gemini"
    display_name = "Google Gemini"

    def __init__(self):
        self._configured = bool(
            settings.gemini_api_key and settings.gemini_api_key.strip()
        )
        self._default_model = settings.gemini_default_model

    def _stub_response(self, request: LLMRequest, start: float) -> LLMResponse:
        if not self._configured:
            msg = "Gemini API key is not configured. Set GEMINI_API_KEY in your .env file."
            err = "provider_not_configured"
        else:
            msg = "Gemini provider is not yet fully implemented. Coming in Phase 10."
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
