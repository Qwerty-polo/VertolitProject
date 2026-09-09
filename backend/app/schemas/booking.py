from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator
from enum import Enum



class BookingCreate(BaseModel):
    service_id: int
    customer_name: str
    customer_phone: str
    starts_at: datetime
    guests: int = Field (ge=1)
    comment: str | None = None
    duration_hours: int | None = Field(default=None, ge=1)

    @field_validator("starts_at")
    @classmethod
    def validate_starts_at(cls, value: datetime):
        if value.tzinfo is None:
            raise ValueError("Потрібен час")

        if value <= datetime.now(timezone.utc):
            raise ValueError("Ці дати вже не доступні")

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