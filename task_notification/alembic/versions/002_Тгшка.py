"""user_telegram

Revision ID: c9f4125843a2
Revises: 001
Create Date: 2026-11-01 11:03:07.800194

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from task_notification.core.config import settings

# revision identifiers, used by Alembic.
revision: str = 'c9f4125843a2'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_telegram',
        sa.Column('email', sa.VARCHAR(255), primary_key=True),
        sa.Column('telegram_id', sa.BIGINT, nullable=False, unique=True),
        sa.Column('telegram_username', sa.VARCHAR(255)),
        sa.Column('registered_at',sa.DateTime(), nullable=False,
            server_default=sa.text("timezone('UTC', CURRENT_TIMESTAMP)"),
    ),
        schema=settings.POSTGRES_SCHEMA,
    )
    


def downgrade() -> None:
    op.drop_table('user_telegram', schema=settings.POSTGRES_SCHEMA)