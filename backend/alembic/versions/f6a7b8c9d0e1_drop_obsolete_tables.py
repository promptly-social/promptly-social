"""drop_obsolete_tables

Revision ID: f6a7b8c9d0e1
Revises: 010a96bb7115
Create Date: 2025-07-18 12:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "010a96bb7115"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop obsolete tables that are no longer used in the current models
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()
    
    # Drop scraped_content table if it exists
    if "scraped_content" in existing_tables:
        # Drop indexes first
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('scraped_content')]
        if "idx_scraped_content_topics" in existing_indexes:
            op.drop_index("idx_scraped_content_topics", table_name="scraped_content")
        if "idx_scraped_content_user_id" in existing_indexes:
            op.drop_index("idx_scraped_content_user_id", table_name="scraped_content")
        
        # Drop the table
        op.drop_table("scraped_content")
    
    # Drop imported_content table if it exists
    if "imported_content" in existing_tables:
        op.drop_table("imported_content")


def downgrade() -> None:
    # Recreate scraped_content table
    op.create_table(
        "scraped_content",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column(
            "topics",
            postgresql.ARRAY(sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "scraped_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "relevance_score", sa.DECIMAL(), nullable=True, server_default=sa.text("0")
        ),
        sa.Column(
            "suggested_for_linkedin",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("false"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    
    # Recreate indexes
    op.create_index("idx_scraped_content_user_id", "scraped_content", ["user_id"])
    op.create_index(
        "idx_scraped_content_topics",
        "scraped_content",
        ["topics"],
        postgresql_using="gin",
    )
    
    # Recreate imported_content table
    op.create_table(
        "imported_content",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("platform_username", sa.Text(), nullable=True),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "imported_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
