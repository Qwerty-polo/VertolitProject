import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.celery_app import celery_app
from app.database import async_session_maker
from app.models.booking import Booking
from app.schemas.booking import BookingStatus


logger = logging.getLogger("vertolit.tasks")


@celery_app.task(
    name="send_booking_notification",
)
def send_booking_notification(
    booking_id: int,
    service_id: int,
    starts_at: str,
):
    logger.info(
        "New booking notification: "
        "booking_id=%s service_id=%s starts_at=%s",
        booking_id,
        service_id,
        starts_at,
    )

    return {
        "status": "sent",
        "booking_id": booking_id,
    }


@celery_app.task(
    name="send_booking_reminder",
)
def send_booking_reminder(
    booking_id: int,
    starts_at: str,
):
    logger.info(
        "Booking reminder: booking_id=%s starts_at=%s",
        booking_id,
        starts_at,
    )

    return {
        "status": "reminder_sent",
        "booking_id": booking_id,
    }


async def _check_upcoming_bookings():
    now = datetime.now(timezone.utc)
    reminder_until = now + timedelta(hours=24)

    async with async_session_maker() as db:
        result = await db.execute(
            select(Booking).where(
                Booking.status == BookingStatus.confirmed.value,
                Booking.starts_at > now,
                Booking.starts_at <= reminder_until,
                Booking.reminder_sent.is_(False),
            )
        )

        bookings = result.scalars().all()

        for booking in bookings:
            send_booking_reminder.delay(
                booking.id,
                booking.starts_at.isoformat(),
            )

            booking.reminder_sent = True

        await db.commit()

        logger.info(
            "Found %s upcoming bookings",
            len(bookings),
        )

        return len(bookings)


@celery_app.task(
    name="app.tasks.check_upcoming_bookings",
)
def check_upcoming_bookings():
    count = asyncio.run(
        _check_upcoming_bookings()
    )

    return {
        "status": "checked",
        "bookings_found": count,
    }