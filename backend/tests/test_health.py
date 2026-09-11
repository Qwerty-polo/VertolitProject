from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_healthcheck_all_services_ok(client):
    with patch(
        "app.api.v1.health.redis_client.ping",
        new_callable=AsyncMock,
        return_value=True,
    ):
        response = await client.get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "ok",
        "redis": "ok",
    }


@pytest.mark.asyncio
async def test_healthcheck_redis_error(client):
    with patch(
        "app.api.v1.health.redis_client.ping",
        new_callable=AsyncMock,
        side_effect=ConnectionError("Redis unavailable"),
    ):
        response = await client.get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "degraded",
        "database": "ok",
        "redis": "error",
    }