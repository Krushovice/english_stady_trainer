"""add final_exam attempt source

Revision ID: a71c4e2f9d08
Revises: f2a5c9d17b3e
Create Date: 2026-08-21 00:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a71c4e2f9d08'
down_revision: Union[str, Sequence[str], None] = 'f2a5c9d17b3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLAlchemy's Enum() persists Python enum *member names* (see
    # e494e8419353) — 'FINAL_EXAM', matching AttemptSource.FINAL_EXAM.
    # Separate migration from the table that uses it: Postgres can't add an
    # enum value and use it in the same transaction (same reason
    # e8b93a565404 split LEVEL_EXAM out on its own).
    op.execute("ALTER TYPE exercise_attempt_source ADD VALUE IF NOT EXISTS 'FINAL_EXAM'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres has no `DROP VALUE` for enum types; the added value is left
    # in place on downgrade.
    pass
