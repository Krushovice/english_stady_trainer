"""add course_exam_attempts table

Revision ID: 9c3d5b1a7e42
Revises: a71c4e2f9d08
Create Date: 2026-08-21 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9c3d5b1a7e42'
down_revision: Union[str, Sequence[str], None] = 'a71c4e2f9d08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'course_exam_attempts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('exercise_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('answers', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('passed', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_course_exam_attempts_user', 'course_exam_attempts', ['user_id'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_course_exam_attempts_user', table_name='course_exam_attempts')
    op.drop_table('course_exam_attempts')
