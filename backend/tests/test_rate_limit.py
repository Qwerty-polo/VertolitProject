from unittest.mock import AsyncMock, patch

import pytest
from fastapi import Request
from starlette.responses import JSONResponse

from app.middleware.rate_limit import rate_limit_middleware


def make_request() -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [],
        "query_string": b"",
        "server": ("test", 80),
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
    }

    return Request(scope)


@pytest.mark.asyncio
async def test_rate_limit_allows_request():
    request = make_request()

    call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))

    with (
        patch(
            "app.middleware.rate_limit.redis_client.incr",
            new_callable=AsyncMock,
            return_value=1,
        ) as incr_mock,
        patch(
            "app.middleware.rate_limit.redis_client.expire",
            new_callable=AsyncMock,
        ) as expire_mock,
    ):
        response = await rate_limit_middleware(
            request,
            call_next,
        )

    assert response.status_code == 200
    call_next.assert_awaited_once()

    incr_mock.assert_awaited_once()
    expire_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_rate_limit_blocks_request_over_limit():
    request = make_request()

    call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))

    with (
        patch(
            "app.middleware.rate_limit.redis_client.incr",
            new_callable=AsyncMock,
            return_value=31,
        ),
        patch(
            "app.middleware.rate_limit.redis_client.expire",
            new_callable=AsyncMock,
        ),
    ):
        response = await rate_limit_middleware(
            request,
            call_next,
        )

    assert response.status_code == 429
    assert b"Too many requests" in response.body

    call_next.assert_not_awaited()


@pytest.mark.asyncio
async def test_rate_limit_sets_ttl_only_for_first_request():
    request = make_request()

    call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))

    with (
        patch(
            "app.middleware.rate_limit.redis_client.incr",
            new_callable=AsyncMock,
            return_value=2,
        ),
        patch(
            "app.middleware.rate_limit.redis_client.expire",
            new_callable=AsyncMock,
        ) as expire_mock,
    ):
        response = await rate_limit_middleware(
            request,
            call_next,
        )

    assert response.status_code == 200
    expire_mock.assert_not_awaited()
