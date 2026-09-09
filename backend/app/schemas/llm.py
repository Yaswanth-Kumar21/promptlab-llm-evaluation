"""
Pydantic schemas for LLM provider requests and responses.

These are the data contracts between:
  - API route handlers  →  LLM services
  - LLM services        →  provider implementations
  - API responses       →  frontend
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ── Request ───────────────────────────────────────────────────────────────────

class LLMRequest(BaseModel):
    """
    All parameters needed to make one LLM call.

    Used by every provider implementation so the interface is uniform
    regardless of which provider handles it.
    """
    system_prompt: str = Field(
        default="",
        description="System/instruction prompt. Leave empty for no system context.",
        max_length=32_000,
    )
    user_prompt: str = Field(
        ...,
        description="The user message or task.",
        min_length=1,
        max_length=32_000,
    )
    provider: str = Field(
        default="mock",
        description="Provider ID: mock | openai | anthropic | gemini | mistral",
    )
    model: str = Field(
        default="",
        description="Model name. If empty, the provider's default model is used.",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature. 0 = deterministic, 1 = creative.",
    )
    max_tokens: int = Field(
        default=1024,
        ge=1,
        le=16_384,
        description="Maximum tokens to generate.",
    )
    # Optional structured output schema name (used by generate_structured)
    response_schema: Optional[str] = Field(
        default=None,
        description="Name of the Pydantic schema to validate the response against.",
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        allowed = {"mock", "openai", "anthropic", "gemini", "mistral"}
        v = v.lower().strip()
        if v not in allowed:
            raise ValueError(f"Unknown provider '{v}'. Allowed: {', '.join(sorted(allowed))}")
        return v

    @field_validator("user_prompt")
    @classmethod
    def validate_user_prompt(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("user_prompt cannot be empty or only whitespace.")
        return v


# ── Response ──────────────────────────────────────────────────────────────────

class TokenUsage(BaseModel):
    """Token counts from an LLM call. Fields are None when the provider doesn't report them."""
    input_tokens: Optional[int] = Field(None, description="Tokens in the prompt")
    output_tokens: Optional[int] = Field(None, description="Tokens in the response")
    total_tokens: Optional[int] = Field(None, description="input + output")


class LLMResponse(BaseModel):
    """
    Standardised response from every provider.

    All providers return this same shape so the frontend never
    needs provider-specific parsing logic.
    """
    content: str = Field(..., description="The model's text response")
    provider: str
    model: str
    temperature: float
    latency_ms: int = Field(..., description="Wall-clock time for the API call in milliseconds")
    usage: TokenUsage = Field(default_factory=TokenUsage)

    # Structured output fields (populated by generate_structured)
    parsed: Optional[Dict[str, Any]] = Field(
        None,
        description="Parsed JSON object when structured output was requested",
    )
    json_valid: Optional[bool] = Field(
        None,
        description="True if the response was valid JSON matching the schema",
    )
    json_repair_attempted: bool = Field(
        False,
        description="True if the original JSON was invalid and a repair was attempted",
    )
    original_content: Optional[str] = Field(
        None,
        description="Original response before JSON repair (only set when repair was attempted)",
    )

    # Error (set when the call failed but we want to record the attempt)
    error: Optional[str] = Field(None, description="Error type if the call failed")
    error_message: Optional[str] = Field(None, description="Human-readable error detail")

    @property
    def succeeded(self) -> bool:
        return self.error is None


# ── Prompt run request/response (API layer) ───────────────────────────────────

class RunPromptRequest(BaseModel):
    """
    POST /api/prompts/run

    What the frontend sends when the user clicks "Run" in the Playground.
    """
    system_prompt: str = Field(default="", max_length=32_000)
    user_prompt: str = Field(..., min_length=1, max_length=32_000)
    provider: str = Field(default="mock")
    model: str = Field(default="")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=16_384)
    # Optional: link this run to a saved prompt version
    prompt_version_id: Optional[str] = Field(None)
    # Optional: link to a test case in an evaluation dataset
    test_case_id: Optional[str] = Field(None)
    dataset_name: Optional[str] = Field(None)

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        allowed = {"mock", "openai", "anthropic", "gemini", "mistral"}
        v = v.lower().strip()
        if v not in allowed:
            raise ValueError(f"Unknown provider '{v}'. Allowed: {', '.join(sorted(allowed))}")
        return v

    @field_validator("user_prompt")
    @classmethod
    def validate_user_prompt(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("user_prompt cannot be empty or only whitespace.")
        return v


class RunPromptResponse(BaseModel):
    """
    POST /api/prompts/run → response body.

    Combines the LLM result with experiment tracking metadata.
    """
    experiment_id: str
    content: str
    provider: str
    model: str
    temperature: float
    latency_ms: int
    usage: TokenUsage
    json_valid: Optional[bool] = None
    parsed: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: str  # ISO format


# ── Technique demo request ────────────────────────────────────────────────────

class TechniqueRunRequest(BaseModel):
    """
    Used by the Prompt Techniques page to run a specific technique demo.
    """
    technique: str = Field(
        ...,
        description="zero_shot | few_shot | role | structured | constraint",
    )
    user_input: str = Field(..., min_length=1, max_length=8_000)
    provider: str = Field(default="mock")
    model: str = Field(default="")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
