import logging
import time

from fastapi import (
    HTTPException,
    Request,
    status,
)
from redis.exceptions import RedisError

from app.config import settings
from app.redis import redis_client

logger = logging.getLogger("vertolit")


async def admin_login_rate_limit(
    request: Request,
) -> None:
    client_ip = request.client.host if request.client else "unknown"

    window_seconds = settings.admin_login_rate_limit_window_seconds

    current_window = int(time.time() // window_seconds)

    redis_key = f"admin_login_rate_limit:{client_ip}:{current_window}"

    try:
        request_count = await redis_client.incr(redis_key)

        if request_count == 1:
            await redis_client.expire(
                redis_key,
                window_seconds,
            )

    except RedisError as exc:
        logger.error(
            "Admin login rate limiter unavailable client_ip=%s error=%s",
            client_ip,
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
            detail=("Admin authentication service unavailable"),
        ) from exc

    if request_count > settings.admin_login_rate_limit:
        raise HTTPException(
            status_code=(status.HTTP_429_TOO_MANY_REQUESTS),
            detail=("Too many admin login attempts"),
        )
