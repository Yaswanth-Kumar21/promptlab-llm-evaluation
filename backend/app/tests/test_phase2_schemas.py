"""
Phase 2 tests — Pydantic schemas and error handling.

Tests:
  - RunPromptRequest validation
  - LLMRequest provider validator
  - Temperature bounds
  - Empty prompt rejection
  - Validation error format (422)
  - 404 error format
"""

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.main import app
from app.schemas.llm import LLMRequest, RunPromptRequest


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── Schema unit tests (no HTTP) ───────────────────────────────────────────────

def test_llm_request_valid():
    req = LLMRequest(user_prompt="Hello", provider="mock")
    assert req.provider == "mock"
    assert req.temperature == 0.7


def test_llm_request_provider_normalised():
    """Provider should be lowercased and stripped."""
    req = LLMRequest(user_prompt="Hello", provider="  OpenAI  ")
    assert req.provider == "openai"


def test_llm_request_invalid_provider():
    with pytest.raises(ValidationError) as exc_info:
        LLMRequest(user_prompt="Hello", provider="gpt-9000")
    assert "Unknown provider" in str(exc_info.value)


def test_llm_request_temperature_bounds():
    with pytest.raises(ValidationError):
        LLMRequest(user_prompt="Hello", temperature=3.0)  # > 2.0
    with pytest.raises(ValidationError):
        LLMRequest(user_prompt="Hello", temperature=-0.1)  # < 0.0


def test_llm_request_empty_prompt():
    with pytest.raises(ValidationError):
        LLMRequest(user_prompt="   ")  # only whitespace


def test_run_prompt_request_defaults():
    req = RunPromptRequest(user_prompt="Test")
    assert req.provider == "mock"
    assert req.temperature == 0.7
    assert req.max_tokens == 1024
    assert req.system_prompt == ""


# ── HTTP validation error tests ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_prompt_missing_user_prompt(client: AsyncClient):
    """Missing required field should return 422."""
    response = await client.post("/api/prompts/run", json={"provider": "mock"})
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"
    assert "detail" in body
    assert isinstance(body["detail"], list)


@pytest.mark.asyncio
async def test_run_prompt_invalid_temperature(client: AsyncClient):
    """Temperature out of range should return 422."""
    response = await client.post(
        "/api/prompts/run",
        json={"user_prompt": "Hello", "temperature": 5.0},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"


@pytest.mark.asyncio
async def test_run_prompt_invalid_provider(client: AsyncClient):
    """Unknown provider ID should return 422."""
    response = await client.post(
        "/api/prompts/run",
        json={"user_prompt": "Hello", "provider": "gpt-9000"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_404_returns_json(client: AsyncClient):
    """404 should return JSON with error field, not HTML."""
    response = await client.get("/api/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    assert "message" in body


@pytest.mark.asyncio
async def test_validation_error_has_request_id(client: AsyncClient):
    """422 errors should include a request_id for log correlation."""
    response = await client.post("/api/prompts/run", json={})
    assert response.status_code == 422
    body = response.json()
    assert "request_id" in body
