"""create_post_media_table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2025-07-18 12:47:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create post_media table if it doesn't exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()
    
    if "post_media" not in existing_tables:
        op.create_table(
            "post_media",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("media_type", sa.Text(), nullable=True),
            sa.Column("file_name", sa.Text(), nullable=True),
            sa.Column("storage_path", sa.Text(), nullable=True),
            sa.Column("gcs_url", sa.Text(), nullable=True),
            sa.Column("linkedin_asset_urn", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.PrimaryKeyConstraint("id", name="pk_post_media"),
            sa.ForeignKeyConstraint(
                ["post_id"],
                ["posts.id"],
                name="fk_post_media_post_id",
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
                name="fk_post_media_user_id",
                ondelete="CASCADE",
            ),
        )

        # Create indexes
        op.create_index("idx_post_media_post_id", "post_media", ["post_id"])
        op.create_index("idx_post_media_user_id", "post_media", ["user_id"])

    # Remove old media columns from posts table if they exist (they're now in post_media table)
    existing_columns = [col['name'] for col in inspector.get_columns('posts')]
    if "media_type" in existing_columns:
        op.drop_column("posts", "media_type")
    if "media_url" in existing_columns:
        op.drop_column("posts", "media_url")
    if "linkedin_asset_urn" in existing_columns:
        op.drop_column("posts", "linkedin_asset_urn")


def downgrade() -> None:
    # Re-add the old media columns to posts table
    op.add_column("posts", sa.Column("media_type", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("media_url", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("linkedin_asset_urn", sa.Text(), nullable=True))

    # Drop indexes and table
    op.drop_index("idx_post_media_user_id", table_name="post_media")
    op.drop_index("idx_post_media_post_id", table_name="post_media")
    op.drop_table("post_media")
