from datetime import datetime, timedelta

from app.models.service import Service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.schemas.booking import BookingStatus

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
