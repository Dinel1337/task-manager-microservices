"""Init analytics schema.

Revision ID: 001
Revises: 
Create Date: 2026-01-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create schema
    op.execute('CREATE SCHEMA IF NOT EXISTS analytics_service')
    
    # Create task_analytics table
    op.create_table(
        'task_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('task_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('assignee', sa.String(), nullable=True),
        sa.Column('priority', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='analytics_service'
    )
    op.create_index('ix_task_analytics_event_id', 'task_analytics', ['event_id'], unique=True, schema='analytics_service')
    op.create_index('ix_task_analytics_event_type', 'task_analytics', ['event_type'], schema='analytics_service')
    op.create_index('ix_task_analytics_task_id', 'task_analytics', ['task_id'], schema='analytics_service')
    op.create_index('ix_task_analytics_status', 'task_analytics', ['status'], schema='analytics_service')


def downgrade() -> None:
    op.drop_table('task_analytics', schema='analytics_service')
    op.execute('DROP SCHEMA IF EXISTS analytics_service CASCADE')
