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

BOOKING_LIMIT = settings.booking_rate_limit
WINDOW_SECONDS = settings.rate_limit_window_seconds


async def booking_rate_limit(
    request: Request,
) -> None:
    client_ip = request.client.host if request.client else "unknown"

    current_window = int(time.time() // WINDOW_SECONDS)

    redis_key = f"booking_rate_limit:{client_ip}:{current_window}"

    try:
        request_count = await redis_client.incr(redis_key)

        if request_count == 1:
            await redis_client.expire(
                redis_key,
                WINDOW_SECONDS,
            )

    except RedisError as exc:
        logger.warning(
            "Booking rate limiter unavailable; "
            "booking request allowed "
            "client_ip=%s error=%s",
            client_ip,
            type(exc).__name__,
        )

        return

    if request_count > BOOKING_LIMIT:
        raise HTTPException(
            status_code=(status.HTTP_429_TOO_MANY_REQUESTS),
            detail="Too many booking attempts",
        )
