from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.cache import invalidate_availability_cache
from app.dependencies import SessionDep
from app.models.booking import Booking
from app.models.service import Service
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingStatus,
    BookingStatusUpdate,
)
from app.security.booking_rate_limit import booking_rate_limit
from app.services.booking_service import (
    calculate_booking_end,
    calculate_daily_booking_interval,
    has_confirmed_conflict,
    has_other_confirmed_conflict,
    validate_booking_within_business_hours,
    validate_minimum_advance_booking,
)
from app.tasks import send_booking_notification
from app.security.admin_auth import require_admin
from app.enums import ServiceBookingType
router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"],
)


@router.get(
    "/",
    response_model=list[BookingResponse],
    dependencies=[Depends(require_admin)],
)
async def get_all_bookings(
    db: SessionDep,
):
    result = await db.execute(
        select(Booking)
    )

    bookings = result.scalars().all()

    return bookings


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    dependencies=[Depends(require_admin)],
    responses={
        404: {
            "description": "Booking not found",
        },
        401: {
            "description": "Admin authentication required",
        },
    },
)


async def get_booking_by_id(
    booking_id: int,
    db: SessionDep,
):
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id
        )
    )

    booking = result.scalar_one_or_none()

    if booking is None:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    return booking


@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(booking_rate_limit)],
    responses={
        400: {
            "description": "Invalid booking parameters",
            "content": {
                "application/json": {
                    "examples": {
                        "business_hours": {
                            "summary": "Outside business hours",
                            "value": {
                                "detail": "Booking cannot start before 10:00"
                            },
                        },
                        "minimum_duration": {
                            "summary": "Duration is too short",
                            "value": {
                                "detail": "Minimum booking duration is 3 hours"
                            },
                        },
                        "maximum_duration": {
                            "summary": "Duration is too long",
                            "value": {
                                "detail": "Maximum booking duration is 12 hours"
                            },
                        },
                        "minimum_advance": {
                            "summary": "Booking is too soon",
                            "value": {
                                "detail": "Booking must be made at least 2 hours in advance"
                            },
                        },
                    }
                }
            },
        },
        404: {
            "description": "Service not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Service not found"
                    }
                }
            },
        },
        409: {
            "description": "Time slot conflict",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "This time slot is already booked"
                    }
                }
            },
        },
        429: {
            "description": "Booking rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Too many booking attempts"
                    }
                }
            },
        },
    },
)
async def create_booking(
    booking_in: BookingCreate,
    db: SessionDep,
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
            detail="Service not found",
        )

    if (
            service.booking_type
            == ServiceBookingType.phone_only.value
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This service is booked by phone",
        )

    try:
        if (
                service.booking_type
                == ServiceBookingType.hourly.value
        ):
            if booking_in.starts_at is None:
                raise ValueError(
                    "Для цієї послуги потрібно обрати час"
                )

            starts_at = booking_in.starts_at

            ends_at = calculate_booking_end(
                service=service,
                starts_at=starts_at,
                requested_duration_hours=(
                    booking_in.duration_hours
                ),
            )

            validate_minimum_advance_booking(
                starts_at=starts_at,
            )

            validate_booking_within_business_hours(
                starts_at=starts_at,
                ends_at=ends_at,
            )

        elif (
                service.booking_type
                == ServiceBookingType.daily.value
        ):
            if (
                    booking_in.check_in_date is None
                    or booking_in.check_out_date is None
            ):
                raise ValueError(
                    "Оберіть дату заїзду та дату виїзду"
                )

            starts_at, ends_at = (
                calculate_daily_booking_interval(
                    service=service,
                    check_in_date=(
                        booking_in.check_in_date
                    ),
                    check_out_date=(
                        booking_in.check_out_date
                    ),
                )
            )

        else:
            raise ValueError(
                "Unsupported booking type"
            )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    conflict = await has_confirmed_conflict(
        db=db,
        service_id=service.id,
        starts_at=starts_at,
        ends_at=ends_at,
    )

    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This time slot is already booked",
        )

    booking = Booking(
        service_id=booking_in.service_id,
        customer_name=booking_in.customer_name,
        customer_phone=booking_in.customer_phone,
        starts_at=starts_at,
        ends_at=ends_at,
        guests=booking_in.guests,
        comment=booking_in.comment,
    )

    db.add(booking)

    await db.commit()
    await db.refresh(booking)

    send_booking_notification.delay(
        booking.id,
        booking.service_id,
        booking.starts_at.isoformat(),
    )

    return booking


@router.patch(
    "/{booking_id}/status",
    response_model=BookingResponse,
    dependencies=[Depends(require_admin)],
    responses={
        404: {
            "description": "Booking not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Booking not found"
                    }
                }
            },
        },
        409: {
            "description": "Confirmed booking conflict",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "This time slot is already confirmed"
                    }
                }
            },
        },
    },
)
async def update_booking_status(
    booking_id: int,
    status_in: BookingStatusUpdate,
    db: SessionDep,
):
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id
        )
    )

    booking = result.scalar_one_or_none()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
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

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()

        if (
                getattr(
                    exc.orig,
                    "sqlstate",
                    None,
                )
                == "23P01"
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This time slot "
                    "is already confirmed"
                ),
            ) from exc

        raise

    await db.refresh(booking)

    await invalidate_availability_cache(
        service_id=booking.service_id,
        starts_at=booking.starts_at,
        ends_at=booking.ends_at,
    )

    return booking