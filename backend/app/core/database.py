"""
Database engine and session management.

Uses SQLAlchemy with an async engine.

Development default: SQLite (zero configuration).
Production: set DATABASE_URL=postgresql+asyncpg://... in .env

The repository/service layer never imports the engine directly — they use the
`get_db` dependency so the database backend can be swapped without changing
business logic.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


def _build_async_url(url: str) -> str:
    """
    Convert a sync DATABASE_URL to its async equivalent.

    SQLite  : sqlite:///  → sqlite+aiosqlite:///
    Postgres: postgresql:// → postgresql+asyncpg://
    """
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


_async_url = _build_async_url(settings.database_url)

# SQLite needs check_same_thread=False; other drivers ignore it
_connect_args = {"check_same_thread": False} if "sqlite" in _async_url else {}

engine = create_async_engine(
    _async_url,
    echo=settings.is_development,   # log SQL in dev, silent in prod
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that yields a database session.

    Usage in a route:
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """
    Create all tables on startup (development convenience).
    In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
