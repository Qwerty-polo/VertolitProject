from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class AvailabilityBlockCreate(BaseModel):
    service_id: int
    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def validate_dates(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be later than starts_at")

        return self


class AvailabilityBlockResponse(AvailabilityBlockCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
