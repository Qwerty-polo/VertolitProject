from fastapi import APIRouter, Depends
from sqlalchemy import select
from typing import List

from app.models.service import Service
from app.schemas.service import ServiceResponse, ServiceCreate
from app.dependencies import SessionDep
# Створюємо роутер
router = APIRouter(prefix="/services", tags=["Services"])


# Сам endpoint
@router.get("/", response_model=List[ServiceResponse])
async def get_all_services(db: SessionDep):
    # Робимо асинхронний запит до БД: SELECT * FROM services;
    result = await db.execute(select(Service))
    # Витягуємо всі знайдені рядки
    services = result.scalars().all()
    return services


@router.post("/", response_model=ServiceResponse)
async def create_service(service_in: ServiceCreate,
                         db: SessionDep):
    service = Service(**service_in.model_dump())

    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service