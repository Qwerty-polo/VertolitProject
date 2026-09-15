from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

#Для того шоб не було circular import
if TYPE_CHECKING:
    from .service import Service

class Booking(Base):
    __tablename__ = 'bookings'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False, index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey('services.id'), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    guests: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False,default="pending")
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reminder_sent: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    service: Mapped["Service"] = relationship(back_populates="bookings")

    __table_args__ = (
        ExcludeConstraint(
            (service_id, "="),
            (
                func.tstzrange(
                    starts_at,
                    ends_at,
                    "[)",
                ),
                "&&",
            ),
            where=text(
                "status = 'confirmed'"
            ),
            using="gist",
            name=(
                "exclude_overlapping_"
                "confirmed_bookings"
            ),
        ),
    )