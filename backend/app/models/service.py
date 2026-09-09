from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text
from app.database import Base
from typing import TYPE_CHECKING

#Для того шоб не було circular import
if TYPE_CHECKING:
    from .booking import Booking
    from .availability_block import AvailabilityBlock

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(nullable=False) # Ціна (наприклад, за годину)
    minimum_duration_hours: Mapped[int] = mapped_column(nullable=False)
    bookings: Mapped[list["Booking"]] = relationship(back_populates="service")

    availability_blocks: Mapped[list["AvailabilityBlock"]] = relationship(
        back_populates="service"
    )