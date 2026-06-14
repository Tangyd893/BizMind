from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_healthy_when_dependencies_ok(client: AsyncClient) -> None:
    with (
        patch("app.services.health_service.check_postgres", AsyncMock(return_value="ok")),
        patch("app.services.health_service.check_redis", AsyncMock(return_value="ok")),
        patch("app.services.health_service.check_qdrant", AsyncMock(return_value="ok")),
    ):
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["checks"]["postgres"] == "ok"
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_health_returns_degraded_when_postgres_fails(client: AsyncClient) -> None:
    with (
        patch("app.services.health_service.check_postgres", AsyncMock(return_value="error")),
        patch("app.services.health_service.check_redis", AsyncMock(return_value="ok")),
        patch("app.services.health_service.check_qdrant", AsyncMock(return_value="ok")),
    ):
        response = await client.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
