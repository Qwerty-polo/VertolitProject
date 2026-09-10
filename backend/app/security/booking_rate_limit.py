import time

from fastapi import HTTPException, Request, status

from app.redis import redis_client


BOOKING_LIMIT = 5
WINDOW_SECONDS = 60


async def booking_rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"

    current_window = int(time.time() // WINDOW_SECONDS)

    redis_key = f"booking_rate_limit:{client_ip}:{current_window}"

    request_count = await redis_client.incr(redis_key)

    if request_count == 1:
        await redis_client.expire(
            redis_key,
            WINDOW_SECONDS,
        )

    if request_count > BOOKING_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many booking attempts",
        )