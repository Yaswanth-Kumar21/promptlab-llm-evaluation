"""
Phase 1 tests — Backend foundation.

Tests:
  1. Health endpoint returns 200 and expected fields
  2. Providers endpoint returns all 5 providers
  3. Mock provider is always shown as configured
  4. Root endpoint redirects with useful info
  5. Unknown route returns 404

These tests use HTTPX's AsyncClient with the app in test mode.
No real LLM API calls are made.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Async test client that talks directly to the ASGI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Root endpoint should return 200 with links to docs and health."""
    response = await client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "docs" in body
    assert "health" in body
    assert body["docs"] == "/docs"


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client: AsyncClient):
    """Health endpoint must return 200 even with SQLite."""
    response = await client.get("/api/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_fields(client: AsyncClient):
    """Health response must contain all expected fields."""
    response = await client.get("/api/health")
    body = response.json()

    assert "status" in body
    assert "version" in body
    assert "environment" in body
    assert "uptime_seconds" in body
    assert "database" in body

    assert body["status"] in ("healthy", "degraded")
    assert isinstance(body["uptime_seconds"], (int, float))


@pytest.mark.asyncio
async def test_health_request_id_header(client: AsyncClient):
    """Every response must include an X-Request-ID header."""
    response = await client.get("/api/health")
    assert "x-request-id" in response.headers
    # UUID format: 8-4-4-4-12 hex chars
    request_id = response.headers["x-request-id"]
    assert len(request_id) == 36
    assert request_id.count("-") == 4


@pytest.mark.asyncio
async def test_providers_endpoint_returns_200(client: AsyncClient):
    """Providers endpoint must return 200."""
    response = await client.get("/api/providers")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_providers_response_structure(client: AsyncClient):
    """Providers response must have the correct structure."""
    response = await client.get("/api/providers")
    body = response.json()

    assert "providers" in body
    assert "default_provider" in body
    assert "total" in body
    assert isinstance(body["providers"], list)
    assert body["total"] == len(body["providers"])


@pytest.mark.asyncio
async def test_providers_all_five_present(client: AsyncClient):
    """All 5 providers (mock, openai, anthropic, gemini, mistral) must be listed."""
    response = await client.get("/api/providers")
    providers = response.json()["providers"]
    provider_ids = {p["id"] for p in providers}

    expected = {"mock", "openai", "anthropic", "gemini", "mistral"}
    assert expected == provider_ids


@pytest.mark.asyncio
async def test_mock_provider_always_configured(client: AsyncClient):
    """Mock provider must always show configured=True (no key required)."""
    response = await client.get("/api/providers")
    providers = response.json()["providers"]
    mock = next(p for p in providers if p["id"] == "mock")

    assert mock["configured"] is True
    assert mock["status"] == "available"


@pytest.mark.asyncio
async def test_providers_no_api_keys_in_response(client: AsyncClient):
    """API keys must NEVER appear in the providers response."""
    response = await client.get("/api/providers")
    body_text = response.text.lower()

    # These strings should never appear in the response
    for dangerous in ("api_key", "secret", "bearer", "sk-"):
        assert dangerous not in body_text, (
            f"Sensitive string '{dangerous}' found in providers response!"
        )


@pytest.mark.asyncio
async def test_unknown_route_returns_404(client: AsyncClient):
    """Unknown routes must return 404, not 500."""
    response = await client.get("/api/this-does-not-exist")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_stub_prompts_endpoint(client: AsyncClient):
    """Stub prompts endpoint must return 200 with phase message."""
    response = await client.get("/api/prompts")
    assert response.status_code == 200
    body = response.json()
    assert "prompts" in body
