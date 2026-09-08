"""
Providers endpoint.

GET /api/providers
  Returns the list of all supported LLM providers and whether each one
  is currently configured (i.e., has a valid API key in the environment).

  The frontend uses this to show/hide provider options and display
  "Provider not configured" where appropriate.

  SECURITY: API keys are NEVER returned — only a boolean configured flag.
"""

from typing import Any, Dict, List

from fastapi import APIRouter

from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# Static metadata about each supported provider
_PROVIDER_METADATA: List[Dict[str, Any]] = [
    {
        "id": "mock",
        "name": "Mock Provider",
        "description": "Local deterministic mock. No API key required. Used for development and testing.",
        "models": ["mock-echo", "mock-structured"],
        "default_model": "mock-echo",
        "supports_structured_output": True,
        "supports_token_counting": True,
    },
    {
        "id": "openai",
        "name": "OpenAI",
        "description": "GPT-4o, GPT-4o-mini and other OpenAI models.",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "default_model": settings.openai_default_model,
        "supports_structured_output": True,
        "supports_token_counting": True,
    },
    {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "description": "Claude 3 Haiku, Sonnet and Opus models.",
        "models": [
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
        ],
        "default_model": settings.anthropic_default_model,
        "supports_structured_output": True,
        "supports_token_counting": True,
    },
    {
        "id": "gemini",
        "name": "Google Gemini",
        "description": "Gemini 1.5 Flash and Pro models.",
        "models": ["gemini-1.5-flash", "gemini-1.5-pro"],
        "default_model": settings.gemini_default_model,
        "supports_structured_output": True,
        "supports_token_counting": False,
    },
    {
        "id": "mistral",
        "name": "Mistral AI",
        "description": "Mistral Small, Medium and Large models.",
        "models": ["mistral-small-latest", "mistral-medium-latest", "mistral-large-latest"],
        "default_model": settings.mistral_default_model,
        "supports_structured_output": True,
        "supports_token_counting": True,
    },
]


@router.get(
    "/providers",
    summary="List LLM providers",
    description=(
        "Returns all supported LLM providers and whether each is currently "
        "configured via environment variables. "
        "API keys are NEVER included in the response."
    ),
    tags=["Providers"],
)
async def list_providers() -> Dict[str, Any]:
    """
    Return provider list with configuration status.

    configured=true  → API key is set, provider is ready to use.
    configured=false → API key is missing, provider shows as unavailable.
    """
    providers = []
    for meta in _PROVIDER_METADATA:
        provider_id = meta["id"]
        configured = settings.provider_is_configured(provider_id)
        providers.append(
            {
                **meta,
                "configured": configured,
                "status": "available" if configured else "not_configured",
            }
        )

    default = settings.default_provider
    logger.info("providers_listed", count=len(providers), default=default)

    return {
        "providers": providers,
        "default_provider": default,
        "total": len(providers),
    }
