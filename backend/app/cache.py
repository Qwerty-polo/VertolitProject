from datetime import datetime, timedelta

from app.redis import redis_client


async def invalidate_availability_cache(
    service_id: int,
    starts_at: datetime,
    ends_at: datetime,
) -> None:
    current_date = starts_at.date()
    end_date = ends_at.date()

    while current_date <= end_date:
        cache_key = (
            f"availability:{service_id}:{current_date.isoformat()}"
        )

        await redis_client.delete(cache_key)

        current_date += timedelta(days=1)