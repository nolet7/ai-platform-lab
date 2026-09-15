from uuid import uuid4

from sqlalchemy.orm import Session

from .db_models import (
    AuditEventRecord,
    DeploymentRequestRecord,
)
from .models import DeploymentRequest
from .security import Principal


def create_deployment_with_audit(
    db: Session,
    request: DeploymentRequest,
    principal: Principal,
) -> DeploymentRequestRecord:

    request_id = uuid4()
    event_id = uuid4()

    deployment = DeploymentRequestRecord(
        request_id=request_id,
        tenant_id=request.tenant_id,
        model_name=request.model_name,
        model_version=request.model_version,
        environment=request.environment,
        status="accepted",
        requested_by=principal.username,
    )

    audit_event = AuditEventRecord(
        event_id=event_id,
        request_id=request_id,
        event_type="deployment.requested",
        actor=principal.username,
        tenant_id=request.tenant_id,
        event_data={
            "model_name": request.model_name,
            "model_version": request.model_version,
            "environment": request.environment,
            "status": "accepted",
        },
    )

    try:
        db.add(deployment)

        # Flush deployment first so the request_id exists
        # before inserting the foreign-key audit event.
        db.flush()

        db.add(audit_event)

        # Both records commit as one transaction.
        db.commit()

        db.refresh(deployment)

        return deployment

    except Exception:
        db.rollback()
        raise
