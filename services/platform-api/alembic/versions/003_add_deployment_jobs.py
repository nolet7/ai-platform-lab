"""Add durable deployment execution jobs.

Revision ID: 003
Revises: 002
Create Date: 2026-09-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deployment_requests",
        sa.Column(
            "execution_status",
            sa.String(length=32),
            server_default=sa.text(
                "'not_started'"
            ),
            nullable=False,
        ),
    )

    op.add_column(
        "deployment_requests",
        sa.Column(
            "execution_message",
            sa.String(length=1000),
            nullable=True,
        ),
    )

    op.create_table(
        "deployment_jobs",

        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "request_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "queue_name",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text(
                "'deployments'"
            ),
        ),

        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text(
                "'queued'"
            ),
        ),

        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),

        sa.Column(
            "max_attempts",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("3"),
        ),

        sa.Column(
            "last_error",
            sa.String(length=2000),
            nullable=True,
        ),

        sa.Column(
            "result_payload",
            postgresql.JSONB(),
            nullable=True,
        ),

        sa.Column(
            "last_dispatched_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "finished_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["request_id"],
            ["deployment_requests.request_id"],
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint(
            "job_id"
        ),

        sa.UniqueConstraint(
            "request_id",
            name="uq_deployment_jobs_request_id",
        ),
    )

    op.create_index(
        "ix_deployment_jobs_status",
        "deployment_jobs",
        ["status"],
    )

    op.create_index(
        "ix_deployment_jobs_created_at",
        "deployment_jobs",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_deployment_jobs_created_at",
        table_name="deployment_jobs",
    )

    op.drop_index(
        "ix_deployment_jobs_status",
        table_name="deployment_jobs",
    )

    op.drop_table(
        "deployment_jobs"
    )

    op.drop_column(
        "deployment_requests",
        "execution_message",
    )

    op.drop_column(
        "deployment_requests",
        "execution_status",
    )
