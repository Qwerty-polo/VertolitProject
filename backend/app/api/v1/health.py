from fastapi import APIRouter
from sqlalchemy import text

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
        await db.execute(text("SELECT 1"))
    except Exception:
        database_status = "error"

    try:
        await redis_client.ping()
    except Exception:
        redis_status = "error"

    overall_status = (
        "ok"
        if database_status == "ok"
        and redis_status == "ok"
        else "degraded"
    )

    return {
        "status": overall_status,
        "database": database_status,
        "redis": redis_status,
    }