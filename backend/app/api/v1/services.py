from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from typing import List

from starlette import status

from app.models import Booking, AvailabilityBlock
from app.models.service import Service
from app.schemas.booking import BookingStatus
from app.schemas.service import ServiceResponse, ServiceCreate
from app.dependencies import SessionDep
from datetime import date, datetime, time, timezone, timedelta
from fastapi import Query
# Створюємо роутер
router = APIRouter(prefix="/services", tags=["Services"])


# Сам endpoint
@router.get("/", response_model=List[ServiceResponse])
async def get_all_services(db: SessionDep):
    # Робимо асинхронний запит до БД: SELECT * FROM services;
    result = await db.execute(select(Service))
    # Витягуємо всі знайдені рядки
    services = result.scalars().all()
    return services


@router.post("/", response_model=ServiceResponse)
async def create_service(service_in: ServiceCreate,
                         db: SessionDep):
    service = Service(**service_in.model_dump())

    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


@router.get("/{service_id}/availability")
async def get_service_availability(service_id: int,
                                   db: SessionDep,
                                   date_value: date = Query(alias="date")
                                   ):
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()

    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    day_start = datetime.combine(
        date_value,
        time(hour=10),
        tzinfo=timezone.utc,
    )

    day_end = datetime.combine(
        date_value,
        time(hour=22),
        tzinfo=timezone.utc,
    )

    bookings_result = await db.execute(
        select(Booking).where(
            Booking.service_id == service_id,
            Booking.status == BookingStatus.confirmed.value,
            Booking.starts_at < day_end,
            Booking.ends_at > day_start,
        )
    )

    bookings = bookings_result.scalars().all()

    blocks_result = await db.execute(
        select(AvailabilityBlock).where(
            AvailabilityBlock.service_id == service_id,
            AvailabilityBlock.starts_at < day_end,
            AvailabilityBlock.ends_at > day_start,
        )
    )
    blocks = blocks_result.scalars().all()

    free_slots = []

    current = day_start

    # Генеруємо можливі слоти від відкриття до закриття
    while current + timedelta(hours=service.minimum_duration_hours) <= day_end:
        slot_end = current + timedelta(
            hours=service.minimum_duration_hours
        )

        # Чи перетинається цей слот хоча б з одним confirmed booking
        booking_conflict = any(
            booking.starts_at < slot_end
            and booking.ends_at > current
            for booking in bookings
        )

        # Чи перетинається цей слот хоча б з одним ручним блокуванням адміна
        block_conflict = any(
            block.starts_at < slot_end
            and block.ends_at > current
            for block in blocks
        )

        # Якщо конфліктів нема — слот вільний
        if not booking_conflict and not block_conflict:
            free_slots.append(current)

        # Переходимо до наступної години
        current += timedelta(hours=1)

        return free_slots

