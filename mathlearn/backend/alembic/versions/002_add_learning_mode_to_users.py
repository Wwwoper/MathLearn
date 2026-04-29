"""add learning_mode to users

Revision ID: 002
Revises: a04a68b9db83
Create Date: 2026-04-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "a04a68b9db83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add learning_mode column to users table."""
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("learning_mode", sa.String(length=20), nullable=False, server_default="classic")
        )


def downgrade() -> None:
    """Remove learning_mode column from users table."""
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("learning_mode")
