from fastapi import APIRouter, Depends

from app.schemas import TokenIdentity
from app.security import get_current_identity


router = APIRouter(
    prefix="/api/v1",
    tags=["Identity"],
)


@router.get(
    "/whoami",
    response_model=TokenIdentity,
)
async def whoami(
    identity: TokenIdentity = Depends(get_current_identity),
):
    return identity
