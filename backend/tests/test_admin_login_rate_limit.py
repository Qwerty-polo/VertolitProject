from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, Request

from app.security.admin_login_rate_limit import (
    admin_login_rate_limit,
)


def make_request() -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/admin/login",
        "headers": [],
        "query_string": b"",
        "server": ("test", 80),
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
    }

    return Request(scope)


@pytest.mark.asyncio
async def test_admin_login_rate_limit_allows_first_attempt():
    request = make_request()

    with (
        patch(
            "app.security.admin_login_rate_limit.redis_client.incr",
            new_callable=AsyncMock,
            return_value=1,
        ) as incr_mock,
        patch(
            "app.security.admin_login_rate_limit.redis_client.expire",
            new_callable=AsyncMock,
        ) as expire_mock,
    ):
        await admin_login_rate_limit(request)

    incr_mock.assert_awaited_once()
    expire_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_login_rate_limit_blocks_sixth_attempt():
    request = make_request()

    with (
        patch(
            "app.security.admin_login_rate_limit.redis_client.incr",
            new_callable=AsyncMock,
            return_value=6,
        ),
        patch(
            "app.security.admin_login_rate_limit.redis_client.expire",
            new_callable=AsyncMock,
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await admin_login_rate_limit(request)

    assert exc_info.value.status_code == 429

    assert exc_info.value.detail == "Too many admin login attempts"


@pytest.mark.asyncio
async def test_admin_login_rate_limit_does_not_reset_ttl():
    request = make_request()

    with (
        patch(
            "app.security.admin_login_rate_limit.redis_client.incr",
            new_callable=AsyncMock,
            return_value=2,
        ),
        patch(
            "app.security.admin_login_rate_limit.redis_client.expire",
            new_callable=AsyncMock,
        ) as expire_mock,
    ):
        await admin_login_rate_limit(request)

    expire_mock.assert_not_awaited()
