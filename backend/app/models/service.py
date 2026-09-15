from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import ServiceBookingType


if TYPE_CHECKING:
    from .availability_block import AvailabilityBlock
    from .booking import Booking


class Service(Base):
    __tablename__ = "services"

    __table_args__ = (
        CheckConstraint(
            "booking_type IN "
            "('hourly', 'daily', 'phone_only')",
            name="ck_services_booking_type",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    price: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    booking_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ServiceBookingType.hourly.value,
        server_default=ServiceBookingType.hourly.value,
    )

    minimum_duration_hours: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    minimum_duration_days: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="service"
    )

    availability_blocks: Mapped[list["AvailabilityBlock"]] = relationship(
        back_populates="service"
    )