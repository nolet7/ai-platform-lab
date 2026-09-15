from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/live")
async def liveness():
    return {
        "status": "alive"
    }


@router.get("/ready")
async def readiness():
    return {
        "status": "ready"
    }
