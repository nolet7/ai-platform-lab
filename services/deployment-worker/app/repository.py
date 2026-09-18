from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import UUID, uuid4

from sqlalchemy import (
    and_,
    or_,
    select,
)

from .config import (
    DISPATCH_LEASE_SECONDS,
    RETRY_DELAY_SECONDS,
)
from .database import SessionLocal
from .models import (
    AuditEventRecord,
    DeploymentJobRecord,
    DeploymentRequestRecord,
)


SYSTEM_ACTOR = "deployment-orchestrator"


def utcnow():
    return datetime.now(
        timezone.utc
    )


def _audit(
    session,
    deployment,
    event_type,
    event_data,
):
    session.add(
        AuditEventRecord(
            event_id=uuid4(),
            request_id=deployment.request_id,
            event_type=event_type,
            actor=SYSTEM_ACTOR,
            tenant_id=deployment.tenant_id,
            event_data=event_data,
            created_at=utcnow(),
        )
    )


def list_dispatch_candidates(
    limit: int = 25,
) -> list[UUID]:

    now = utcnow()

    retry_cutoff = now - timedelta(
        seconds=RETRY_DELAY_SECONDS
    )

    lease_cutoff = now - timedelta(
        seconds=DISPATCH_LEASE_SECONDS
    )

    with SessionLocal() as session:
        rows = session.execute(
            select(
                DeploymentJobRecord.job_id
            )
            .where(
                or_(
                    DeploymentJobRecord.status
                    == "queued",

                    and_(
                        DeploymentJobRecord.status
                        == "failed",
                        DeploymentJobRecord.attempt_count
                        < DeploymentJobRecord.max_attempts,
                        DeploymentJobRecord.updated_at
                        <= retry_cutoff,
                    ),

                    and_(
                        DeploymentJobRecord.status
                        == "dispatched",
                        or_(
                            DeploymentJobRecord
                            .last_dispatched_at
                            .is_(None),

                            DeploymentJobRecord
                            .last_dispatched_at
                            <= lease_cutoff,
                        ),
                    ),
                )
            )
            .order_by(
                DeploymentJobRecord.created_at
            )
            .limit(limit)
        ).scalars().all()

        return list(rows)


def mark_dispatch_intent(
    job_id: UUID,
) -> bool:

    now = utcnow()

    with SessionLocal() as session:
        try:
            job = session.execute(
                select(DeploymentJobRecord)
                .where(
                    DeploymentJobRecord.job_id
                    == job_id
                )
                .with_for_update()
            ).scalar_one_or_none()

            if job is None:
                return False

            if (
                job.attempt_count
                >= job.max_attempts
            ):
                return False

            deployment = session.get(
                DeploymentRequestRecord,
                job.request_id,
            )

            if (
                deployment is None
                or deployment.status
                != "approved"
            ):
                job.status = "failed"
                job.last_error = (
                    "Deployment is not approved"
                )
                job.updated_at = now

                if deployment:
                    deployment.execution_status = (
                        "failed"
                    )

                session.commit()
                return False

            job.status = "dispatched"
            job.last_dispatched_at = now
            job.updated_at = now

            _audit(
                session=session,
                deployment=deployment,
                event_type=(
                    "deployment.execution.dispatched"
                ),
                event_data={
                    "job_id": str(job.job_id),
                    "attempt_number": (
                        job.attempt_count + 1
                    ),
                },
            )

            session.commit()

            return True

        except Exception:
            session.rollback()
            raise


def mark_dispatch_error(
    job_id: UUID,
    error: str,
):
    now = utcnow()

    with SessionLocal() as session:
        job = session.execute(
            select(DeploymentJobRecord)
            .where(
                DeploymentJobRecord.job_id
                == job_id
            )
            .with_for_update()
        ).scalar_one_or_none()

        if job is None:
            return

        deployment = session.get(
            DeploymentRequestRecord,
            job.request_id,
        )

        job.attempt_count += 1
        job.status = "failed"
        job.last_error = error[:2000]
        job.updated_at = now

        if deployment:
            deployment.execution_status = "failed"
            deployment.execution_message = (
                "Dispatch failed; retry scheduled"
                if job.attempt_count < job.max_attempts
                else "Maximum dispatch attempts exceeded"
            )
            _audit(
                session=session,
                deployment=deployment,
                event_type=(
                    "deployment.execution."
                    "dispatch_failed"
                ),
                event_data={
                    "job_id": str(job.job_id),
                    "error": error[:500],
                },
            )

        session.commit()


def claim_job(
    job_id: UUID,
) -> dict | None:

    now = utcnow()

    with SessionLocal() as session:
        try:
            job = session.execute(
                select(DeploymentJobRecord)
                .where(
                    DeploymentJobRecord.job_id
                    == job_id
                )
                .with_for_update()
            ).scalar_one_or_none()

            if job is None:
                return None

            deployment = session.get(
                DeploymentRequestRecord,
                job.request_id,
            )

            if deployment is None:
                return None

            if job.status in {
                "running",
                "succeeded",
            }:
                return None

            if (
                job.attempt_count
                >= job.max_attempts
            ):
                job.status = "failed"
                deployment.execution_status = (
                    "failed"
                )
                deployment.execution_message = (
                    "Maximum orchestration "
                    "attempts exceeded"
                )
                session.commit()
                return None

            if deployment.status != "approved":
                job.status = "failed"
                job.last_error = (
                    "Deployment is not approved"
                )
                deployment.execution_status = (
                    "failed"
                )
                deployment.execution_message = (
                    "Deployment approval is invalid"
                )
                session.commit()
                return None

            job.attempt_count += 1
            job.status = "running"
            job.started_at = now
            job.updated_at = now
            job.last_error = None

            deployment.execution_status = (
                "running"
            )
            deployment.execution_message = (
                f"Orchestration attempt "
                f"{job.attempt_count} running"
            )

            _audit(
                session=session,
                deployment=deployment,
                event_type=(
                    "deployment.execution.started"
                ),
                event_data={
                    "job_id": str(job.job_id),
                    "attempt": job.attempt_count,
                },
            )

            payload = {
                "job_id": str(job.job_id),
                "request_id": str(
                    deployment.request_id
                ),
                "tenant_id": (
                    deployment.tenant_id
                ),
                "model_name": (
                    deployment.model_name
                ),
                "model_version": (
                    deployment.model_version
                ),
                "environment": (
                    deployment.environment
                ),
                "attempt": (
                    job.attempt_count
                ),
            }

            session.commit()

            return payload

        except Exception:
            session.rollback()
            raise


def complete_job(
    job_id: UUID,
    result_payload: dict,
):
    now = utcnow()

    with SessionLocal() as session:
        job = session.execute(
            select(DeploymentJobRecord)
            .where(
                DeploymentJobRecord.job_id
                == job_id
            )
            .with_for_update()
        ).scalar_one()

        deployment = session.get(
            DeploymentRequestRecord,
            job.request_id,
        )

        if job.status == "succeeded":
            return

        job.status = "succeeded"
        job.result_payload = result_payload
        job.finished_at = now
        job.updated_at = now
        job.last_error = None

        deployment.execution_status = (
            "ready_for_gitops"
        )

        deployment.execution_message = (
            "Orchestration completed; "
            "ready for GitOps generation"
        )

        _audit(
            session=session,
            deployment=deployment,
            event_type=(
                "deployment.execution."
                "ready_for_gitops"
            ),
            event_data={
                "job_id": str(job.job_id),
                "next_action": (
                    "generate_gitops_manifest"
                ),
            },
        )

        session.commit()


def fail_job(
    job_id: UUID,
    error: str,
):
    now = utcnow()

    with SessionLocal() as session:
        job = session.execute(
            select(DeploymentJobRecord)
            .where(
                DeploymentJobRecord.job_id
                == job_id
            )
            .with_for_update()
        ).scalar_one_or_none()

        if job is None:
            return

        deployment = session.get(
            DeploymentRequestRecord,
            job.request_id,
        )

        job.status = "failed"
        job.last_error = error[:2000]
        job.finished_at = now
        job.updated_at = now

        if deployment:
            deployment.execution_status = (
                "failed"
            )

            deployment.execution_message = (
                error[:1000]
            )

            _audit(
                session=session,
                deployment=deployment,
                event_type=(
                    "deployment.execution.failed"
                ),
                event_data={
                    "job_id": str(job.job_id),
                    "attempt_count": (
                        job.attempt_count
                    ),
                    "max_attempts": (
                        job.max_attempts
                    ),
                    "retryable": (
                        job.attempt_count
                        < job.max_attempts
                    ),
                    "error": error[:500],
                },
            )

        session.commit()


def complete_gitops_job(
    job_id: UUID,
    result_payload: dict,
):
    now = utcnow()

    with SessionLocal() as session:
        job = session.execute(
            select(DeploymentJobRecord)
            .where(
                DeploymentJobRecord.job_id
                == job_id
            )
            .with_for_update()
        ).scalar_one()

        deployment = session.get(
            DeploymentRequestRecord,
            job.request_id,
        )

        if job.status == "succeeded":
            return

        job.status = "succeeded"
        job.result_payload = result_payload
        job.finished_at = now
        job.updated_at = now
        job.last_error = None

        deployment.execution_status = (
            "gitops_committed"
        )

        commit_sha = result_payload.get(
            "gitops",
            {},
        ).get(
            "commit_sha",
            "unknown",
        )

        deployment.execution_message = (
            "GitOps desired state committed "
            f"at {commit_sha[:12]}"
        )

        _audit(
            session=session,
            deployment=deployment,
            event_type=(
                "deployment.execution."
                "gitops_committed"
            ),
            event_data={
                "job_id": str(job.job_id),
                "commit_sha": commit_sha,
                "application": (
                    result_payload.get(
                        "gitops",
                        {},
                    ).get(
                        "application"
                    )
                ),
                "next_action": (
                    "argocd_reconcile"
                ),
            },
        )

        session.commit()
