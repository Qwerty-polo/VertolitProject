import json
from unittest.mock import (
    AsyncMock,
    patch,
)

import pytest
from fastapi import Request, Response
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.health import healthcheck
from app.middleware.rate_limit import (
    rate_limit_middleware,
)
from app.security.booking_rate_limit import (
    booking_rate_limit,
)


def make_request(
    path: str = "/api/v1/services/",
) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "raw_path": path.encode(),
        "headers": [],
        "query_string": b"",
        "server": ("test", 80),
        "client": (
            "127.0.0.1",
            12345,
        ),
        "scheme": "http",
    }

    return Request(scope)


@pytest.mark.asyncio
async def test_health_bypasses_global_rate_limit():
    request = make_request("/api/v1/health/")

    call_next = AsyncMock(return_value=Response(status_code=200))

    with patch(
        "app.middleware.rate_limit.redis_client.incr",
        new_callable=AsyncMock,
    ) as incr_mock:
        response = await rate_limit_middleware(
            request,
            call_next,
        )

    assert response.status_code == 200

    incr_mock.assert_not_awaited()
    call_next.assert_awaited_once()


@pytest.mark.asyncio
async def test_global_rate_limit_fails_open_when_redis_is_down():
    request = make_request()

    call_next = AsyncMock(return_value=Response(status_code=200))

    with patch(
        "app.middleware.rate_limit.redis_client.incr",
        new_callable=AsyncMock,
        side_effect=RedisError("Redis unavailable"),
    ):
        response = await rate_limit_middleware(
            request,
            call_next,
        )

    assert response.status_code == 200

    call_next.assert_awaited_once()


@pytest.mark.asyncio
async def test_booking_rate_limit_fails_open_when_redis_is_down():
    request = make_request("/api/v1/bookings/")

    with patch(
        "app.security.booking_rate_limit.redis_client.incr",
        new_callable=AsyncMock,
        side_effect=RedisError("Redis unavailable"),
    ):
        await booking_rate_limit(request)


class HealthyDatabase:
    async def execute(
        self,
        statement,
    ):
        return None


class BrokenDatabase:
    async def execute(
        self,
        statement,
    ):
        raise SQLAlchemyError("Database unavailable")


@pytest.mark.asyncio
async def test_health_is_degraded_when_redis_is_down():
    database = HealthyDatabase()

    with patch(
        "app.api.v1.health.redis_client.ping",
        new_callable=AsyncMock,
        side_effect=RedisError("Redis unavailable"),
    ):
        response = await healthcheck(database)

    assert response.status_code == 200

    data = json.loads(response.body)

    assert data == {
        "status": "degraded",
        "database": "ok",
        "redis": "error",
    }


@pytest.mark.asyncio
async def test_health_is_unhealthy_when_database_is_down():
    database = BrokenDatabase()

    with patch(
        "app.api.v1.health.redis_client.ping",
        new_callable=AsyncMock,
        return_value=True,
    ):
        response = await healthcheck(database)

    assert response.status_code == 503

    data = json.loads(response.body)

    assert data == {
        "status": "unhealthy",
        "database": "error",
        "redis": "ok",
    }
