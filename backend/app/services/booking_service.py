from app.models.service import Service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.schemas.booking import BookingStatus
from datetime import datetime, timedelta, time, timezone
from zoneinfo import ZoneInfo
from app.config import settings
from datetime import datetime, timedelta, timezone


KYIV_TZ = ZoneInfo(settings.timezone)

BUSINESS_START = time(
    hour=settings.business_start_hour
)

BUSINESS_END = time(
    hour=settings.business_end_hour
)

def validate_booking_within_business_hours(
    starts_at: datetime,
    ends_at: datetime,
) -> None:
    local_start = starts_at.astimezone(KYIV_TZ)
    local_end = ends_at.astimezone(KYIV_TZ)

    if local_start.date() != local_end.date():
        raise ValueError(
            "Booking must start and end on the same day"
        )

    if local_start.time() < BUSINESS_START:
        raise ValueError(
            f"Booking cannot start before "
            f"{BUSINESS_START.strftime('%H:%M')}"
        )

    if local_end.time() > BUSINESS_END:
        raise ValueError(
            f"Booking cannot end after "
            f"{BUSINESS_END.strftime('%H:%M')}"
        )

def calculate_booking_end(
    service: Service,
    starts_at: datetime,
    requested_duration_hours: int | None,
) -> datetime:
    duration_hours = (
        requested_duration_hours
        if requested_duration_hours is not None
        else service.minimum_duration_hours
    )

    if duration_hours < service.minimum_duration_hours:
        raise ValueError(
            f"Мінімальне бронювання: "
            f"{service.minimum_duration_hours} годин"
        )

    if duration_hours > settings.max_booking_duration_hours:
        raise ValueError(
            f"Максимальне бронювання: "
            f"{settings.max_booking_duration_hours} годин"
        )

    return starts_at + timedelta(hours=duration_hours)


async def has_confirmed_conflict(
        db: AsyncSession,
        service_id: int,
        starts_at: datetime,
        ends_at: datetime,
) -> bool:
    result = await db.execute(
        select(Booking).where(
            Booking.service_id == service_id,
            Booking.starts_at < ends_at,
            Booking.ends_at > starts_at,
            Booking.status == BookingStatus.confirmed.value,
        )
    )

    return result.scalars().first() is not None


async def has_other_confirmed_conflict(
    db: AsyncSession,
    booking: Booking,
) -> bool:
    result = await db.execute(
        select(Booking).where(
            Booking.id != booking.id,
            Booking.service_id == booking.service_id,
            Booking.starts_at < booking.ends_at,
            Booking.ends_at > booking.starts_at,
            Booking.status == BookingStatus.confirmed.value,
        )
    )

    return result.scalars().first() is not None


def validate_minimum_advance_booking(
    starts_at: datetime,
) -> None:
    minimum_start = (
        datetime.now(timezone.utc)
        + timedelta(
            hours=settings.minimum_advance_booking_hours
        )
    )

    if starts_at <= minimum_start:
        raise ValueError(
            f"Booking must be made at least "
            f"{settings.minimum_advance_booking_hours} hours in advance"
        )
