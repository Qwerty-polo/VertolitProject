from enum import StrEnum


class ServiceBookingType(StrEnum):
    hourly = "hourly"
    daily = "daily"
    phone_only = "phone_only"
