from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select

from app.cache import invalidate_availability_cache
from app.dependencies import SessionDep
from app.models import AvailabilityBlock
from app.models.service import Service
from app.schemas.availability_block import (
    AvailabilityBlockCreate,
    AvailabilityBlockResponse,
)
from app.security.admin_auth import require_admin

router = APIRouter(
    prefix="/availability-blocks",
    tags=["Availability Blocks"],
)


@router.post(
    "/",
    response_model=AvailabilityBlockResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
    responses={
        404: {
            "description": "Service not found",
            "content": {
                "application/json": {"example": {"detail": "Service not found"}}
            },
        }
    },
)
async def create_availability_block(
    availability_block: AvailabilityBlockCreate,
    db: SessionDep,
):
    result = await db.execute(
        select(Service).where(Service.id == availability_block.service_id)
    )

    service = result.scalar_one_or_none()

    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    block = AvailabilityBlock(**availability_block.model_dump())

    db.add(block)

    await db.commit()
    await db.refresh(block)

    await invalidate_availability_cache(
        service_id=block.service_id,
        starts_at=block.starts_at,
        ends_at=block.ends_at,
    )

    return block


@router.get(
    "/",
    response_model=list[AvailabilityBlockResponse],
    dependencies=[Depends(require_admin)],
)
async def get_availability_blocks(
    db: SessionDep,
):
    result = await db.execute(select(AvailabilityBlock))

    return result.scalars().all()
