"""add learning_profiles.placement_skip_credit_through

Revision ID: b4d8e6a1f3c7
Revises: 9c3d5b1a7e42
Create Date: 2026-08-21 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4d8e6a1f3c7"
down_revision: str | Sequence[str] | None = "9c3d5b1a7e42"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # cefr_level already exists (created by 01a7a759cfed) — reused here, not recreated.
    op.add_column(
        "learning_profiles",
        sa.Column(
            "placement_skip_credit_through",
            postgresql.ENUM("A1", "A2", "B1", "B2", name="cefr_level", create_type=False),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("learning_profiles", "placement_skip_credit_through")
