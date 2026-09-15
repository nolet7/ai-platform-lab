import logging

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    status,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .database import (
    database_is_ready,
    get_db,
)
from .models import (
    DeploymentAccepted,
    DeploymentRequest,
)
from .repository import create_deployment_with_audit
from .security import (
    Principal,
    get_current_principal,
    require_any_role,
)


logger = logging.getLogger(__name__)


app = FastAPI(
    title="AI Platform Control API",
    version="0.2.0",
    description=(
        "Enterprise control API for AI/ML deployments"
    ),
)


@app.get("/health/live")
async def health_live():
    return {
        "status": "healthy",
    }


@app.get("/health/ready")
def health_ready():
    try:
        database_is_ready()

    except SQLAlchemyError:
        logger.exception(
            "Database readiness check failed"
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not-ready",
                "database": "unavailable",
            },
        )

    return {
        "status": "ready",
        "database": "ready",
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
def create_deployment(
    request: DeploymentRequest,

    principal: Principal = Depends(
        require_any_role(
            "data-scientist",
            "ml-engineer",
        )
    ),

    db: Session = Depends(get_db),
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

    try:
        deployment = create_deployment_with_audit(
            db=db,
            request=request,
            principal=principal,
        )

    except SQLAlchemyError:
        logger.exception(
            "Failed to persist deployment request"
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": (
                    "Control-plane database unavailable"
                )
            },
        )

    return DeploymentAccepted(
        request_id=str(deployment.request_id),
        status=deployment.status,
        tenant_id=deployment.tenant_id,
        model_name=deployment.model_name,
        model_version=deployment.model_version,
        environment=deployment.environment,
        requested_by=deployment.requested_by,
    )
