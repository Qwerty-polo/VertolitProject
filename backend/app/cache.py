import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from redis.exceptions import RedisError

from app.config import settings
from app.redis import redis_client

logger = logging.getLogger("vertolit")

BUSINESS_TZ = ZoneInfo(settings.timezone)


async def invalidate_availability_cache(
    service_id: int,
    starts_at: datetime,
    ends_at: datetime,
) -> None:
    local_starts_at = starts_at.astimezone(BUSINESS_TZ)

    local_ends_at = ends_at.astimezone(BUSINESS_TZ)

    current_date = local_starts_at.date()

    end_date = local_ends_at.date()

    while current_date <= end_date:
        cache_key = f"availability:{service_id}:{current_date.isoformat()}"

        try:
            await redis_client.delete(cache_key)

        except RedisError as exc:
            logger.warning(
                "Availability cache invalidation failed key=%s error=%s",
                cache_key,
                type(exc).__name__,
            )

        current_date += timedelta(days=1)
