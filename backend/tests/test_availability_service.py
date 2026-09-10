from datetime import datetime, timezone

from app.models.service import Service
from app.services.availability_service import build_free_slots


def test_build_free_slots_without_conflicts():
    service = Service(
        name="Sauna",
        description="Test",
        price=1500,
        minimum_duration_hours=3,
    )

    day_start = datetime(
        2026, 9, 20, 10, 0,
        tzinfo=timezone.utc,
    )
    day_end = datetime(
        2026, 9, 20, 22, 0,
        tzinfo=timezone.utc,
    )

    free_slots = build_free_slots(
        service=service,
        day_start=day_start,
        day_end=day_end,
        bookings=[],
        blocks=[],
    )

    assert len(free_slots) == 10
    assert free_slots[0] == day_start
    assert free_slots[-1].hour == 19