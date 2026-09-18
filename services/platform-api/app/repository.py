from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db_models import (
    AuditEventRecord,
    DeploymentJobRecord,
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
        execution_status="not_started",
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

        if decision.decision == "approved":
            deployment.execution_status = "queued"
            deployment.execution_message = (
                "Approved and queued for "
                "deployment orchestration"
            )

            job = DeploymentJobRecord(
                job_id=uuid4(),
                request_id=deployment.request_id,
                queue_name="deployments",
                status="queued",
                attempt_count=0,
                max_attempts=3,
            )

            db.add(job)

            _audit(
                db=db,
                deployment=deployment,
                principal=principal,
                event_type=(
                    "deployment.execution.queued"
                ),
                event_data={
                    "execution_status": "queued",
                    "queue_name": "deployments",
                    "job_id": str(job.job_id),
                },
            )

        else:
            deployment.execution_status = (
                "not_started"
            )
            deployment.execution_message = (
                "Deployment rejected before execution"
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



def list_deployments(db: Session, principal: Principal, limit: int = 50):
    query = select(DeploymentRequestRecord)
    if "platform-admin" not in principal.roles:
        query = query.where(DeploymentRequestRecord.tenant_id == principal.tenant_id)
    return list(db.scalars(query.order_by(DeploymentRequestRecord.created_at.desc()).limit(limit)))


def get_audit_events(db: Session, request_id: UUID, principal: Principal):
    get_deployment(db, request_id, principal)
    return list(db.scalars(
        select(AuditEventRecord)
        .where(AuditEventRecord.request_id == request_id)
        .order_by(AuditEventRecord.created_at.asc())
    ))


def get_job_result(db: Session, request_id: UUID):
    job = db.scalar(
        select(DeploymentJobRecord).where(DeploymentJobRecord.request_id == request_id)
    )
    if job is None:
        return None
    return {
        "job_status": job.status,
        "attempt_count": job.attempt_count,
        "result": job.result_payload,
    }
