from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text
from app.database import Base

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(nullable=False) # Ціна (наприклад, за годину)