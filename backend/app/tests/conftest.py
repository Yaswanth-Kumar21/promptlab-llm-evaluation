"""
Shared pytest fixtures.

Design notes:
  - All async fixtures use function scope to avoid event_loop ScopeMismatch
    with pytest-asyncio in auto mode.
  - init_test_db runs before each test that uses the `client` fixture,
    ensuring a clean DB state. It's cheap because SQLite is in-memory-like.
  - The `client` fixture depends on init_test_db so DB is always ready.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import engine, Base
from app.main import app


@pytest.fixture(autouse=True)
async def init_test_db():
    """
    Create all DB tables before each test, drop after.
    Uses function scope to stay compatible with pytest-asyncio auto mode.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """Async HTTP test client wrapping the FastAPI ASGI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
