from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator
from enum import Enum



class BookingCreate(BaseModel):
    service_id: int = Field(
        description="ID послуги",
        examples=[1],
    )

    customer_name: str = Field(
        description="Ім'я клієнта",
        examples=["Ivan"],
    )

    customer_phone: str = Field(
        description="Номер телефону клієнта",
        examples=["+380991112233"],
    )

    starts_at: datetime = Field(
        description=(
            "Дата і час початку бронювання у форматі ISO 8601 "
            "з timezone. Наприклад: 2026-09-20T13:00:00+03:00"
        ),
        examples=["2026-09-20T13:00:00+03:00"],
    )

    guests: int = Field(
        ge=1,
        description="Кількість гостей. Мінімум 1",
        examples=[4],
    )

    comment: str | None = Field(
        default=None,
        description="Необов'язковий коментар до бронювання",
        examples=["Birthday"],
    )

    duration_hours: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Тривалість бронювання в годинах. "
            "Якщо не передати, буде використана мінімальна "
            "тривалість цієї послуги"
        ),
        examples=[3],
    )

    @field_validator("starts_at")
    @classmethod
    def validate_starts_at(cls, value: datetime):
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