from fastapi import FastAPI
from app.config import settings
from app.api.v1.services import router as services_router
from app.api.v1.bookings import router as booking_router
app = FastAPI(
    title="Vertolit Complex API",
    description="API для комплексу відпочинку",
    version="0.1.0",
)

app.include_router(services_router, prefix="/api/v1")
app.include_router(booking_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"status": "ok",
            "message": "Hello, World! Vertolit API is running"}