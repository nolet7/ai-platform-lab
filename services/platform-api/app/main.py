import logging
from pathlib import Path
from uuid import UUID

from fastapi import (
    Depends,
    Query,
    FastAPI,
    HTTPException,
    status,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import (
    database_is_ready,
    get_db,
)
from .model_catalog import load_model_catalog
from .models import (
    ApprovalDecision,
    AuditEventView,
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
    list_deployments,
    get_audit_events,
    get_job_result,
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
    version="0.4.9",
    description=(
        "Enterprise control API for AI/ML deployments"
    ),
)


@app.middleware("http")
async def prevent_protected_response_caching(request, call_next):
    response = await call_next(request)
    if request.url.path in {"/me", "/catalog/models"} or (
        request.url.path.startswith("/deployments")
    ):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
    return response


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


@app.get("/catalog/models")
def model_catalog(
    principal: Principal = Depends(get_current_principal),
):
    del principal
    public_fields = (
        "name", "display_name", "description", "owner", "environments",
        "minimum_macro_f1",
    )
    return [
        {field: model[field] for field in public_fields}
        for model in load_model_catalog().values()
    ]


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

        response = deployment_response(deployment)
        response.orchestration = get_job_result(db, request_id)
        return response

    except (
        DeploymentNotFound,
        TenantAccessDenied,
    ) as error:
        translate_workflow_error(error)



@app.get("/deployments", response_model=list[DeploymentStatus])
def read_deployments(
    limit: int = Query(default=50, ge=1, le=100),
    principal: Principal = Depends(require_any_role(
        "viewer", "data-scientist", "ml-engineer", "platform-engineer", "approver"
    )),
    db: Session = Depends(get_db),
):
    try:
        records = list_deployments(db, principal, limit)
        return [deployment_response(record) for record in records]
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.get("/deployments/{request_id}/audit", response_model=list[AuditEventView])
def read_audit(
    request_id: UUID,
    principal: Principal = Depends(require_any_role(
        "viewer", "data-scientist", "ml-engineer", "platform-engineer", "approver"
    )),
    db: Session = Depends(get_db),
):
    try:
        events = get_audit_events(db, request_id, principal)
        return [
            AuditEventView(
                event_type=event.event_type,
                actor=event.actor,
                tenant_id=event.tenant_id,
                event_data=event.event_data,
                created_at=event.created_at.isoformat(),
            )
            for event in events
        ]
    except (DeploymentNotFound, TenantAccessDenied) as error:
        translate_workflow_error(error)
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable")


PORTAL_DIR = Path(__file__).resolve().parent / "portal"
app.mount("/portal/assets", StaticFiles(directory=PORTAL_DIR), name="portal-assets")


@app.get("/portal")
@app.get("/portal/")
def portal_home():
    return FileResponse(
        PORTAL_DIR / "index.html",
        headers={
            "Content-Security-Policy": (
                "default-src 'none'; script-src 'self'; style-src 'self'; "
                "connect-src 'self' https://keycloak.ai-platform.local; "
                "form-action 'none'; base-uri 'none'; frame-ancestors 'none'"
            ),
            "Cache-Control": "no-store",
        },
    )
