"""Pytest configuration with async SQLAlchemy test fixtures.

Database fixtures are opt-in — import `session` or `client` from this module
to get an isolated test database session. Pure-sync tests (e.g., chunker)
don't trigger any DB setup.
"""

from collections.abc import AsyncGenerator

import pytest_asyncio
from app.config import get_settings
from app.dependencies import get_db
from app.main import app
from app.models import Base
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

settings = get_settings()

_db_engine = None
_db_session_factory = None


def _get_test_engine():
    global _db_engine
    if _db_engine is None:
        _db_engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
        )
    return _db_engine


def _get_session_factory():
    global _db_session_factory
    if _db_session_factory is None:
        _db_session_factory = async_sessionmaker(
            _get_test_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _db_session_factory


@pytest_asyncio.fixture
async def setup_database() -> AsyncGenerator[None, None]:
    """Create all tables, then drop after yield. Use this fixture when you need DB."""
    engine = _get_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Provide a test DB session that rolls back after each test."""
    factory = _get_session_factory()
    async with factory() as s, s.begin() as tx:
        await tx.start()
        yield s
        await tx.rollback()


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client with DB dependency overridden to test session."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
