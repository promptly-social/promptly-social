"""add_missing_user_preferences_columns

Revision ID: h8c9d0e1f2g3
Revises: g7b8c9d0e1f2
Create Date: 2025-07-18 12:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "h8c9d0e1f2g3"
down_revision: Union[str, None] = "g7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to user_preferences table if they don't exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [col['name'] for col in inspector.get_columns('user_preferences')]
    
    if "substacks" not in existing_columns:
        op.add_column(
            "user_preferences", 
            sa.Column("substacks", postgresql.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'"))
        )
    
    if "bio" not in existing_columns:
        op.add_column(
            "user_preferences", 
            sa.Column("bio", sa.String(), nullable=False, server_default=sa.text("''"))
        )
    
    if "preferred_posting_time" not in existing_columns:
        op.add_column(
            "user_preferences", 
            sa.Column("preferred_posting_time", sa.Time(timezone=False), nullable=True)
        )
    
    if "timezone" not in existing_columns:
        op.add_column(
            "user_preferences", 
            sa.Column("timezone", sa.String(), nullable=True)
        )


def downgrade() -> None:
    op.drop_column("user_preferences", "timezone")
    op.drop_column("user_preferences", "preferred_posting_time")
    op.drop_column("user_preferences", "bio")
    op.drop_column("user_preferences", "substacks")
