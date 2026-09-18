"""RQ-compatible IDs for repeatable deployment dispatches."""

from uuid import UUID, uuid4


def make_rq_job_id(job_id: UUID, dispatch_id: UUID | None = None) -> str:
    return f"deployment-{job_id}-{dispatch_id or uuid4()}"
