import logging
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError

from app.config import settings
from app.redis import redis_client

logger = logging.getLogger("vertolit")

REQUEST_LIMIT = settings.global_rate_limit
WINDOW_SECONDS = settings.rate_limit_window_seconds


async def rate_limit_middleware(
    request: Request,
    call_next,
):
    if request.url.path.rstrip("/") == "/api/v1/health":
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"

    current_window = int(time.time() // WINDOW_SECONDS)

    redis_key = f"rate_limit:{client_ip}:{current_window}"

    try:
        request_count = await redis_client.incr(redis_key)

        if request_count == 1:
            await redis_client.expire(
                redis_key,
                WINDOW_SECONDS,
            )

    except RedisError as exc:
        logger.warning(
            "Global rate limiter unavailable; "
            "request allowed "
            "path=%s client_ip=%s error=%s",
            request.url.path,
            client_ip,
            type(exc).__name__,
        )

        return await call_next(request)

    if request_count > REQUEST_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"},
        )

    return await call_next(request)
