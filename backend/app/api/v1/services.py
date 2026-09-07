from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Annotated

from app.database import async_session_maker
from app.models.service import Service
from app.schemas.service import ServiceResponse

# Створюємо роутер
router = APIRouter(prefix="/services", tags=["Services"])

# Функція-залежність (Dependency) для отримання сесії бази даних
async def get_db():
    async with async_session_maker() as session:
        yield session

SessionDep = Annotated[
    AsyncSession,
    Depends(get_db)
]

# Сам endpoint
@router.get("/", response_model=List[ServiceResponse])
async def get_all_services(db: SessionDep):
    # Робимо асинхронний запит до БД: SELECT * FROM services;
    result = await db.execute(select(Service))
    # Витягуємо всі знайдені рядки
    services = result.scalars().all()
    return services