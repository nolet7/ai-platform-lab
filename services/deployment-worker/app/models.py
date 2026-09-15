from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID as PG_UUID,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    pass


class DeploymentRequestRecord(Base):
    __tablename__ = "deployment_requests"

    request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )

    tenant_id: Mapped[str] = mapped_column(
        String(128),
    )

    model_name: Mapped[str] = mapped_column(
        String(255),
    )

    model_version: Mapped[str] = mapped_column(
        String(128),
    )

    environment: Mapped[str] = mapped_column(
        String(32),
    )

    status: Mapped[str] = mapped_column(
        String(32),
    )

    execution_status: Mapped[str] = mapped_column(
        String(32),
    )

    execution_message: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )


class DeploymentJobRecord(Base):
    __tablename__ = "deployment_jobs"

    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )

    request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        unique=True,
    )

    queue_name: Mapped[str] = mapped_column(
        String(64),
    )

    status: Mapped[str] = mapped_column(
        String(32),
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
    )

    max_attempts: Mapped[int] = mapped_column(
        Integer,
    )

    last_error: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    result_payload: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    last_dispatched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )


class AuditEventRecord(Base):
    __tablename__ = "audit_events"

    event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )

    request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
    )

    event_type: Mapped[str] = mapped_column(
        String(128),
    )

    actor: Mapped[str] = mapped_column(
        String(255),
    )

    tenant_id: Mapped[str] = mapped_column(
        String(128),
    )

    event_data: Mapped[dict] = mapped_column(
        JSONB,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )
