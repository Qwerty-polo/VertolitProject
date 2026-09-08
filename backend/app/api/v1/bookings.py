from datetime import timedelta
from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.models.booking import Booking
from app.models.service import Service
from app.schemas.booking import BookingCreate, BookingResponse, BookingStatus, BookingStatusUpdate

from app.dependencies import SessionDep

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

    duration_hours = (
        booking_in.duration_hours
        if booking_in.duration_hours is not None
        else service.minimum_duration_hours
    )

    if duration_hours < service.minimum_duration_hours:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Minimum booking duration is "
                f"{service.minimum_duration_hours} hours"
            )
        )

    ends_at = booking_in.starts_at + timedelta(
        hours=duration_hours
    )

    reserved = await db.execute(
        select(Booking).where(
            Booking.service_id == service.id,
            Booking.starts_at < ends_at,
            Booking.ends_at > booking_in.starts_at,
            Booking.status != BookingStatus.cancelled.value,
        )
    )

    conflict = reserved.scalars().first()

    if conflict is not None:
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
async def update_booking_status(booking_id: int, status_in: BookingStatusUpdate,db: SessionDep):
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()

    if booking is None:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )
    booking.status = status_in.status.value

    await db.commit()
    await db.refresh(booking)
    return booking
