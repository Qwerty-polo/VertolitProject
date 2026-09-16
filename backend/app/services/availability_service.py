from datetime import datetime, timedelta

from app.models.availability_block import AvailabilityBlock
from app.models.booking import Booking
from app.models.service import Service


def build_free_slots(
    service: Service,
    day_start: datetime,
    day_end: datetime,
    bookings: list[Booking],
    blocks: list[AvailabilityBlock],
):
    free_slots = []
    current = day_start

    while current + timedelta(hours=service.minimum_duration_hours) <= day_end:
        slot_end = current + timedelta(hours=service.minimum_duration_hours)

        booking_conflict = any(
            booking.starts_at < slot_end and booking.ends_at > current
            for booking in bookings
        )

        block_conflict = any(
            block.starts_at < slot_end and block.ends_at > current for block in blocks
        )

        if not booking_conflict and not block_conflict:
            free_slots.append(current)

        current += timedelta(hours=1)

    return free_slots
