import time

from fastapi import Request
from fastapi.responses import JSONResponse

from app.redis import redis_client
from app.config import settings

REQUEST_LIMIT = settings.global_rate_limit
WINDOW_SECONDS = settings.rate_limit_window_seconds


async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"

    current_window = int(time.time() // WINDOW_SECONDS)

    redis_key = f"rate_limit:{client_ip}:{current_window}"

    request_count = await redis_client.incr(redis_key)

    if request_count == 1:
        await redis_client.expire(redis_key, WINDOW_SECONDS)

    if request_count > REQUEST_LIMIT:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too many requests"
            },
        )

    return await call_next(request)