"""add_image_generation_style_to_user_preferences

Revision ID: 9cb3ffcba638
Revises: a2db5c6cc8b4
Create Date: 2025-07-19 16:53:18.096371

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9cb3ffcba638"
down_revision: Union[str, None] = "a2db5c6cc8b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add image_generation_style column to user_preferences table
    op.add_column(
        "user_preferences",
        sa.Column("image_generation_style", sa.String(), nullable=True),
    )


def downgrade() -> None:
    # Remove image_generation_style column from user_preferences table
    op.drop_column("user_preferences", "image_generation_style")
