"""add task history and restore status index

Revision ID: 4f05be092d60
Revises: 3a6348cbd68a
Create Date: ...
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = '4f05be092d60'
down_revision: Union[str, None] = '3a6348cbd68a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_task_service_tasks_status",
        "tasks",
        ["status"],
        unique=False,
        schema="task_service",
    )

    op.create_table(
        "task_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("changed_by", sa.String(length=255), nullable=False),
        sa.Column("change_type", sa.String(length=50), nullable=False),
        sa.Column("changes", postgresql.JSONB(), nullable=False),
        sa.Column(
            "changed_at",
            sa.DateTime(),
            server_default=sa.text("timezone('UTC', CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="task_service",
    )
    op.create_index(
        "ix_task_service_task_history_task_id",
        "task_history",
        ["task_id"],
        schema="task_service",
    )
    op.create_index(
        "ix_task_service_task_history_changed_at",
        "task_history",
        ["changed_at"],
        schema="task_service",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_task_service_task_history_changed_at",
        table_name="task_history",
        schema="task_service",
    )
    op.drop_index(
        "ix_task_service_task_history_task_id",
        table_name="task_history",
        schema="task_service",
    )
    op.drop_table("task_history", schema="task_service")
    op.drop_index(
        "ix_task_service_tasks_status",
        table_name="tasks",
        schema="task_service",
    )