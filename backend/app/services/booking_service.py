from datetime import datetime, timedelta

from app.models.service import Service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.schemas.booking import BookingStatus
from datetime import time
from zoneinfo import ZoneInfo


KYIV_TZ = ZoneInfo("Europe/Kyiv")

BUSINESS_START = time(hour=10)
BUSINESS_END = time(hour=22)

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
            "Booking cannot start before 10:00"
        )

    if local_end.time() > BUSINESS_END:
        raise ValueError(
            "Booking cannot end after 22:00"
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
            f"Minimum booking duration is "
            f"{service.minimum_duration_hours} hours"
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
