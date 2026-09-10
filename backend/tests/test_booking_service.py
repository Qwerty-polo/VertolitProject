from datetime import datetime, timezone, timedelta

import pytest

from app.models.service import Service
from app.services.booking_service import calculate_booking_end
from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.booking_service import (
    validate_booking_within_business_hours,
)

KYIV_TZ = ZoneInfo("Europe/Kyiv")

def test_calculate_booking_end_with_requested_duration():
    service = Service(
        name="Sauna",
        description="Test",
        price=1500,
        minimum_duration_hours=3,
    )

    starts_at = datetime(
        2026, 9, 20, 10, 0,
        tzinfo=timezone.utc,
    )

    ends_at = calculate_booking_end(
        service=service,
        starts_at=starts_at,
        requested_duration_hours=5,
    )

    assert ends_at == starts_at + timedelta(hours=5)


def test_calculate_booking_end_uses_minimum_duration():
    service = Service(
        name="Sauna",
        description="Test",
        price=1500,
        minimum_duration_hours=3,
    )

    starts_at = datetime(
        2026, 9, 20, 10, 0,
        tzinfo=timezone.utc,
    )

    ends_at = calculate_booking_end(
        service=service,
        starts_at=starts_at,
        requested_duration_hours=None,
    )

    assert ends_at == starts_at + timedelta(hours=3)


def test_calculate_booking_end_rejects_short_duration():
    service = Service(
        name="Sauna",
        description="Test",
        price=1500,
        minimum_duration_hours=3,
    )

    starts_at = datetime(
        2026, 9, 20, 10, 0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        ValueError,
        match="Minimum booking duration is 3 hours",
    ):
        calculate_booking_end(
            service=service,
            starts_at=starts_at,
            requested_duration_hours=2,
        )


def test_booking_within_business_hours_is_valid():
    starts_at = datetime(
        2026, 9, 20, 10, 0,
        tzinfo=KYIV_TZ,
    )
    ends_at = datetime(
        2026, 9, 20, 13, 0,
        tzinfo=KYIV_TZ,
    )

    validate_booking_within_business_hours(
        starts_at=starts_at,
        ends_at=ends_at,
    )


def test_booking_cannot_start_before_business_hours():
    starts_at = datetime(
        2026, 9, 20, 9, 0,
        tzinfo=KYIV_TZ,
    )
    ends_at = datetime(
        2026, 9, 20, 12, 0,
        tzinfo=KYIV_TZ,
    )

    with pytest.raises(
        ValueError,
        match="Booking cannot start before 10:00",
    ):
        validate_booking_within_business_hours(
            starts_at=starts_at,
            ends_at=ends_at,
        )


def test_booking_cannot_end_after_business_hours():
    starts_at = datetime(
        2026, 9, 20, 20, 0,
        tzinfo=KYIV_TZ,
    )
    ends_at = datetime(
        2026, 9, 20, 23, 0,
        tzinfo=KYIV_TZ,
    )

    with pytest.raises(
        ValueError,
        match="Booking cannot end after 22:00",
    ):
        validate_booking_within_business_hours(
            starts_at=starts_at,
            ends_at=ends_at,
        )


def test_booking_can_end_exactly_at_closing_time():
    starts_at = datetime(
        2026, 9, 20, 19, 0,
        tzinfo=KYIV_TZ,
    )
    ends_at = datetime(
        2026, 9, 20, 22, 0,
        tzinfo=KYIV_TZ,
    )

    validate_booking_within_business_hours(
        starts_at=starts_at,
        ends_at=ends_at,
    )