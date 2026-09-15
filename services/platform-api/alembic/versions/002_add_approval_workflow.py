"""Add approval workflow fields.

Revision ID: 002
Revises: 001
Create Date: 2026-09-15
"""

from alembic import op
import sqlalchemy as sa


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deployment_requests",
        sa.Column(
            "requested_by_sub",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "deployment_requests",
        sa.Column(
            "decision_by",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "deployment_requests",
        sa.Column(
            "decision_by_sub",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "deployment_requests",
        sa.Column(
            "decision_reason",
            sa.String(length=1000),
            nullable=True,
        ),
    )

    op.add_column(
        "deployment_requests",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "deployment_requests",
        "updated_at",
    )

    op.drop_column(
        "deployment_requests",
        "decision_reason",
    )

    op.drop_column(
        "deployment_requests",
        "decision_by_sub",
    )

    op.drop_column(
        "deployment_requests",
        "decision_by",
    )

    op.drop_column(
        "deployment_requests",
        "requested_by_sub",
    )
