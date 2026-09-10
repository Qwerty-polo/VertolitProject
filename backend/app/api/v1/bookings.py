from datetime import timedelta
from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.models.booking import Booking
from app.models.service import Service
from app.schemas.booking import BookingCreate, BookingResponse, BookingStatus, BookingStatusUpdate

from app.dependencies import SessionDep
from app.services.booking_service import calculate_booking_end
from app.services.booking_service import (
    calculate_booking_end,
    has_confirmed_conflict,
)
from app.services.booking_service import (
    calculate_booking_end,
    has_confirmed_conflict,
    has_other_confirmed_conflict,
)
from app.cache import invalidate_availability_cache
router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)

@router.get("/", response_model=List[BookingResponse])
async def get_all_bookings(db:SessionDep):
    result = await db.execute(select(Booking))
    if not Booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    bookings = result.scalars().all()
    return bookings


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: int, db: SessionDep):
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    return booking

@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_booking(
    booking_in: BookingCreate,
    db: SessionDep
):
    result = await db.execute(
        select(Service).where(
            Service.id == booking_in.service_id
        )
    )

    service = result.scalar_one_or_none()

    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    try:
        ends_at = calculate_booking_end(
            service=service,
            starts_at=booking_in.starts_at,
            requested_duration_hours=booking_in.duration_hours,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    conflict = await has_confirmed_conflict(
        db=db,
        service_id=service.id,
        starts_at=booking_in.starts_at,
        ends_at=ends_at,
    )

    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This time slot is already booked"
        )

    booking_data = booking_in.model_dump(
        exclude={"duration_hours"}
    )

    booking = Booking(
        **booking_data,
        ends_at=ends_at
    )

    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    return booking

@router.patch("/{booking_id}/status", response_model=BookingResponse)
async def update_booking_status(
    booking_id: int,
    status_in: BookingStatusUpdate,
    db: SessionDep
):
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )

    booking = result.scalar_one_or_none()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    if status_in.status == BookingStatus.confirmed:
        conflict = await has_other_confirmed_conflict(
            db=db,
            booking=booking,
        )

        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This time slot is already confirmed",
            )

    booking.status = status_in.status.value
    
    await db.commit()
    await db.refresh(booking)

    await invalidate_availability_cache(
        service_id=booking.service_id,
        starts_at=booking.starts_at,
        ends_at=booking.ends_at,
    )

    return booking
