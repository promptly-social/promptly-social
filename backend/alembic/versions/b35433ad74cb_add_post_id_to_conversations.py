"""add_post_id_to_conversations

Revision ID: b35433ad74cb
Revises: 85a2ff56a0bb
Create Date: 2025-07-21 10:55:48.600360

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b35433ad74cb"
down_revision: Union[str, None] = "85a2ff56a0bb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add post_id column to conversations table
    op.add_column(
        "conversations",
        sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_conversations_post_id",
        "conversations",
        "posts",
        ["post_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add index for post_id
    op.create_index("idx_conversations_post_id", "conversations", ["post_id"])


def downgrade() -> None:
    # Remove index
    op.drop_index("idx_conversations_post_id", table_name="conversations")

    # Remove foreign key constraint
    op.drop_constraint("fk_conversations_post_id", "conversations", type_="foreignkey")

    # Remove post_id column
    op.drop_column("conversations", "post_id")
