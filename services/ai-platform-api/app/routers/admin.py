from fastapi import (
    APIRouter,
    Depends,
)

from app.schemas import TokenIdentity
from app.security import require_roles


router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Administration"],
)


@router.get("/status")
async def admin_status(
    identity: TokenIdentity = Depends(
        require_roles(
            "platform-admin"
        )
    ),
):
    return {
        "status": "authorized",
        "role": "platform-admin",
        "requested_by":
            identity.username,
    }
