from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Створюємо асинхронний рушій (engine)
# echo=True дозволить бачити SQL-запити в консолі (дуже корисно при розробці)
engine = create_async_engine(settings.database_url, echo=True)

# Фабрика для створення сесій бази даних
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовий клас, від якого будуть успадковуватися всі наші моделі
class Base(DeclarativeBase):
    pass