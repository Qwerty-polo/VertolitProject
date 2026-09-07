from datetime import datetime
from pydantic import BaseModel, ConfigDict

class BookingCreate(BaseModel):
    service_id: int
    customer_name: str
    customer_phone: str
    starts_at: datetime
    guests: int
    comment: str | None = None


class BookingResponse(BaseModel):
    id: int
    service_id: int
    customer_name: str
    customer_phone: str
    starts_at: datetime
    ends_at: datetime
    guests: int
    status: str
    comment: str | None = None

    model_config = ConfigDict(from_attributes=True)