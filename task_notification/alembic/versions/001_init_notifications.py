"""init notifications table

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from task_notification.core.config import settings

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), server_default="pending", nullable=False),
        sa.Column("recipient", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("timezone('UTC', CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema=settings.POSTGRES_SCHEMA,
    )

    op.create_index(
        f"ix_{settings.POSTGRES_SCHEMA}_notifications_task_id",
        "notifications",
        ["task_id"],
        schema=settings.POSTGRES_SCHEMA,
    )
    op.create_index(
        f"ix_{settings.POSTGRES_SCHEMA}_notifications_recipient",
        "notifications",
        ["recipient"],
        schema=settings.POSTGRES_SCHEMA,
    )
    op.create_index(
        f"ix_{settings.POSTGRES_SCHEMA}_notifications_status",
        "notifications",
        ["status"],
        schema=settings.POSTGRES_SCHEMA,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        f"ix_{settings.POSTGRES_SCHEMA}_notifications_status",
        table_name="notifications",
        schema=settings.POSTGRES_SCHEMA,
    )
    op.drop_index(
        f"ix_{settings.POSTGRES_SCHEMA}_notifications_recipient",
        table_name="notifications",
        schema=settings.POSTGRES_SCHEMA,
    )
    op.drop_index(
        f"ix_{settings.POSTGRES_SCHEMA}_notifications_task_id",
        table_name="notifications",
        schema=settings.POSTGRES_SCHEMA,
    )
    op.drop_table("notifications", schema=settings.POSTGRES_SCHEMA)
