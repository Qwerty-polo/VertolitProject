from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.cache import invalidate_availability_cache


@pytest.mark.asyncio
async def test_invalidate_availability_cache_single_day():
    with patch(
        "app.cache.redis_client.delete",
        new_callable=AsyncMock,
    ) as delete_mock:
        starts_at = datetime(
            2026, 9, 20, 10, 0,
            tzinfo=timezone.utc,
        )
        ends_at = datetime(
            2026, 9, 20, 13, 0,
            tzinfo=timezone.utc,
        )

        await invalidate_availability_cache(
            service_id=1,
            starts_at=starts_at,
            ends_at=ends_at,
        )

        delete_mock.assert_awaited_once_with(
            "availability:1:2026-09-20"
        )


@pytest.mark.asyncio
async def test_invalidate_availability_cache_multiple_days():
    with patch(
        "app.cache.redis_client.delete",
        new_callable=AsyncMock,
    ) as delete_mock:
        starts_at = datetime(
            2026, 9, 20, 20, 0,
            tzinfo=timezone.utc,
        )
        ends_at = datetime(
            2026, 9, 22, 2, 0,
            tzinfo=timezone.utc,
        )

        await invalidate_availability_cache(
            service_id=2,
            starts_at=starts_at,
            ends_at=ends_at,
        )

        assert delete_mock.await_count == 3

        delete_mock.assert_any_await(
            "availability:2:2026-09-20"
        )
        delete_mock.assert_any_await(
            "availability:2:2026-09-21"
        )
        delete_mock.assert_any_await(
            "availability:2:2026-09-22"
        )