from datetime import datetime
from pydantic import BaseModel, ConfigDict
from enum import Enum

class BookingCreate(BaseModel):
    service_id: int
    customer_name: str
    customer_phone: str
    starts_at: datetime
    guests: int
    comment: str | None = None
    duration_hours: int | None = None

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