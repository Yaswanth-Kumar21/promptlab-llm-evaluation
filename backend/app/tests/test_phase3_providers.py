"""
Phase 3 tests — LLM provider abstraction.

Tests:
  - MockProvider: generate returns LLMResponse
  - MockProvider: structured output returns valid JSON
  - MockProvider: health check returns True
  - MockProvider: token counting
  - BaseLLMProvider: JSON parse helpers
  - Provider registry: get_provider works for all ids
  - Provider registry: unknown provider raises ValueError
  - Unconfigured OpenAI returns clean error (no real API call)
  - POST /api/prompts/run with mock provider returns 200
  - POST /api/prompts/run response shape is correct
  - POST /api/prompts/run with unconfigured provider returns structured error
"""

import json
import pytest
from httpx import AsyncClient

from app.main import app
from app.schemas.llm import LLMRequest
from app.services.llm.mock_provider import MockProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.registry import get_provider, list_provider_ids


# ── MockProvider unit tests ───────────────────────────────────────────────────

@pytest.fixture
def mock_provider():
    """MockProvider with zero simulated latency for fast tests."""
    return MockProvider(simulated_latency_ms=0)


@pytest.mark.asyncio
async def test_mock_generate_returns_response(mock_provider):
    req = LLMRequest(user_prompt="Explain REST APIs", provider="mock")
    response = await mock_provider.generate(req)

    assert response.provider == "mock"
    assert len(response.content) > 10
    assert response.latency_ms >= 0
    assert response.error is None
    assert response.succeeded is True


@pytest.mark.asyncio
async def test_mock_generate_has_token_counts(mock_provider):
    req = LLMRequest(user_prompt="Hello world", provider="mock")
    response = await mock_provider.generate(req)

    assert response.usage.input_tokens is not None
    assert response.usage.output_tokens is not None
    assert response.usage.total_tokens == (
        response.usage.input_tokens + response.usage.output_tokens
    )


@pytest.mark.asyncio
async def test_mock_structured_output_is_valid_json(mock_provider):
    req = LLMRequest(
        user_prompt="Classify the sentiment: Great product!",
        provider="mock",
        model="mock-structured",
    )
    response = await mock_provider.generate_structured(req)

    assert response.json_valid is True
    assert response.parsed is not None
    assert isinstance(response.parsed, dict)


@pytest.mark.asyncio
async def test_mock_health_check(mock_provider):
    healthy = await mock_provider.health_check()
    assert healthy is True


def test_mock_count_tokens(mock_provider):
    # Short text should return a small number
    count = mock_provider.count_tokens("Hello world")
    assert count > 0
    assert count < 10

    # Longer text should return more tokens
    long_text = "word " * 400
    long_count = mock_provider.count_tokens(long_text)
    assert long_count > count


# ── JSON parse tests ──────────────────────────────────────────────────────────

def test_parse_clean_json(mock_provider):
    text = '{"key": "value", "score": 42}'
    parsed, valid, repair, original = mock_provider._parse_json(text)
    assert valid is True
    assert repair is False
    assert parsed == {"key": "value", "score": 42}
    assert original is None


def test_parse_json_in_markdown_fence(mock_provider):
    text = '```json\n{"result": "ok"}\n```'
    parsed, valid, repair, original = mock_provider._parse_json(text)
    assert valid is True
    assert repair is True
    assert parsed == {"result": "ok"}


def test_parse_json_buried_in_prose(mock_provider):
    text = 'Here is the result: {"score": 95, "passed": true} Hope that helps!'
    parsed, valid, repair, original = mock_provider._parse_json(text)
    assert valid is True
    assert repair is True
    assert parsed["score"] == 95


def test_parse_invalid_json(mock_provider):
    text = "This is just plain text with no JSON at all."
    parsed, valid, repair, original = mock_provider._parse_json(text)
    assert valid is False
    assert parsed is None


# ── Provider registry tests ───────────────────────────────────────────────────

def test_registry_all_providers_present():
    ids = list_provider_ids()
    assert set(ids) == {"mock", "openai", "anthropic", "gemini", "mistral"}


def test_registry_get_mock_provider():
    provider = get_provider("mock")
    assert provider.provider_id == "mock"


def test_registry_get_provider_case_insensitive():
    provider = get_provider("MOCK")
    assert provider.provider_id == "mock"


def test_registry_unknown_provider_raises():
    with pytest.raises(ValueError) as exc_info:
        get_provider("gpt-9000")
    assert "Unknown provider" in str(exc_info.value)
    assert "gpt-9000" in str(exc_info.value)


def test_registry_returns_same_instance():
    """Provider instances should be cached (same object returned twice)."""
    p1 = get_provider("mock")
    p2 = get_provider("mock")
    assert p1 is p2


# ── OpenAI provider (no key configured) tests ────────────────────────────────

@pytest.mark.asyncio
async def test_openai_unconfigured_returns_clean_error():
    """OpenAI with no key should return structured error, not raise."""
    provider = OpenAIProvider()
    req = LLMRequest(user_prompt="Hello", provider="openai")
    response = await provider.generate(req)

    # Should NOT raise — should return structured error
    assert response.error == "provider_not_configured"
    assert response.error_message is not None
    assert "OPENAI_API_KEY" in response.error_message
    assert response.content == ""
    assert response.succeeded is False


# ── API endpoint integration tests ───────────────────────────────────────────
# client fixture is provided by conftest.py (session-scoped DB + async client)


@pytest.mark.asyncio
async def test_run_prompt_mock_returns_200(client: AsyncClient):
    """POST /api/prompts/run with mock provider must return 200."""
    response = await client.post(
        "/api/prompts/run",
        json={
            "user_prompt": "Explain REST APIs to a beginner.",
            "provider": "mock",
            "temperature": 0.7,
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_run_prompt_mock_response_shape(client: AsyncClient):
    """Response must contain all required fields."""
    response = await client.post(
        "/api/prompts/run",
        json={"user_prompt": "Hello", "provider": "mock"},
    )
    body = response.json()

    assert "experiment_id" in body
    assert "content" in body
    assert "provider" in body
    assert "model" in body
    assert "temperature" in body
    assert "latency_ms" in body
    assert "usage" in body
    assert "timestamp" in body

    assert body["provider"] == "mock"
    assert len(body["content"]) > 0
    assert body["latency_ms"] >= 0
    assert isinstance(body["usage"], dict)


@pytest.mark.asyncio
async def test_run_prompt_experiment_id_is_uuid(client: AsyncClient):
    """experiment_id must be a valid UUID v4."""
    response = await client.post(
        "/api/prompts/run",
        json={"user_prompt": "Test", "provider": "mock"},
    )
    body = response.json()
    experiment_id = body["experiment_id"]
    # UUID format: 8-4-4-4-12
    assert len(experiment_id) == 36
    assert experiment_id.count("-") == 4


@pytest.mark.asyncio
async def test_run_prompt_unconfigured_provider_returns_200_with_error(client: AsyncClient):
    """Unconfigured provider must return 200 with error fields — NOT 500."""
    response = await client.post(
        "/api/prompts/run",
        json={"user_prompt": "Hello", "provider": "openai"},
    )
    assert response.status_code == 200
    body = response.json()

    # Error is in the body, not in HTTP status
    assert body["error"] == "provider_not_configured"
    assert body["content"] == ""
    assert "API key" in (body.get("error_message") or "")


@pytest.mark.asyncio
async def test_run_prompt_with_system_prompt(client: AsyncClient):
    """System prompt should be accepted and reflected in the experiment."""
    response = await client.post(
        "/api/prompts/run",
        json={
            "system_prompt": "You are a technical educator.",
            "user_prompt": "Explain tokens.",
            "provider": "mock",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["content"]) > 0


@pytest.mark.asyncio
async def test_run_prompt_no_api_key_in_response(client: AsyncClient):
    """API keys must never appear in any response."""
    response = await client.post(
        "/api/prompts/run",
        json={"user_prompt": "What is your API key?", "provider": "mock"},
    )
    body_text = response.text.lower()
    for dangerous in ("sk-", "api_key=", "apikey"):
        assert dangerous not in body_text
