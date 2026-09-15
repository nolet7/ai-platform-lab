from uuid import uuid4

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    status,
)

from .models import (
    DeploymentAccepted,
    DeploymentRequest,
)

from .security import (
    Principal,
    get_current_principal,
    require_any_role,
)


app = FastAPI(
    title="AI Platform Control API",
    version="0.1.1",
    description="Enterprise control API for AI/ML deployments",
)


@app.get("/health/live")
async def health_live():
    return {
        "status": "healthy"
    }


@app.get("/health/ready")
async def health_ready():
    return {
        "status": "ready"
    }


@app.get("/me")
async def who_am_i(
    principal: Principal = Depends(
        get_current_principal
    ),
):
    return principal


@app.post(
    "/deployments",
    response_model=DeploymentAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_deployment(
    request: DeploymentRequest,
    principal: Principal = Depends(
        require_any_role(
            "data-scientist",
            "ml-engineer",
        )
    ),
):
    is_platform_admin = (
        "platform-admin" in principal.roles
    )

    if (
        not is_platform_admin
        and request.tenant_id != principal.tenant_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Tenant access denied",
                "token_tenant": principal.tenant_id,
                "requested_tenant": request.tenant_id,
            },
        )

    deployment_request_id = str(uuid4())

    return DeploymentAccepted(
        request_id=deployment_request_id,
        status="accepted",
        tenant_id=request.tenant_id,
        model_name=request.model_name,
        model_version=request.model_version,
        environment=request.environment,
        requested_by=principal.username,
    )
