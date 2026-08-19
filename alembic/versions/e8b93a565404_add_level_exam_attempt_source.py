"""add level_exam attempt source

Revision ID: e8b93a565404
Revises: e494e8419353
Create Date: 2026-08-19 19:25:43.524063

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8b93a565404'
down_revision: Union[str, Sequence[str], None] = 'e494e8419353'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLAlchemy's Enum() persists Python enum *member names* (see
    # e494e8419353) — 'LEVEL_EXAM', matching AttemptSource.LEVEL_EXAM.
    op.execute("ALTER TYPE exercise_attempt_source ADD VALUE IF NOT EXISTS 'LEVEL_EXAM'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres has no `DROP VALUE` for enum types; the added value is left
    # in place on downgrade.
    pass
