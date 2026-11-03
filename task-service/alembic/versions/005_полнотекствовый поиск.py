"""add fulltext search

Revision ID: 14ebf5922d1a
Revises: 764d6ffaa0ec
Create Date: 2026-11-01 07:11:10.690943

"""
from typing import Sequence, Union
from task_service.core.config import settings
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14ebf5922d1a'
down_revision: Union[str, None] = '764d6ffaa0ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(f"""
        ALTER TABLE {settings.POSTGRES_SCHEMA}.tasks
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector('russian', coalesce(title, '') || ' ' || coalesce(description, ''))
        ) STORED;
    """)

    op.execute(f"""
        CREATE INDEX idx_tasks_search 
        ON {settings.POSTGRES_SCHEMA}.tasks 
        USING GIN (search_vector);
    """)

def downgrade() -> None:
    op.execute(f"DROP INDEX IF EXISTS {settings.POSTGRES_SCHEMA}.idx_tasks_search;")
    op.execute(f"ALTER TABLE {settings.POSTGRES_SCHEMA}.tasks DROP COLUMN IF EXISTS search_vector;")


