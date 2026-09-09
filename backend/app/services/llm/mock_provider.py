"""
MockProvider — deterministic local provider for development and testing.

Purpose:
  - Works with zero configuration (no API key needed)
  - Returns predictable, structured responses
  - Makes the entire UI and evaluation pipeline testable without spending money
  - Simulates realistic token counts and latency

The mock provider has two models:
  mock-echo      → returns a rich text response based on the prompt
  mock-structured → returns valid JSON for structured output testing

IMPORTANT: The mock provider ALWAYS succeeds and ALWAYS returns valid
responses. It is designed to verify that the surrounding plumbing works —
not to test LLM capabilities.
"""

import asyncio
import json
import re
import time
from typing import Optional

from app.core.logging import get_logger
from app.schemas.llm import LLMRequest, LLMResponse, TokenUsage
from app.services.llm.base import BaseLLMProvider

logger = get_logger(__name__)

# ── Demo response templates ───────────────────────────────────────────────────
# These are keyed by keywords found in the prompt so the mock gives
# contextually relevant (if canned) responses.

_KEYWORD_RESPONSES = {
    "rest api": """REST (Representational State Transfer) is an architectural style for designing networked applications.

Key concepts:
- **Resources**: Everything is a resource identified by a URL (e.g., /users/42)
- **HTTP methods**: GET (read), POST (create), PUT/PATCH (update), DELETE (remove)
- **Stateless**: Each request contains all information needed — no server-side session
- **Representations**: Resources are transferred as JSON or XML

Example:
GET /api/users/42 → returns user 42's data as JSON
POST /api/users   → creates a new user from the JSON body
DELETE /api/users/42 → removes user 42

REST APIs power most modern web services including Twitter, GitHub, and Stripe.

[Mock response — connect a real provider to see live LLM output]""",

    "summarize": """Here is a concise summary of the provided content:

• The text introduces the main subject and establishes its importance in the field.
• Key findings or arguments are presented with supporting evidence from credible sources.
• The author highlights practical implications and real-world applications.
• Limitations and areas for future research are acknowledged.
• The conclusion reinforces the central thesis and suggests next steps.

[Mock response — connect a real provider to see live LLM output]""",

    "summarise": """Here is a concise summary of the provided content:

• The text introduces the main subject and establishes its importance in the field.
• Key findings or arguments are presented with supporting evidence from credible sources.
• The author highlights practical implications and real-world applications.
• Limitations and areas for future research are acknowledged.
• The conclusion reinforces the central thesis and suggests next steps.

[Mock response — connect a real provider to see live LLM output]""",

    "classify": "positive\n\n[Mock response — the mock provider classified this as positive based on keyword analysis]",

    "sentiment": "Sentiment: **positive**\nConfidence: 0.87\nReason: The text contains predominantly positive language and constructive framing.\n\n[Mock response]",

    "extract": json.dumps({
        "extracted_fields": {
            "name": "Example Entity",
            "date": "2026-01-01",
            "value": 42
        },
        "confidence": 0.92,
        "note": "Mock extraction — connect a real provider for actual extraction"
    }, indent=2),

    "json": json.dumps({
        "result": "mock_structured_output",
        "score": 85,
        "reasoning": "This is a mock JSON response. Connect a real provider for actual structured output.",
        "passed": True
    }, indent=2),

    "explain": """Here's a clear explanation:

**Core concept:** The subject involves a fundamental principle that applies broadly across related domains.

**Simple analogy:** Think of it like a library — you can request any book (resource), the librarian finds it (server processes the request), and hands it back to you (response). The librarian doesn't remember your previous visits (stateless).

**Technical detail:** The underlying mechanism relies on well-established protocols that ensure consistency and interoperability between systems.

**Common mistakes:**
1. Assuming the system has memory between separate requests
2. Overcomplicating the design when simple patterns suffice
3. Ignoring error handling for edge cases

[Mock response — connect a real provider for tailored explanations]""",

    "resume": json.dumps({
        "match_score": 72,
        "matched_skills": [
            {"skill": "Python", "evidence": "Listed in technical skills section"},
            {"skill": "REST APIs", "evidence": "Mentioned in project descriptions"}
        ],
        "missing_skills": ["Docker", "Kubernetes"],
        "recommendation": "Strong candidate for the technical skills. Consider upskilling in container technologies.",
        "note": "Mock analysis — connect a real provider for actual resume evaluation"
    }, indent=2),
}

_DEFAULT_RESPONSE = """I understand your request. Here is a thoughtful response based on the context provided.

The topic you've asked about is interesting and has several important dimensions worth exploring:

1. **Foundation**: The core principle here is well-established and widely applied in practice.
2. **Application**: Real-world implementations vary based on specific requirements and constraints.
3. **Considerations**: Important factors include performance, maintainability, and scalability.

For more specific and accurate information, please connect a real LLM provider (OpenAI, Anthropic, Gemini, or Mistral) by adding the API key to your .env file.

[Mock response — PromptLab Mock Provider v0.1.0]"""


def _mock_response_for_prompt(system_prompt: str, user_prompt: str) -> str:
    """
    Return a contextually relevant canned response by checking keywords.
    Falls back to the default response.
    """
    combined = (system_prompt + " " + user_prompt).lower()
    for keyword, response in _KEYWORD_RESPONSES.items():
        if keyword in combined:
            return response
    return _DEFAULT_RESPONSE


class MockProvider(BaseLLMProvider):
    """
    Deterministic mock LLM provider.

    - No API key required
    - Always succeeds
    - Returns predictable responses based on prompt keywords
    - Simulates 200–800ms latency (configurable)
    - Reports realistic token counts
    """

    provider_id = "mock"
    display_name = "Mock Provider"

    def __init__(self, simulated_latency_ms: int = 300):
        """
        Args:
            simulated_latency_ms: How long to sleep to simulate network/inference time.
                                  Set to 0 in unit tests for speed.
        """
        self._latency_ms = simulated_latency_ms

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Return a deterministic mock response."""
        start = time.perf_counter()

        if self._latency_ms > 0:
            await asyncio.sleep(self._latency_ms / 1000)

        model = request.model or "mock-echo"
        content = _mock_response_for_prompt(request.system_prompt, request.user_prompt)

        input_tokens = self._estimate_tokens(request.system_prompt + request.user_prompt)
        output_tokens = self._estimate_tokens(content)

        latency = self._elapsed_ms(start)

        logger.info(
            "mock_generate",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency,
        )

        return LLMResponse(
            content=content,
            provider=self.provider_id,
            model=model,
            temperature=request.temperature,
            latency_ms=latency,
            usage=TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            ),
        )

    async def generate_structured(self, request: LLMRequest, schema=None, schema_dict=None) -> LLMResponse:
        """Return valid JSON for structured output tests."""
        start = time.perf_counter()

        if self._latency_ms > 0:
            await asyncio.sleep(self._latency_ms / 1000)

        # Build a JSON response that looks like a real structured output
        combined = (request.system_prompt + " " + request.user_prompt).lower()

        if "resume" in combined or "job" in combined:
            content = _KEYWORD_RESPONSES["resume"]
        elif "classify" in combined or "sentiment" in combined:
            content = json.dumps({
                "classification": "positive",
                "confidence": 0.89,
                "reason": "Mock structured classification result"
            })
        elif "extract" in combined:
            content = _KEYWORD_RESPONSES["extract"]
        else:
            content = json.dumps({
                "result": "mock_structured_output",
                "score": 85,
                "reasoning": "Mock structured response. Connect a real provider for actual output.",
                "passed": True
            })

        input_tokens = self._estimate_tokens(request.system_prompt + request.user_prompt)
        output_tokens = self._estimate_tokens(content)
        latency = self._elapsed_ms(start)

        parsed, json_valid, repair_attempted, original = self._parse_json(content)

        return LLMResponse(
            content=content,
            provider=self.provider_id,
            model=request.model or "mock-structured",
            temperature=request.temperature,
            latency_ms=latency,
            usage=TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            ),
            parsed=parsed,
            json_valid=json_valid,
            json_repair_attempted=repair_attempted,
        )

    def count_tokens(self, text: str) -> int:
        """Use the 4-chars-per-token heuristic."""
        return self._estimate_tokens(text)

    async def health_check(self) -> bool:
        """Mock is always healthy."""
        return True
