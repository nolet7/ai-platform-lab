from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db_models import (
    AuditEventRecord,
    DeploymentRequestRecord,
)
from .models import (
    ApprovalDecision,
    DeploymentRequest,
)
from .security import Principal


class DeploymentNotFound(Exception):
    pass


class TenantAccessDenied(Exception):
    pass


class InvalidStateTransition(Exception):
    pass


class SelfApprovalDenied(Exception):
    pass


def _check_tenant(
    deployment: DeploymentRequestRecord,
    principal: Principal,
) -> None:
    if "platform-admin" in principal.roles:
        return

    if deployment.tenant_id != principal.tenant_id:
        raise TenantAccessDenied


def _get_for_update(
    db: Session,
    request_id: UUID,
) -> DeploymentRequestRecord:

    deployment = db.execute(
        select(DeploymentRequestRecord)
        .where(
            DeploymentRequestRecord.request_id
            == request_id
        )
        .with_for_update()
    ).scalar_one_or_none()

    if deployment is None:
        raise DeploymentNotFound

    return deployment


def _audit(
    db: Session,
    deployment: DeploymentRequestRecord,
    principal: Principal,
    event_type: str,
    event_data: dict,
) -> None:

    db.add(
        AuditEventRecord(
            event_id=uuid4(),
            request_id=deployment.request_id,
            event_type=event_type,
            actor=principal.username,
            tenant_id=deployment.tenant_id,
            event_data=event_data,
        )
    )


def create_deployment_with_audit(
    db: Session,
    request: DeploymentRequest,
    principal: Principal,
) -> DeploymentRequestRecord:

    deployment = DeploymentRequestRecord(
        request_id=uuid4(),
        tenant_id=request.tenant_id,
        model_name=request.model_name,
        model_version=request.model_version,
        environment=request.environment,
        status="accepted",
        requested_by=principal.username,
        requested_by_sub=principal.subject,
    )

    try:
        db.add(deployment)
        db.flush()

        _audit(
            db=db,
            deployment=deployment,
            principal=principal,
            event_type="deployment.requested",
            event_data={
                "model_name": request.model_name,
                "model_version": request.model_version,
                "environment": request.environment,
                "status": "accepted",
            },
        )

        db.commit()
        db.refresh(deployment)

        return deployment

    except Exception:
        db.rollback()
        raise


def submit_for_approval(
    db: Session,
    request_id: UUID,
    principal: Principal,
) -> DeploymentRequestRecord:

    try:
        deployment = _get_for_update(
            db,
            request_id,
        )

        _check_tenant(
            deployment,
            principal,
        )

        if deployment.status != "accepted":
            raise InvalidStateTransition(
                f"Cannot submit request in "
                f"{deployment.status} state"
            )

        deployment.status = "pending_approval"
        deployment.updated_at = datetime.now(
            timezone.utc
        )

        _audit(
            db=db,
            deployment=deployment,
            principal=principal,
            event_type=(
                "deployment.submitted_for_approval"
            ),
            event_data={
                "previous_status": "accepted",
                "new_status": "pending_approval",
            },
        )

        db.commit()
        db.refresh(deployment)

        return deployment

    except Exception:
        db.rollback()
        raise


def decide_deployment(
    db: Session,
    request_id: UUID,
    principal: Principal,
    decision: ApprovalDecision,
) -> DeploymentRequestRecord:

    try:
        deployment = _get_for_update(
            db,
            request_id,
        )

        _check_tenant(
            deployment,
            principal,
        )

        if deployment.status != "pending_approval":
            raise InvalidStateTransition(
                f"Cannot decide request in "
                f"{deployment.status} state"
            )

        if (
            deployment.requested_by_sub
            and deployment.requested_by_sub
            == principal.subject
        ):
            raise SelfApprovalDenied

        if (
            not deployment.requested_by_sub
            and deployment.requested_by
            == principal.username
        ):
            raise SelfApprovalDenied

        deployment.status = decision.decision
        deployment.decision_by = principal.username
        deployment.decision_by_sub = principal.subject
        deployment.decision_reason = decision.reason
        deployment.updated_at = datetime.now(
            timezone.utc
        )

        _audit(
            db=db,
            deployment=deployment,
            principal=principal,
            event_type=(
                f"deployment.{decision.decision}"
            ),
            event_data={
                "previous_status": (
                    "pending_approval"
                ),
                "new_status": decision.decision,
                "reason": decision.reason,
            },
        )

        db.commit()
        db.refresh(deployment)

        return deployment

    except Exception:
        db.rollback()
        raise


def get_deployment(
    db: Session,
    request_id: UUID,
    principal: Principal,
) -> DeploymentRequestRecord:

    deployment = db.get(
        DeploymentRequestRecord,
        request_id,
    )

    if deployment is None:
        raise DeploymentNotFound

    _check_tenant(
        deployment,
        principal,
    )

    return deployment
