"""add_article_urls_to_posts

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2025-07-18 12:48:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add article URL columns to posts table if they don't exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [col["name"] for col in inspector.get_columns("posts")]

    if "article_url" not in existing_columns:
        op.add_column("posts", sa.Column("article_url", sa.Text(), nullable=True))
    if "linkedin_article_url" not in existing_columns:
        op.add_column(
            "posts", sa.Column("linkedin_article_url", sa.Text(), nullable=True)
        )


def downgrade() -> None:
    op.drop_column("posts", "linkedin_article_url")
    op.drop_column("posts", "article_url")
