from datetime import datetime, timezone, timedelta

import pytest

from app.models.service import Service
from app.services.booking_service import calculate_booking_end


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