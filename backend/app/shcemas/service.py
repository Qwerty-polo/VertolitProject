from pydantic import BaseModel, ConfigDict

class ServiceBase(BaseModel):
    name: str
    description: str | None = None
    price: int

class ServiceResponse(ServiceBase):
    id: int

    # Цей конфіг дозволяє Pydantic читати дані прямо з об'єктів SQLAlchemy
    model_config = ConfigDict(from_attributes=True)