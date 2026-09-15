from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.availability_blocks import router as availability_blocks_router
from app.api.v1.bookings import router as booking_router
from app.api.v1.services import router as services_router
from app.exception_handlers import (
    global_exception_handler,
    validation_exception_handler,
)
from app.logging_config import setup_logging
from app.middleware.rate_limit import rate_limit_middleware
from app.middleware.request_logging import request_logging_middleware
from app.api.v1.health import router as health_router

from app.api.v1.admin import router as admin_router

setup_logging()

app = FastAPI(
    title="Vertolit Complex API",
    description="API для комплексу відпочинку",
    version="0.1.0",
)


app.middleware("http")(rate_limit_middleware)
app.middleware("http")(request_logging_middleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    Exception,
    global_exception_handler,
)


app.include_router(
    services_router,
    prefix="/api/v1",
)

app.include_router(
    admin_router,
    prefix="/api/v1",
)

app.include_router(
    booking_router,
    prefix="/api/v1",
)

app.include_router(
    availability_blocks_router,
    prefix="/api/v1",
)

app.include_router(
    health_router,
    prefix="/api/v1",
)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Hello, World! Vertolit API is running",
    }