from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class BookingCreate(BaseModel):
    service_id: int = Field(
        description="ID послуги",
        examples=[1],
    )

    customer_name: str = Field(
        min_length=2,
        max_length=100,
        description="Ім'я клієнта",
        examples=["Ivan"],
    )

    customer_phone: str = Field(
        min_length=7,
        max_length=30,
        description="Телефон клієнта",
        examples=["+380991112233"],
    )

    starts_at: datetime | None = Field(
        default=None,
        description=("Дата і час початку для погодинного бронювання"),
    )

    check_in_date: date | None = Field(
        default=None,
        description="Дата заїзду для подобового бронювання",
    )

    check_out_date: date | None = Field(
        default=None,
        description="Дата виїзду для подобового бронювання",
    )

    guests: int = Field(
        ge=1,
        description="Кількість гостей",
        examples=[4],
    )

    comment: str | None = Field(
        default=None,
        max_length=500,
        description="Коментар до бронювання",
    )

    duration_hours: int | None = Field(
        default=None,
        ge=1,
        description=("Тривалість погодинного бронювання"),
    )

    @field_validator("starts_at")
    @classmethod
    def validate_starts_at(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is None:
            return value

        if value.tzinfo is None:
            raise ValueError("Timezone is required")

        if value <= datetime.now(UTC):
            raise ValueError("Booking start time must be in the future")

        return value


class BookingStatus(StrEnum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class BookingResponse(BaseModel):
    id: int
    service_id: int
    customer_name: str
    customer_phone: str
    starts_at: datetime
    ends_at: datetime
    guests: int
    status: BookingStatus
    comment: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BookingStatusUpdate(BaseModel):
    status: BookingStatus
