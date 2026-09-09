"""
Provider registry and factory.

Usage:
    from app.services.llm.registry import get_provider, get_all_providers

    provider = get_provider("openai")    # returns OpenAIProvider instance
    provider = get_provider("mock")      # always works, no key needed
    provider = get_provider("unknown")   # raises ValueError with clear message

Design:
  - Providers are instantiated once and cached (singleton per provider)
  - The cache is module-level so it's shared across all requests
  - Adding a new provider requires only: add it to _REGISTRY
"""

from typing import Dict

from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm.base import BaseLLMProvider
from app.services.llm.mock_provider import MockProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.mistral_provider import MistralProvider

logger = get_logger(__name__)

# ── Provider cache ────────────────────────────────────────────────────────────
# Providers are instantiated lazily on first use and then reused.
_provider_cache: Dict[str, BaseLLMProvider] = {}

# ── Registry ──────────────────────────────────────────────────────────────────
# Maps provider_id → provider class.
# To add a new provider: add one line here.
_REGISTRY: Dict[str, type] = {
    "mock":      MockProvider,
    "openai":    OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini":    GeminiProvider,
    "mistral":   MistralProvider,
}


def get_provider(provider_id: str) -> BaseLLMProvider:
    """
    Return a provider instance for the given provider_id.

    Instances are cached — each provider is only instantiated once.

    Args:
        provider_id: One of "mock", "openai", "anthropic", "gemini", "mistral"

    Raises:
        ValueError: If provider_id is not in the registry.
    """
    provider_id = provider_id.lower().strip()

    if provider_id not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError(
            f"Unknown provider '{provider_id}'. Available: {available}"
        )

    if provider_id not in _provider_cache:
        provider_class = _REGISTRY[provider_id]
        _provider_cache[provider_id] = provider_class()
        logger.info("provider_instantiated", provider=provider_id)

    return _provider_cache[provider_id]


def get_default_provider() -> BaseLLMProvider:
    """Return the default provider from settings, falling back to mock."""
    provider_id = settings.default_provider.lower()
    if provider_id not in _REGISTRY:
        logger.warning(
            "default_provider_invalid",
            configured=provider_id,
            fallback="mock",
        )
        provider_id = "mock"
    return get_provider(provider_id)


def get_all_providers() -> Dict[str, BaseLLMProvider]:
    """Return all registered providers (instantiating any that aren't cached yet)."""
    return {pid: get_provider(pid) for pid in _REGISTRY}


def list_provider_ids() -> list[str]:
    """Return sorted list of all registered provider IDs."""
    return sorted(_REGISTRY.keys())
