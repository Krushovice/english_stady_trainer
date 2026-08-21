"""add exercise_attempt user+attempted_at index

Revision ID: f2a5c9d17b3e
Revises: e8b93a565404
Create Date: 2026-08-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a5c9d17b3e'
down_revision: Union[str, Sequence[str], None] = 'e8b93a565404'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        'ix_exercise_attempts_user_attempted_at',
        'exercise_attempts',
        ['user_id', 'attempted_at'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_exercise_attempts_user_attempted_at', table_name='exercise_attempts')
