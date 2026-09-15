from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.enums import ServiceBookingType


class ServiceBase(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    description: str | None = None

    price: int | None = Field(
        default=None,
        ge=0,
    )

    booking_type: ServiceBookingType = (
        ServiceBookingType.hourly
    )

    minimum_duration_hours: int | None = Field(
        default=None,
        ge=1,
    )

    minimum_duration_days: int | None = Field(
        default=None,
        ge=1,
    )

    @model_validator(mode="after")
    def validate_booking_type(self) -> Self:
        if self.booking_type == ServiceBookingType.hourly:
            if self.minimum_duration_hours is None:
                raise ValueError(
                    "Hourly service requires "
                    "minimum_duration_hours"
                )

            if self.minimum_duration_days is not None:
                raise ValueError(
                    "Hourly service cannot have "
                    "minimum_duration_days"
                )

        elif self.booking_type == ServiceBookingType.daily:
            if self.minimum_duration_days is None:
                raise ValueError(
                    "Daily service requires "
                    "minimum_duration_days"
                )

            if self.minimum_duration_hours is not None:
                raise ValueError(
                    "Daily service cannot have "
                    "minimum_duration_hours"
                )

        elif self.booking_type == ServiceBookingType.phone_only:
            if (
                self.minimum_duration_hours is not None
                or self.minimum_duration_days is not None
            ):
                raise ValueError(
                    "Phone-only service cannot have "
                    "minimum duration"
                )

        return self


class ServiceResponse(ServiceBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True
    )


class ServiceCreate(ServiceBase):
    pass