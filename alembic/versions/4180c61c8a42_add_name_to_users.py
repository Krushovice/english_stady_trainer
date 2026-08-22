"""add name to users

Revision ID: 4180c61c8a42
Revises: b4d8e6a1f3c7
Create Date: 2026-08-22 18:31:32.440616

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4180c61c8a42"
down_revision: str | Sequence[str] | None = "b4d8e6a1f3c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default backfills existing rows (registration predates this
    # column); new registrations always provide a real name explicitly, so
    # the default is only ever a safety net for accounts created before
    # this migration.
    op.add_column("users", sa.Column("name", sa.String(length=100), nullable=False, server_default=""))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "name")
