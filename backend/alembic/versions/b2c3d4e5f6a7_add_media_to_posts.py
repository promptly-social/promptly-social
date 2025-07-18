"""add_media_to_posts

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-07-18 12:46:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add media columns to posts table if they don't exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [col['name'] for col in inspector.get_columns('posts')]
    
    if "media_type" not in existing_columns:
        op.add_column("posts", sa.Column("media_type", sa.Text(), nullable=True))
    if "media_url" not in existing_columns:
        op.add_column("posts", sa.Column("media_url", sa.Text(), nullable=True))
    if "linkedin_asset_urn" not in existing_columns:
        op.add_column("posts", sa.Column("linkedin_asset_urn", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("posts", "linkedin_asset_urn")
    op.drop_column("posts", "media_url")
    op.drop_column("posts", "media_type")
