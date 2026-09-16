import asyncio

from sqlalchemy import select

from app.database import async_session_maker
from app.enums import ServiceBookingType
from app.models.service import Service

SERVICES = [
    {
        "name": "Лазня / Баня",
        "description": None,
        "price": None,
        "booking_type": ServiceBookingType.hourly.value,
        "minimum_duration_hours": 3,
        "minimum_duration_days": None,
    },
    {
        "name": "Чан на дровах",
        "description": None,
        "price": None,
        "booking_type": ServiceBookingType.hourly.value,
        "minimum_duration_hours": 3,
        "minimum_duration_days": None,
    },
    {
        "name": "Оренда кімнат",
        "description": None,
        "price": None,
        "booking_type": ServiceBookingType.daily.value,
        "minimum_duration_hours": None,
        "minimum_duration_days": 1,
    },
    {
        "name": "Оренда приміщення + кухня",
        "description": None,
        "price": None,
        "booking_type": ServiceBookingType.phone_only.value,
        "minimum_duration_hours": None,
        "minimum_duration_days": None,
    },
]


async def seed_services() -> None:
    async with async_session_maker() as session:
        for service_data in SERVICES:
            result = await session.execute(
                select(Service).where(Service.name == service_data["name"])
            )

            service = result.scalars().first()

            if service is None:
                service = Service(**service_data)
                session.add(service)

                print(f"Created service: {service_data['name']}")
            else:
                service.description = service_data["description"]
                service.price = service_data["price"]
                service.booking_type = service_data["booking_type"]
                service.minimum_duration_hours = service_data["minimum_duration_hours"]
                service.minimum_duration_days = service_data["minimum_duration_days"]

                print(f"Updated service: {service_data['name']}")

        await session.commit()


async def main() -> None:
    await seed_services()


if __name__ == "__main__":
    asyncio.run(main())
