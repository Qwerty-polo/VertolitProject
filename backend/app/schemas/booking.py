from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator
from enum import Enum



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

    starts_at: datetime = Field(
        description="Дата і час початку бронювання з timezone",
        examples=["2026-09-20T13:00:00+03:00"],
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
        examples=["Birthday"],
    )

    duration_hours: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Тривалість бронювання у годинах. "
            "Якщо не передано — використовується мінімальна "
            "тривалість послуги."
        ),
        examples=[3],
    )

    @field_validator("starts_at")
    @classmethod
    def validate_starts_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError(
                "Timezone is required. "
                "Example: 2026-09-20T13:00:00+03:00"
            )

        if value <= datetime.now(timezone.utc):
            raise ValueError(
                "Booking start time must be in the future"
            )

        return value



class BookingStatus(str, Enum):
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