from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, Request

from app.security.booking_rate_limit import booking_rate_limit


def make_request() -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/bookings/",
        "headers": [],
        "query_string": b"",
        "server": ("test", 80),
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
    }

    return Request(scope)


@pytest.mark.asyncio
async def test_booking_rate_limit_allows_first_request():
    request = make_request()

    with (
        patch(
            "app.security.booking_rate_limit.redis_client.incr",
            new_callable=AsyncMock,
            return_value=1,
        ) as incr_mock,
        patch(
            "app.security.booking_rate_limit.redis_client.expire",
            new_callable=AsyncMock,
        ) as expire_mock,
    ):
        await booking_rate_limit(request)

    incr_mock.assert_awaited_once()
    expire_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_booking_rate_limit_blocks_sixth_request():
    request = make_request()

    with (
        patch(
            "app.security.booking_rate_limit.redis_client.incr",
            new_callable=AsyncMock,
            return_value=6,
        ),
        patch(
            "app.security.booking_rate_limit.redis_client.expire",
            new_callable=AsyncMock,
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await booking_rate_limit(request)

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "Too many booking attempts"


@pytest.mark.asyncio
async def test_booking_rate_limit_does_not_reset_ttl_after_first_request():
    request = make_request()

    with (
        patch(
            "app.security.booking_rate_limit.redis_client.incr",
            new_callable=AsyncMock,
            return_value=2,
        ),
        patch(
            "app.security.booking_rate_limit.redis_client.expire",
            new_callable=AsyncMock,
        ) as expire_mock,
    ):
        await booking_rate_limit(request)

    expire_mock.assert_not_awaited()
