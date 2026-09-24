from datetime import (
    UTC,
    date,
    datetime,
    time,
    timedelta,
)
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.availability_block import AvailabilityBlock
from app.models.booking import Booking
from app.models.service import Service
from app.schemas.booking import BookingStatus

KYIV_TZ = ZoneInfo(settings.timezone)

BUSINESS_START = time(hour=settings.business_start_hour)

BUSINESS_END = time(hour=settings.business_end_hour)


def validate_booking_within_business_hours(
    starts_at: datetime,
    ends_at: datetime,
) -> None:
    local_start = starts_at.astimezone(KYIV_TZ)
    local_end = ends_at.astimezone(KYIV_TZ)

    if local_start.date() != local_end.date():
        raise ValueError("Booking must start and end on the same day")

    if local_start.time() < BUSINESS_START:
        raise ValueError(
            f"Booking cannot start before {BUSINESS_START.strftime('%H:%M')}"
        )

    if local_end.time() > BUSINESS_END:
        raise ValueError(f"Booking cannot end after {BUSINESS_END.strftime('%H:%M')}")


def calculate_booking_end(
    service: Service,
    starts_at: datetime,
    requested_duration_hours: int | None,
) -> datetime:
    minimum_hours = service.minimum_duration_hours

    if minimum_hours is None:
        raise ValueError("Hourly service has no minimum duration")

    duration_hours = (
        requested_duration_hours
        if requested_duration_hours is not None
        else minimum_hours
    )

    if duration_hours < minimum_hours:
        raise ValueError(f"Мінімальне бронювання: {minimum_hours} годин")

    if duration_hours > settings.max_booking_duration_hours:
        raise ValueError(
            f"Максимальне бронювання: {settings.max_booking_duration_hours} годин"
        )

    return starts_at + timedelta(hours=duration_hours)


def calculate_daily_booking_interval(
    service: Service,
    check_in_date: date,
    check_out_date: date,
) -> tuple[datetime, datetime]:
    if check_out_date <= check_in_date:
        raise ValueError("Дата виїзду повинна бути пізніше дати заїзду")

    minimum_days = service.minimum_duration_days

    if minimum_days is None:
        raise ValueError("Daily service has no minimum duration")

    duration_days = (check_out_date - check_in_date).days

    if duration_days < minimum_days:
        raise ValueError(f"Мінімальне бронювання: {minimum_days} доба")

    today = datetime.now(KYIV_TZ).date()

    if check_in_date < today:
        raise ValueError("Дата заїзду не може бути в минулому")

    starts_at = datetime.combine(
        check_in_date,
        time.min,
        tzinfo=KYIV_TZ,
    )

    ends_at = datetime.combine(
        check_out_date,
        time.min,
        tzinfo=KYIV_TZ,
    )

    return starts_at, ends_at


async def has_availability_block_conflict(
    db: AsyncSession,
    service_id: int,
    starts_at: datetime,
    ends_at: datetime,
) -> bool:
    result = await db.execute(
        select(AvailabilityBlock.id)
        .where(
            AvailabilityBlock.service_id == service_id,
            AvailabilityBlock.starts_at < ends_at,
            AvailabilityBlock.ends_at > starts_at,
        )
        .limit(1)
    )

    return result.scalar_one_or_none() is not None


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
    minimum_start = datetime.now(UTC) + timedelta(
        hours=settings.minimum_advance_booking_hours
    )

    if starts_at <= minimum_start:
        raise ValueError(
            f"Booking must be made at least "
            f"{settings.minimum_advance_booking_hours} "
            f"hours in advance"
        )
