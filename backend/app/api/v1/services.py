import json
import logging
from datetime import (
    date,
    datetime,
    time,
)
from zoneinfo import ZoneInfo

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from redis.exceptions import RedisError
from sqlalchemy import select
from starlette import status

from app.config import settings
from app.dependencies import SessionDep
from app.enums import ServiceBookingType
from app.models import (
    AvailabilityBlock,
    Booking,
)
from app.models.service import Service
from app.redis import redis_client
from app.schemas.booking import BookingStatus
from app.schemas.service import (
    ServiceCreate,
    ServiceResponse,
)
from app.security.admin_auth import require_admin
from app.services.availability_service import (
    build_free_slots,
)

logger = logging.getLogger("vertolit")

router = APIRouter(
    prefix="/services",
    tags=["Services"],
)

KYIV_TZ = ZoneInfo(settings.timezone)


@router.get(
    "/",
    response_model=list[ServiceResponse],
)
async def get_all_services(
    db: SessionDep,
):
    result = await db.execute(select(Service))

    services = result.scalars().all()

    return services


@router.post(
    "/",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_service(
    service_in: ServiceCreate,
    db: SessionDep,
):
    service = Service(**service_in.model_dump())

    db.add(service)

    await db.commit()
    await db.refresh(service)

    return service


@router.get("/{service_id}/availability")
async def get_service_availability(
    service_id: int,
    db: SessionDep,
    date_value: date = Query(alias="date"),
):
    result = await db.execute(select(Service).where(Service.id == service_id))

    service = result.scalar_one_or_none()

    if service is None:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail="Service not found",
        )

    if service.booking_type != ServiceBookingType.hourly.value:
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail=("Hourly availability is only available for hourly services"),
        )

    cache_key = f"availability:{service_id}:{date_value.isoformat()}"

    cached = None

    try:
        cached = await redis_client.get(cache_key)

    except RedisError as exc:
        logger.warning(
            "Availability cache read failed key=%s error=%s",
            cache_key,
            type(exc).__name__,
        )

    if cached is not None:
        try:
            return json.loads(cached)

        except json.JSONDecodeError:
            logger.warning(
                "Invalid availability cache value key=%s",
                cache_key,
            )

    day_start = datetime.combine(
        date_value,
        time(hour=(settings.business_start_hour)),
        tzinfo=KYIV_TZ,
    )

    day_end = datetime.combine(
        date_value,
        time(hour=(settings.business_end_hour)),
        tzinfo=KYIV_TZ,
    )

    bookings_result = await db.execute(
        select(Booking).where(
            Booking.service_id == service_id,
            Booking.status == BookingStatus.confirmed.value,
            Booking.starts_at < day_end,
            Booking.ends_at > day_start,
        )
    )

    bookings = bookings_result.scalars().all()

    blocks_result = await db.execute(
        select(AvailabilityBlock).where(
            AvailabilityBlock.service_id == service_id,
            AvailabilityBlock.starts_at < day_end,
            AvailabilityBlock.ends_at > day_start,
        )
    )

    blocks = blocks_result.scalars().all()

    free_slots = build_free_slots(
        service=service,
        day_start=day_start,
        day_end=day_end,
        bookings=bookings,
        blocks=blocks,
    )

    serialized_slots = [slot.isoformat() for slot in free_slots]

    try:
        await redis_client.set(
            cache_key,
            json.dumps(serialized_slots),
            ex=(settings.availability_cache_ttl),
        )

    except RedisError as exc:
        logger.warning(
            "Availability cache write failed key=%s error=%s",
            cache_key,
            type(exc).__name__,
        )

    return serialized_slots
