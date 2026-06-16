"""Pytest configuration with async SQLAlchemy test fixtures.

Uses SQLite (aiosqlite) for integration tests — no external DB required.
Set DATABASE_URL to PostgreSQL (e.g. Docker on localhost:5433) for PG-backed runs.

Provides `app_client` with mocked DB for tests that mock dependencies (health).
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest_asyncio
from app.dependencies import get_db
from app.main import app
from app.models import Base
from httpx import ASGITransport, AsyncClient
from sqlalchemy import String, event, text
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.types import JSON, Uuid

DEFAULT_SQLITE_URL = "sqlite+aiosqlite:///./test.db"
TEST_DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_SQLITE_URL)
_USE_SQLITE = TEST_DATABASE_URL.startswith("sqlite")

_engine = None
_session_factory = None
_tables_ready = False
_types_patched = False


def _patch_types_for_sqlite():
    """Replace PostgreSQL-specific column types so DDL works on SQLite.

    We walk every table in Base.metadata and swap PG types for SQLite-compatible
    ones.  This only affects DDL — query-time bind/result processing is not
    touched because we don't override any compilation rules.
    """
    global _types_patched
    if _types_patched:
        return
    _types_patched = True

    from sqlalchemy import Column

    for table in Base.metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, PGUUID):
                col.type = Uuid()
            elif isinstance(col.type, JSONB):
                col.type = JSON()
            elif isinstance(col.type, PGEnum):
                col.type = String(255)


def _get_engine():
    global _engine
    if _engine is None:
        if _USE_SQLITE:
            _patch_types_for_sqlite()
        _engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            pool_pre_ping=not _USE_SQLITE,
        )
    return _engine


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


async def _ensure_schema(engine) -> None:
    global _tables_ready
    if _tables_ready:
        return
    async with engine.begin() as conn:
        if _USE_SQLITE:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        if not _USE_SQLITE:
            await conn.execute(
                text(
                    "INSERT INTO documents_version_counter (id, current_version) "
                    "VALUES (1, 0) ON CONFLICT (id) DO NOTHING"
                )
            )
    _tables_ready = True


@pytest_asyncio.fixture
async def db_engine():
    """Function-scoped engine; schema is created once per test process."""
    engine = _get_engine()
    await _ensure_schema(engine)
    yield engine


@pytest_asyncio.fixture
async def session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Per-test session — deletes all rows after each test.

    App code calls session.commit() inside the endpoint, so we can't rely on
    transaction rollback.  Instead we DELETE all rows from every table after
    the test yields.
    """
    factory = _get_session_factory()
    async with factory() as s:
        yield s
        await s.execute(text("DELETE FROM messages"))
        await s.execute(text("DELETE FROM threads"))
        await s.execute(text("DELETE FROM documents"))
        await s.execute(text("DELETE FROM eval_runs"))
        await s.execute(text("DELETE FROM users"))
        await s.execute(text("DELETE FROM tenants"))
        await s.execute(text("DELETE FROM documents_version_counter"))
        await s.commit()


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client with real DB session override."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def app_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client with mocked DB — for health / no-DB tests."""

    async def override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
