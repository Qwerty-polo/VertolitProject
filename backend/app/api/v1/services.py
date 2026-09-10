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
from app.services.availability_service import build_free_slots

from zoneinfo import ZoneInfo
# Створюємо роутер
router = APIRouter(prefix="/services", tags=["Services"])

KYIV_TZ = ZoneInfo("Europe/Kyiv")
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
async def get_service_availability(
    service_id: int,
    db: SessionDep,
    date_value: date = Query(alias="date"),
):
    result = await db.execute(
        select(Service).where(Service.id == service_id)
    )
    service = result.scalar_one_or_none()

    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    day_start = datetime.combine(
        date_value,
        time(hour=10),
        tzinfo=KYIV_TZ,
    )

    day_end = datetime.combine(
        date_value,
        time(hour=22),
        tzinfo=KYIV_TZ,
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

    return build_free_slots(
        service=service,
        day_start=day_start,
        day_end=day_end,
        bookings=bookings,
        blocks=blocks,
    )
