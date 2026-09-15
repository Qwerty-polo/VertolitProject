from fastapi import APIRouter
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies import SessionDep
from app.redis import redis_client

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/")
async def healthcheck(
    db: SessionDep,
):
    database_status = "ok"
    redis_status = "ok"

    try:
        await db.execute(
            text("SELECT 1")
        )
    except SQLAlchemyError:
        database_status = "error"

    try:
        await redis_client.ping()
    except RedisError:
        redis_status = "error"

    if database_status == "error":
        overall_status = "unhealthy"
        status_code = 503

    elif redis_status == "error":
        overall_status = "degraded"
        status_code = 200

    else:
        overall_status = "ok"
        status_code = 200

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "database": database_status,
            "redis": redis_status,
        },
    )