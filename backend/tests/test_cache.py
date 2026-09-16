from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from redis.exceptions import RedisError

from app.cache import invalidate_availability_cache


@pytest.mark.asyncio
async def test_invalidate_availability_cache_single_day():
    with patch(
        "app.cache.redis_client.delete",
        new_callable=AsyncMock,
    ) as delete_mock:
        starts_at = datetime(
            2026,
            9,
            20,
            10,
            0,
            tzinfo=UTC,
        )
        ends_at = datetime(
            2026,
            9,
            20,
            13,
            0,
            tzinfo=UTC,
        )

        await invalidate_availability_cache(
            service_id=1,
            starts_at=starts_at,
            ends_at=ends_at,
        )

        delete_mock.assert_awaited_once_with("availability:1:2026-09-20")


@pytest.mark.asyncio
async def test_invalidate_availability_cache_multiple_days():
    with patch(
        "app.cache.redis_client.delete",
        new_callable=AsyncMock,
    ) as delete_mock:
        starts_at = datetime(
            2026,
            9,
            20,
            20,
            0,
            tzinfo=UTC,
        )
        ends_at = datetime(
            2026,
            9,
            22,
            2,
            0,
            tzinfo=UTC,
        )

        await invalidate_availability_cache(
            service_id=2,
            starts_at=starts_at,
            ends_at=ends_at,
        )

        assert delete_mock.await_count == 3

        delete_mock.assert_any_await("availability:2:2026-09-20")
        delete_mock.assert_any_await("availability:2:2026-09-21")
        delete_mock.assert_any_await("availability:2:2026-09-22")


@pytest.mark.asyncio
async def test_cache_invalidation_survives_redis_failure():
    with patch(
        "app.cache.redis_client.delete",
        new_callable=AsyncMock,
        side_effect=RedisError("Redis unavailable"),
    ):
        starts_at = datetime(
            2026,
            9,
            20,
            10,
            0,
            tzinfo=UTC,
        )

        ends_at = datetime(
            2026,
            9,
            20,
            13,
            0,
            tzinfo=UTC,
        )

        await invalidate_availability_cache(
            service_id=1,
            starts_at=starts_at,
            ends_at=ends_at,
        )


@pytest.mark.asyncio
async def test_cache_invalidation_uses_kyiv_date():
    with patch(
        "app.cache.redis_client.delete",
        new_callable=AsyncMock,
    ) as delete_mock:
        starts_at = datetime(
            2026,
            9,
            20,
            22,
            30,
            tzinfo=UTC,
        )

        ends_at = datetime(
            2026,
            9,
            20,
            23,
            30,
            tzinfo=UTC,
        )

        await invalidate_availability_cache(
            service_id=7,
            starts_at=starts_at,
            ends_at=ends_at,
        )

        delete_mock.assert_awaited_once_with("availability:7:2026-09-21")
