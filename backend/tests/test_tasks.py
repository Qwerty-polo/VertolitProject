import asyncio
import os
import subprocess
import sys
from contextlib import nullcontext
from datetime import UTC, datetime, timedelta
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.config import settings
from app.models.booking import Booking
from app.models.service import Service
from app.tasks import _check_upcoming_bookings, check_upcoming_bookings


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

        starts_at = datetime.now(UTC) + timedelta(hours=2)

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
            "app.tasks.settings.database_url",
            settings.test_database_url,
        ),
        patch("app.tasks.send_booking_reminder.delay") as delay_mock,
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

        starts_at = datetime.now(UTC) + timedelta(hours=2)

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
            "app.tasks.settings.database_url",
            settings.test_database_url,
        ),
        patch("app.tasks.send_booking_reminder.delay") as delay_mock,
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

        starts_at = datetime.now(UTC) + timedelta(hours=2)

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
            "app.tasks.settings.database_url",
            settings.test_database_url,
        ),
        patch("app.tasks.send_booking_reminder.delay") as delay_mock,
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

        starts_at = datetime.now(UTC) + timedelta(hours=2)

        booking = Booking(
            service_id=service.id,
            customer_name="Ivan",
            customer_phone="+380991112233",
            starts_at=starts_at,
            ends_at=(starts_at + timedelta(hours=3)),
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
            "app.tasks.settings.database_url",
            settings.test_database_url,
        ),
        patch(
            "app.tasks.send_booking_reminder.delay",
            side_effect=RuntimeError("Celery broker unavailable"),
        ) as delay_mock,
    ):
        count = await _check_upcoming_bookings()

    assert count == 0
    delay_mock.assert_called_once()

    async with test_db_session_maker() as db:
        saved_booking = await db.get(
            Booking,
            booking_id,
        )

        assert saved_booking is not None
        assert saved_booking.reminder_sent is False


@pytest.mark.asyncio
async def test_reminder_scan_repeated_across_event_loops(test_db_session_maker):
    async with test_db_session_maker() as db:
        service = Service(
            name="Repeated scan",
            price=1500,
            minimum_duration_hours=3,
        )
        db.add(service)
        await db.flush()
        starts_at = datetime.now(UTC) + timedelta(hours=2)
        booking = Booking(
            service_id=service.id,
            customer_name="Ivan",
            customer_phone="+380991112233",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=3),
            guests=4,
            status="confirmed",
            reminder_sent=False,
        )
        db.add(booking)
        await db.commit()
        booking_id = booking.id

    # Import the task in a fresh process with only the test database configured.
    # Real pooled asyncpg connections must survive until task cleanup; mocking
    # the session or using NullPool would conceal the original loop-reuse bug.
    script = dedent("""\
        from unittest.mock import patch
        from app.tasks import check_upcoming_bookings

        with patch("app.tasks.send_booking_reminder.delay") as notification:
            first = check_upcoming_bookings.run()
            assert first == {"status": "checked", "bookings_found": 1}, first
            second = check_upcoming_bookings.run()
            assert second == {"status": "checked", "bookings_found": 0}, second
            notification.assert_called_once()
    """)
    env = os.environ.copy()
    env.update(
        APP_ENV="test",
        DATABASE_URL=settings.test_database_url,
        TEST_DATABASE_URL=settings.test_database_url,
        SQLALCHEMY_ECHO="false",
    )
    result = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-B", "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    async with test_db_session_maker() as db:
        saved_booking = await db.get(Booking, booking_id)
        assert saved_booking.reminder_sent is True


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [None, "execute", "commit"])
async def test_reminder_scan_disposes_engine_before_loop_closes(failure):
    events = []
    original_close = AsyncSession.close
    original_dispose = AsyncEngine.dispose

    def create_engine(*args, **kwargs):
        engine = create_async_engine(*args, **kwargs)
        events.append(("created", asyncio.get_running_loop()))
        return engine

    async def close_session(session):
        await original_close(session)
        events.append(("session_closed", asyncio.get_running_loop()))

    async def dispose_engine(engine):
        assert engine.pool.checkedout() == 0
        await original_dispose(engine)
        events.append(("disposed", asyncio.get_running_loop()))

    database_failure = (
        patch.object(
            AsyncSession, failure, side_effect=RuntimeError("Database work failed")
        )
        if failure
        else nullcontext()
    )
    with (
        patch("app.tasks.settings.database_url", settings.test_database_url),
        patch("app.tasks.create_async_engine", side_effect=create_engine),
        patch.object(AsyncSession, "close", close_session),
        patch.object(AsyncEngine, "dispose", dispose_engine),
        database_failure,
    ):
        # The synchronous wrapper owns its loop, independently of pytest's loop.
        if failure:
            with pytest.raises(RuntimeError, match="Database work failed"):
                await asyncio.to_thread(check_upcoming_bookings.run)
        else:
            result = await asyncio.to_thread(check_upcoming_bookings.run)
            assert result == {"status": "checked", "bookings_found": 0}

    assert [name for name, _ in events] == ["created", "session_closed", "disposed"]
    owning_loop = events[0][1]
    assert all(loop is owning_loop for _, loop in events)
    assert owning_loop.is_closed()
