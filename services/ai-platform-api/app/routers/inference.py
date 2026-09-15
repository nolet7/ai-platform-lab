from fastapi import APIRouter, Depends

from app.schemas import (
    InferenceRequest,
    InferenceResponse,
    TokenIdentity,
)
from app.security import require_roles


router = APIRouter(
    prefix="/api/v1",
    tags=["Inference"],
)


@router.post(
    "/inference",
    response_model=InferenceResponse,
)
async def inference(
    request: InferenceRequest,
    identity: TokenIdentity = Depends(
        require_roles(
            "inference-client",
            "platform-admin",
        )
    ),
):
    """
    Phase 2L authorization test.

    Real model invocation will replace this placeholder
    in a later phase.
    """

    return InferenceResponse(
        status="authorized",
        model_name=request.model_name,
        requested_by=identity.username,
        result={
            "prediction": "phase-2l-placeholder",
            "authorization": "RBAC passed",
        },
    )
