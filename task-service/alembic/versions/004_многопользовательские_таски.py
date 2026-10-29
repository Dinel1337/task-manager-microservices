"""Многопользовательские таски

Revision ID: 764d6ffaa0ec
Revises: 4f05be092d60
Create Date: 2026-10-29 12:53:37.850688

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from task_service.core.config import settings

# revision identifiers, used by Alembic.
revision: str = '764d6ffaa0ec'
down_revision: Union[str, None] = '4f05be092d60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "task_assignees",
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("assignee_email", sa.String(255), nullable=False),
        sa.Column(
            "assigned_at",
            sa.DateTime(),
            server_default=sa.text("timezone('UTC', CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            [f"{settings.POSTGRES_SCHEMA}.tasks.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("task_id", "assignee_email"),
        schema=settings.POSTGRES_SCHEMA,
    )
    op.create_index(
        f"ix_{settings.POSTGRES_SCHEMA}_task_assignees_assignee_email",
        "task_assignees",
        ["assignee_email"],
        schema=settings.POSTGRES_SCHEMA,
    )

def downgrade() -> None:
    op.drop_index(
        f"ix_{settings.POSTGRES_SCHEMA}_task_assignees_assignee_email",
        table_name="task_assignees",
        schema=settings.POSTGRES_SCHEMA,
    )
    op.drop_table("task_assignees", schema=settings.POSTGRES_SCHEMA)


