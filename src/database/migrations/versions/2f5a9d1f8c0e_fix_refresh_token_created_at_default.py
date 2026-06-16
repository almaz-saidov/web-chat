"""fix refresh token created at default

Revision ID: 2f5a9d1f8c0e
Revises: 914ba6990f25
Create Date: 2026-06-16 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2f5a9d1f8c0e"
down_revision: Union[str, Sequence[str], None] = "914ba6990f25"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "refresh_tokens",
        "created_at",
        server_default=sa.text("now()"),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "refresh_tokens",
        "created_at",
        server_default=sa.text("(NOW() + INTERVAL '30 days')"),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )
