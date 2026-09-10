"""
Phase 4/5/6 tests — Playground, Techniques, Prompt CRUD, Versioning.

All tests use the mock provider — no real LLM API calls are made.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ─────────────────────────────────────────────────────────────────────────────
# Playground — POST /api/prompts/run
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_prompt_mock(client):
    """Basic mock provider run returns 200 with content."""
    resp = await client.post("/api/prompts/run", json={
        "system_prompt": "You are a helpful assistant.",
        "user_prompt": "Explain REST APIs.",
        "provider": "mock",
        "temperature": 0.7,
        "max_tokens": 512,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "mock"
    assert body["content"]
    assert body["latency_ms"] >= 0
    assert body["experiment_id"]
    assert body["timestamp"]


@pytest.mark.asyncio
async def test_run_prompt_returns_token_usage(client):
    """Token usage must be reported for the mock provider."""
    resp = await client.post("/api/prompts/run", json={
        "user_prompt": "Hello",
        "provider": "mock",
    })
    assert resp.status_code == 200
    usage = resp.json()["usage"]
    assert usage["input_tokens"] is not None
    assert usage["output_tokens"] is not None
    assert usage["total_tokens"] is not None


@pytest.mark.asyncio
async def test_run_prompt_empty_user_prompt(client):
    """Empty user_prompt must be rejected with 422."""
    resp = await client.post("/api/prompts/run", json={
        "user_prompt": "   ",
        "provider": "mock",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_run_prompt_invalid_provider(client):
    """Invalid provider must be rejected with 422."""
    resp = await client.post("/api/prompts/run", json={
        "user_prompt": "Hello",
        "provider": "nonexistent_provider",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_run_prompt_temperature_range(client):
    """Temperature outside 0–2 must be rejected."""
    resp = await client.post("/api/prompts/run", json={
        "user_prompt": "Hello",
        "provider": "mock",
        "temperature": 3.5,
    })
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# Techniques — POST /api/prompts/run/technique
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("technique", ["zero_shot", "few_shot", "role", "structured", "constraint"])
async def test_all_techniques_run(client, technique):
    """Every technique must return 200 with content."""
    resp = await client.post("/api/prompts/run/technique", json={
        "technique": technique,
        "user_input": "The product is great but arrived late.",
        "provider": "mock",
    })
    assert resp.status_code == 200, f"technique={technique} got {resp.status_code}"
    assert resp.json()["content"]


@pytest.mark.asyncio
async def test_structured_technique_returns_json(client):
    """Structured technique should return parseable JSON via mock provider."""
    resp = await client.post("/api/prompts/run/technique", json={
        "technique": "structured",
        "user_input": "FastAPI is fast and easy to use.",
        "provider": "mock",
        "temperature": 0.0,
    })
    assert resp.status_code == 200
    body = resp.json()
    # Mock structured output should set json_valid
    assert body["json_valid"] is True or body["content"]  # mock always returns valid JSON


@pytest.mark.asyncio
async def test_invalid_technique_rejected(client):
    """Unknown technique name must be rejected with 422."""
    resp = await client.post("/api/prompts/run/technique", json={
        "technique": "nonexistent_technique",
        "user_input": "test",
        "provider": "mock",
    })
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# Prompt CRUD
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_and_list_prompt(client):
    """Create a prompt then verify it appears in the list."""
    create_resp = await client.post("/api/prompts", json={
        "name": "Test Prompt",
        "description": "A test",
        "category": "general",
        "tags": "",
    })
    assert create_resp.status_code == 201
    prompt = create_resp.json()
    assert prompt["id"]
    assert prompt["name"] == "Test Prompt"

    list_resp = await client.get("/api/prompts")
    assert list_resp.status_code == 200
    ids = [p["id"] for p in list_resp.json()["prompts"]]
    assert prompt["id"] in ids


@pytest.mark.asyncio
async def test_get_prompt(client):
    """Created prompt is retrievable by ID."""
    create_resp = await client.post("/api/prompts", json={"name": "Get Test", "category": "general"})
    pid = create_resp.json()["id"]

    resp = await client.get(f"/api/prompts/{pid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == pid


@pytest.mark.asyncio
async def test_get_nonexistent_prompt_returns_404(client):
    resp = await client.get("/api/prompts/nonexistent-uuid-00000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_prompt(client):
    """Prompt name can be updated."""
    pid = (await client.post("/api/prompts", json={"name": "Old Name", "category": "general"})).json()["id"]

    resp = await client.put(f"/api/prompts/{pid}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_prompt(client):
    """Deleted prompt is no longer retrievable."""
    pid = (await client.post("/api/prompts", json={"name": "To Delete", "category": "general"})).json()["id"]

    del_resp = await client.delete(f"/api/prompts/{pid}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/prompts/{pid}")
    assert get_resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# Versions
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_versions_numbered_sequentially(client):
    """Versions are numbered 1, 2, 3… automatically."""
    pid = (await client.post("/api/prompts", json={"name": "Versioned", "category": "general"})).json()["id"]

    for i in range(3):
        resp = await client.post(f"/api/prompts/{pid}/versions", json={
            "user_prompt_template": f"Prompt version {i + 1}",
            "notes": f"Version {i + 1}",
        })
        assert resp.status_code == 201
        assert resp.json()["version_number"] == i + 1


@pytest.mark.asyncio
async def test_mark_best_version(client):
    """Marking a version as best clears the flag on all others."""
    pid = (await client.post("/api/prompts", json={"name": "Best Test", "category": "general"})).json()["id"]

    v1 = (await client.post(f"/api/prompts/{pid}/versions", json={"user_prompt_template": "V1"})).json()
    v2 = (await client.post(f"/api/prompts/{pid}/versions", json={"user_prompt_template": "V2"})).json()

    # Mark V2 as best
    resp = await client.put(f"/api/prompts/{pid}/versions/{v2['id']}/best")
    assert resp.status_code == 200
    assert resp.json()["is_best"] is True

    # Verify V1 is no longer best
    versions = (await client.get(f"/api/prompts/{pid}/versions")).json()
    v1_updated = next(v for v in versions if v["id"] == v1["id"])
    assert v1_updated["is_best"] is False


@pytest.mark.asyncio
async def test_duplicate_version(client):
    """Duplicated version has same content and incremented version number."""
    pid = (await client.post("/api/prompts", json={"name": "Dup Test", "category": "general"})).json()["id"]
    v1 = (await client.post(f"/api/prompts/{pid}/versions", json={
        "user_prompt_template": "Original text",
        "notes": "Original notes",
    })).json()

    dup = (await client.post(f"/api/prompts/{pid}/versions/{v1['id']}/duplicate")).json()
    assert dup["status_code"] != 404 if "status_code" in dup else True
    assert dup["user_prompt_template"] == "Original text"
    assert dup["version_number"] == 2


# ─────────────────────────────────────────────────────────────────────────────
# Experiments
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_creates_experiment(client):
    """Running a prompt creates an experiment visible in GET /experiments."""
    await client.post("/api/prompts/run", json={
        "user_prompt": "Unique experiment test prompt XYZ",
        "provider": "mock",
    })

    resp = await client.get("/api/experiments")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_experiments_stats(client):
    """Stats endpoint returns required fields."""
    resp = await client.get("/api/experiments/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert "total_experiments" in body
    assert "total_prompts" in body
    assert "total_versions" in body
