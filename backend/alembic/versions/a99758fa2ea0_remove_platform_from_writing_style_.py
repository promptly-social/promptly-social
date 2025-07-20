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

    # Now drop the platform and content_count columns
    op.drop_column("writing_style_analysis", "platform")
    op.drop_column("writing_style_analysis", "content_count")

    # Add unique constraint on user_id (since we now have only one record per user)
    op.create_unique_constraint(
        "uq_writing_style_analysis_user_id", "writing_style_analysis", ["user_id"]
    )


def downgrade() -> None:
    # Drop the unique constraint on user_id
    op.drop_constraint(
        "uq_writing_style_analysis_user_id", "writing_style_analysis", type_="unique"
    )

    # Add back the platform and content_count columns
    op.add_column(
        "writing_style_analysis",
        sa.Column("platform", sa.String(), nullable=False, server_default="import"),
    )
    op.add_column(
        "writing_style_analysis",
        sa.Column("content_count", sa.Integer(), nullable=False, server_default="0"),
    )

    # Remove the server defaults after adding the columns
    op.alter_column("writing_style_analysis", "platform", server_default=None)
    op.alter_column("writing_style_analysis", "content_count", server_default=None)
