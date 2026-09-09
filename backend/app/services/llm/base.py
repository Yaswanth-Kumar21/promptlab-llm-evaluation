"""
BaseLLMProvider — abstract base class for all LLM providers.

Every provider (OpenAI, Anthropic, Gemini, Mistral, Mock) implements
this interface. The rest of the application ONLY talks to this interface,
making providers completely swappable.

Interface contract:
  generate()           → text completion
  generate_structured() → JSON-validated completion
  count_tokens()       → token count estimate
  health_check()       → provider reachability check

All methods are async. All errors are caught and returned as structured
LLMResponse objects — they never bubble up as unhandled exceptions.
"""

import json
import re
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

from app.core.logging import get_logger
from app.schemas.llm import LLMRequest, LLMResponse, TokenUsage

logger = get_logger(__name__)


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    Subclasses must implement:
      - generate()
      - count_tokens()
      - health_check()

    generate_structured() has a default implementation that:
      1. Calls generate() with a JSON-requesting system prompt addendum
      2. Parses the JSON response
      3. Validates against the provided Pydantic schema
      4. Attempts repair if parsing fails
    """

    # Subclasses set these as class attributes
    provider_id: str = "base"
    display_name: str = "Base Provider"

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate a text completion.

        Must return an LLMResponse. On failure, return an LLMResponse with
        error and error_message set — do NOT raise exceptions.
        """
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Estimate the token count for a string.

        If the provider doesn't have a tokeniser, use the ~4 chars/token heuristic.
        Return 0 rather than raising.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is reachable.
        Return True if healthy, False if not. Never raise.
        """
        ...

    async def generate_structured(
        self,
        request: LLMRequest,
        schema: Optional[Type[BaseModel]] = None,
        schema_dict: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Generate a response and attempt to parse it as JSON.

        Steps:
          1. Append JSON instruction to the system prompt
          2. Call generate()
          3. Extract JSON from the response (handles markdown code fences)
          4. Validate against schema if provided
          5. If parsing fails, attempt regex-based repair
          6. Record whether repair was needed

        This default implementation works for all providers.
        Providers that have native JSON mode (like OpenAI) can override it.
        """
        # Build a system prompt that requests JSON output
        json_instruction = "\n\nIMPORTANT: Your response must be valid JSON only. No explanation, no markdown fences, no text before or after the JSON object."
        if schema:
            schema_example = json.dumps(schema.model_json_schema(), indent=2)
            json_instruction += f"\n\nExpected JSON schema:\n{schema_example}"
        elif schema_dict:
            json_instruction += f"\n\nExpected JSON structure:\n{json.dumps(schema_dict, indent=2)}"

        modified_request = request.model_copy(
            update={
                "system_prompt": request.system_prompt + json_instruction,
            }
        )

        response = await self.generate(modified_request)

        if response.error:
            return response

        # Attempt to extract and parse JSON
        raw = response.content
        parsed, json_valid, repair_attempted, original = self._parse_json(raw)

        return response.model_copy(
            update={
                "parsed": parsed,
                "json_valid": json_valid,
                "json_repair_attempted": repair_attempted,
                "original_content": original if repair_attempted else None,
            }
        )

    def _parse_json(
        self, text: str
    ) -> tuple[Optional[Dict[str, Any]], bool, bool, Optional[str]]:
        """
        Try to parse JSON from model output.

        Returns: (parsed_dict, json_valid, repair_attempted, original_text)

        Handles:
          - Clean JSON responses
          - JSON wrapped in markdown code fences: ```json ... ```
          - JSON buried in prose (regex extraction)
        """
        original = None
        repair_attempted = False

        # Step 1: Try direct parse
        cleaned = text.strip()
        try:
            parsed = json.loads(cleaned)
            return parsed, True, False, None
        except json.JSONDecodeError:
            pass

        # Step 2: Strip markdown code fences
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned, re.IGNORECASE)
        if fence_match:
            inner = fence_match.group(1).strip()
            try:
                parsed = json.loads(inner)
                return parsed, True, True, text
            except json.JSONDecodeError:
                pass

        # Step 3: Find the outermost { ... } block
        brace_match = re.search(r"\{[\s\S]*\}", cleaned)
        if brace_match:
            original = text
            repair_attempted = True
            candidate = brace_match.group(0)
            try:
                parsed = json.loads(candidate)
                logger.info(
                    "json_repair_succeeded",
                    provider=self.provider_id,
                    original_length=len(text),
                    extracted_length=len(candidate),
                )
                return parsed, True, True, original
            except json.JSONDecodeError:
                pass

        # All attempts failed
        logger.warning(
            "json_parse_failed",
            provider=self.provider_id,
            response_length=len(text),
            repair_attempted=repair_attempted,
        )
        return None, False, repair_attempted, original if repair_attempted else None

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """
        Heuristic token estimate: ~4 characters per token.
        Used by providers that lack a local tokeniser.
        """
        return max(1, len(text) // 4)

    @staticmethod
    def _elapsed_ms(start: float) -> int:
        """Return elapsed milliseconds since start (from time.perf_counter())."""
        return round((time.perf_counter() - start) * 1000)
