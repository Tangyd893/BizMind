import asyncio
from typing import Any

import httpx
import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings


async def check_postgres(session: AsyncSession) -> str:
    try:
        await session.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "error"


async def check_redis(settings: Settings) -> str:
    try:
        client = aioredis.from_url(settings.redis_url)
        try:
            pong = await client.ping()
            return "ok" if pong else "error"
        finally:
            await client.aclose()
    except Exception:
        return "error"


async def check_qdrant(settings: Settings) -> str:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.qdrant_url.rstrip('/')}/readyz")
            return "ok" if response.status_code == 200 else "error"
    except Exception:
        return "error"


async def gather_health(session: AsyncSession, settings: Settings) -> dict[str, Any]:
    pg_status, redis_status, qdrant_status = await asyncio.gather(
        check_postgres(session),
        check_redis(settings),
        check_qdrant(settings),
    )
    checks = {
        "postgres": pg_status,
        "redis": redis_status,
        "qdrant": qdrant_status,
    }
    all_ok = all(value == "ok" for value in checks.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "version": "0.1.0",
        "checks": checks,
    }
