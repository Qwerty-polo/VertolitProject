from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.models.booking import Booking
from app.models.service import Service
from app.tasks import _check_upcoming_bookings


@pytest.mark.asyncio
async def test_upcoming_booking_creates_reminder(
    test_db_session_maker,
):
    async with test_db_session_maker() as db:
        service = Service(
            name="Sauna",
            description="Test",
            price=1500,
            minimum_duration_hours=3,
        )

        db.add(service)
        await db.commit()
        await db.refresh(service)

        starts_at = datetime.now(timezone.utc) + timedelta(hours=2)

        booking = Booking(
            service_id=service.id,
            customer_name="Ivan",
            customer_phone="+380991112233",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=3),
            guests=4,
            status="confirmed",
            comment=None,
            reminder_sent=False,
        )

        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        booking_id = booking.id

    with (
        patch(
            "app.tasks.async_session_maker",
            test_db_session_maker,
        ),
        patch(
            "app.tasks.send_booking_reminder.delay"
        ) as delay_mock,
    ):
        count = await _check_upcoming_bookings()

    assert count == 1

    delay_mock.assert_called_once()

    called_args = delay_mock.call_args.args

    assert called_args[0] == booking_id
    async with test_db_session_maker() as db:
        saved_booking = await db.get(
            Booking,
            booking_id,
        )

        assert saved_booking is not None
        assert saved_booking.reminder_sent is True


@pytest.mark.asyncio
async def test_reminder_is_not_sent_twice(
    test_db_session_maker,
):
    async with test_db_session_maker() as db:
        service = Service(
            name="Sauna",
            description="Test",
            price=1500,
            minimum_duration_hours=3,
        )

        db.add(service)
        await db.commit()
        await db.refresh(service)

        starts_at = datetime.now(timezone.utc) + timedelta(hours=2)

        booking = Booking(
            service_id=service.id,
            customer_name="Ivan",
            customer_phone="+380991112233",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=3),
            guests=4,
            status="confirmed",
            comment=None,
            reminder_sent=True,
        )

        db.add(booking)
        await db.commit()

    with (
        patch(
            "app.tasks.async_session_maker",
            test_db_session_maker,
        ),
        patch(
            "app.tasks.send_booking_reminder.delay"
        ) as delay_mock,
    ):
        count = await _check_upcoming_bookings()

    assert count == 0
    delay_mock.assert_not_called()


@pytest.mark.asyncio
async def test_pending_booking_does_not_receive_reminder(
    test_db_session_maker,
):
    async with test_db_session_maker() as db:
        service = Service(
            name="Sauna",
            description="Test",
            price=1500,
            minimum_duration_hours=3,
        )

        db.add(service)
        await db.commit()
        await db.refresh(service)

        starts_at = datetime.now(timezone.utc) + timedelta(hours=2)

        booking = Booking(
            service_id=service.id,
            customer_name="Ivan",
            customer_phone="+380991112233",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=3),
            guests=4,
            status="pending",
            comment=None,
            reminder_sent=False,
        )

        db.add(booking)
        await db.commit()

    with (
        patch(
            "app.tasks.async_session_maker",
            test_db_session_maker,
        ),
        patch(
            "app.tasks.send_booking_reminder.delay"
        ) as delay_mock,
    ):
        count = await _check_upcoming_bookings()

    assert count == 0
    delay_mock.assert_not_called()


@pytest.mark.asyncio
async def test_failed_reminder_enqueue_is_retried_later(
    test_db_session_maker,
):
    async with test_db_session_maker() as db:
        service = Service(
            name="Sauna Reminder Failure",
            description="Test",
            price=1500,
            minimum_duration_hours=3,
        )

        db.add(service)
        await db.commit()
        await db.refresh(service)

        starts_at = (
            datetime.now(timezone.utc)
            + timedelta(hours=2)
        )

        booking = Booking(
            service_id=service.id,
            customer_name="Ivan",
            customer_phone="+380991112233",
            starts_at=starts_at,
            ends_at=(
                starts_at
                + timedelta(hours=3)
            ),
            guests=4,
            status="confirmed",
            comment=None,
            reminder_sent=False,
        )

        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        booking_id = booking.id

    with (
        patch(
            "app.tasks.async_session_maker",
            test_db_session_maker,
        ),
        patch(
            "app.tasks."
            "send_booking_reminder.delay",
            side_effect=RuntimeError(
                "Celery broker unavailable"
            ),
        ) as delay_mock,
    ):
        count = await (
            _check_upcoming_bookings()
        )

    assert count == 0
    delay_mock.assert_called_once()

    async with test_db_session_maker() as db:
        saved_booking = await db.get(
            Booking,
            booking_id,
        )

        assert saved_booking is not None
        assert (
            saved_booking.reminder_sent
            is False
        )