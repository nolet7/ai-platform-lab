import logging
from uuid import UUID

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
    ApprovalDecision,
    DeploymentAccepted,
    DeploymentRequest,
    DeploymentStatus,
)
from .repository import (
    DeploymentNotFound,
    InvalidStateTransition,
    SelfApprovalDenied,
    TenantAccessDenied,
    create_deployment_with_audit,
    decide_deployment,
    get_deployment,
    submit_for_approval,
)
from .security import (
    Principal,
    get_current_principal,
    require_any_role,
)


logger = logging.getLogger(__name__)


app = FastAPI(
    title="AI Platform Control API",
    version="0.4.0",
    description=(
        "Enterprise control API for AI/ML deployments"
    ),
)


def deployment_response(
    deployment,
) -> DeploymentStatus:

    return DeploymentStatus(
        request_id=str(
            deployment.request_id
        ),
        status=deployment.status,
        execution_status=(
            deployment.execution_status
        ),
        execution_message=(
            deployment.execution_message
        ),
        tenant_id=deployment.tenant_id,
        model_name=deployment.model_name,
        model_version=deployment.model_version,
        environment=deployment.environment,
        requested_by=deployment.requested_by,
        decision_by=deployment.decision_by,
        decision_reason=(
            deployment.decision_reason
        ),
    )


def translate_workflow_error(
    error: Exception,
) -> None:

    if isinstance(
        error,
        DeploymentNotFound,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment request not found",
        )

    if isinstance(
        error,
        TenantAccessDenied,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant access denied",
        )

    if isinstance(
        error,
        SelfApprovalDenied,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Requester cannot approve or reject "
                "their own deployment"
            ),
        )

    if isinstance(
        error,
        InvalidStateTransition,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )

    raise error


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
            status_code=503,
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
    if (
        "platform-admin" not in principal.roles
        and request.tenant_id
        != principal.tenant_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Tenant access denied",
        )

    try:
        deployment = (
            create_deployment_with_audit(
                db=db,
                request=request,
                principal=principal,
            )
        )

    except SQLAlchemyError:
        logger.exception(
            "Deployment creation failed"
        )

        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )

    return DeploymentAccepted(
        request_id=str(
            deployment.request_id
        ),
        status=deployment.status,
        execution_status=(
            deployment.execution_status
        ),
        tenant_id=deployment.tenant_id,
        model_name=deployment.model_name,
        model_version=deployment.model_version,
        environment=deployment.environment,
        requested_by=deployment.requested_by,
    )


@app.post(
    "/deployments/{request_id}/submit",
    response_model=DeploymentStatus,
)
def submit_deployment(
    request_id: UUID,

    principal: Principal = Depends(
        require_any_role(
            "data-scientist",
            "ml-engineer",
        )
    ),

    db: Session = Depends(get_db),
):
    try:
        deployment = submit_for_approval(
            db=db,
            request_id=request_id,
            principal=principal,
        )

        return deployment_response(
            deployment
        )

    except (
        DeploymentNotFound,
        TenantAccessDenied,
        InvalidStateTransition,
    ) as error:
        translate_workflow_error(error)

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )


@app.post(
    "/deployments/{request_id}/decision",
    response_model=DeploymentStatus,
)
def approval_decision(
    request_id: UUID,
    decision: ApprovalDecision,

    principal: Principal = Depends(
        require_any_role(
            "approver",
        )
    ),

    db: Session = Depends(get_db),
):
    try:
        deployment = decide_deployment(
            db=db,
            request_id=request_id,
            principal=principal,
            decision=decision,
        )

        return deployment_response(
            deployment
        )

    except (
        DeploymentNotFound,
        TenantAccessDenied,
        InvalidStateTransition,
        SelfApprovalDenied,
    ) as error:
        translate_workflow_error(error)

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )


@app.get(
    "/deployments/{request_id}",
    response_model=DeploymentStatus,
)
def read_deployment(
    request_id: UUID,

    principal: Principal = Depends(
        require_any_role(
            "viewer",
            "data-scientist",
            "ml-engineer",
            "platform-engineer",
            "approver",
        )
    ),

    db: Session = Depends(get_db),
):
    try:
        deployment = get_deployment(
            db=db,
            request_id=request_id,
            principal=principal,
        )

        return deployment_response(
            deployment
        )

    except (
        DeploymentNotFound,
        TenantAccessDenied,
    ) as error:
        translate_workflow_error(error)
