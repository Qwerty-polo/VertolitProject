from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.models.booking import Booking
from app.models.service import Service
from app.schemas.booking import BookingCreate, BookingResponse

from .services import SessionDep


router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)


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