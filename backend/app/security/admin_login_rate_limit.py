import time

from fastapi import HTTPException, Request, status

from app.config import settings
from app.redis import redis_client


async def admin_login_rate_limit(
    request: Request,
) -> None:
    client_ip = (
        request.client.host
        if request.client
        else "unknown"
    )

    window_seconds = (
        settings.admin_login_rate_limit_window_seconds
    )

    current_window = int(
        time.time() // window_seconds
    )

    redis_key = (
        f"admin_login_rate_limit:"
        f"{client_ip}:"
        f"{current_window}"
    )

    request_count = await redis_client.incr(
        redis_key
    )

    if request_count == 1:
        await redis_client.expire(
            redis_key,
            window_seconds,
        )

    if (
        request_count
        > settings.admin_login_rate_limit
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many admin login attempts",
        )