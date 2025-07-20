"""remove_platform_from_writing_style_analysis

Revision ID: a99758fa2ea0
Revises: 9cb3ffcba638
Create Date: 2025-07-20 09:47:03.162907

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a99758fa2ea0"
down_revision: Union[str, None] = "9cb3ffcba638"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Before dropping the platform column, keep only the record with the latest updated_at per user

    # First, create a temporary table to store the IDs of records to keep
    op.execute(
        """
        CREATE TEMPORARY TABLE records_to_keep AS
        SELECT DISTINCT ON (user_id) id
        FROM writing_style_analysis
        ORDER BY user_id, updated_at DESC, created_at DESC
    """
    )

    # Delete all records except those in the temporary table
    op.execute(
        """
        DELETE FROM writing_style_analysis
        WHERE id NOT IN (SELECT id FROM records_to_keep)
    """
    )

    # Now drop the platform column
    op.drop_column("writing_style_analysis", "platform")


def downgrade() -> None:
    # Add back the platform column with a default value
    op.add_column(
        "writing_style_analysis",
        sa.Column("platform", sa.String(), nullable=False, server_default="import"),
    )

    # Remove the server default after adding the column
    op.alter_column("writing_style_analysis", "platform", server_default=None)
