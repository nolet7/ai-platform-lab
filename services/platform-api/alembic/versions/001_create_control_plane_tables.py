"""Create control-plane deployment and audit tables.

Revision ID: 001
Revises:
Create Date: 2026-09-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deployment_requests",

        sa.Column(
            "request_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "tenant_id",
            sa.String(length=128),
            nullable=False,
        ),

        sa.Column(
            "model_name",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "model_version",
            sa.String(length=128),
            nullable=False,
        ),

        sa.Column(
            "environment",
            sa.String(length=32),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
        ),

        sa.Column(
            "requested_by",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint(
            "request_id"
        ),
    )

    op.create_index(
        "ix_deployment_requests_tenant_id",
        "deployment_requests",
        ["tenant_id"],
    )

    op.create_index(
        "ix_deployment_requests_status",
        "deployment_requests",
        ["status"],
    )

    op.create_index(
        "ix_deployment_requests_created_at",
        "deployment_requests",
        ["created_at"],
    )

    op.create_table(
        "audit_events",

        sa.Column(
            "event_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "request_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "event_type",
            sa.String(length=128),
            nullable=False,
        ),

        sa.Column(
            "actor",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "tenant_id",
            sa.String(length=128),
            nullable=False,
        ),

        sa.Column(
            "event_data",
            postgresql.JSONB(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
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
            "event_id"
        ),
    )

    op.create_index(
        "ix_audit_events_request_id",
        "audit_events",
        ["request_id"],
    )

    op.create_index(
        "ix_audit_events_tenant_id",
        "audit_events",
        ["tenant_id"],
    )

    op.create_index(
        "ix_audit_events_created_at",
        "audit_events",
        ["created_at"],
    )

    # Database-level enforcement:
    # audit_events may be INSERTED but never
    # UPDATEd or DELETEd.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION
        prevent_audit_event_mutation()
        RETURNS trigger
        AS $$
        BEGIN
            RAISE EXCEPTION
                'audit_events is append-only';

            RETURN OLD;
        END;
        $$
        LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER
            audit_events_append_only
        BEFORE UPDATE OR DELETE
        ON audit_events
        FOR EACH ROW
        EXECUTE FUNCTION
            prevent_audit_event_mutation();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS
            audit_events_append_only
        ON audit_events;
        """
    )

    op.execute(
        """
        DROP FUNCTION IF EXISTS
            prevent_audit_event_mutation();
        """
    )

    op.drop_index(
        "ix_audit_events_created_at",
        table_name="audit_events",
    )

    op.drop_index(
        "ix_audit_events_tenant_id",
        table_name="audit_events",
    )

    op.drop_index(
        "ix_audit_events_request_id",
        table_name="audit_events",
    )

    op.drop_table(
        "audit_events"
    )

    op.drop_index(
        "ix_deployment_requests_created_at",
        table_name="deployment_requests",
    )

    op.drop_index(
        "ix_deployment_requests_status",
        table_name="deployment_requests",
    )

    op.drop_index(
        "ix_deployment_requests_tenant_id",
        table_name="deployment_requests",
    )

    op.drop_table(
        "deployment_requests"
    )
