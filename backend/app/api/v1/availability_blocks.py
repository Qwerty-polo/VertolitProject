from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.models import AvailabilityBlock
from app.models.service import Service
from app.schemas.availability_block import AvailabilityBlockCreate, AvailabilityBlockResponse

from app.dependencies import SessionDep

router = APIRouter(prefix="/availability-blocks", tags=["Availability Blocks"])

@router.post(
    "/",
    response_model=AvailabilityBlockResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_availability_block(
        availability_block: AvailabilityBlockCreate,
        db: SessionDep
):
    result = await db.execute(select(Service).where(Service.id == availability_block.service_id))

    service = result.scalar_one_or_none()

    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Service not found")

    block = AvailabilityBlock(**availability_block.model_dump())

    db.add(block)
    await db.commit()
    await db.refresh(block)
    return block


@router.get("/", response_model=list[AvailabilityBlockResponse])
async def get_availability_blocks(db: SessionDep):
    result = await db.execute(
        select(AvailabilityBlock)
    )

    blocks = result.scalars().all()

    return blocks