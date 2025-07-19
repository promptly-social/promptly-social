"""add_post_scheduling_fields

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2025-07-18 12:49:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add post scheduling fields if they don't exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [col["name"] for col in inspector.get_columns("posts")]
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("posts")]

    if "scheduler_job_name" not in existing_columns:
        op.add_column(
            "posts", sa.Column("scheduler_job_name", sa.String(255), nullable=True)
        )
    if "linkedin_post_id" not in existing_columns:
        op.add_column(
            "posts", sa.Column("linkedin_post_id", sa.String(255), nullable=True)
        )
    if "sharing_error" not in existing_columns:
        op.add_column("posts", sa.Column("sharing_error", sa.Text(), nullable=True))

    # Create indexes for efficient lookups if they don't exist
    if "idx_posts_scheduler_job_name" not in existing_indexes:
        op.create_index(
            "idx_posts_scheduler_job_name",
            "posts",
            ["scheduler_job_name"],
            postgresql_where=sa.text("scheduler_job_name IS NOT NULL"),
        )
    if "idx_posts_linkedin_post_id" not in existing_indexes:
        op.create_index(
            "idx_posts_linkedin_post_id",
            "posts",
            ["linkedin_post_id"],
            postgresql_where=sa.text("linkedin_post_id IS NOT NULL"),
        )
    if "idx_posts_scheduled_pending" not in existing_indexes:
        op.create_index(
            "idx_posts_scheduled_pending",
            "posts",
            ["scheduled_at", "status"],
            postgresql_where=sa.text(
                "scheduled_at IS NOT NULL AND status = 'scheduled'"
            ),
        )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_posts_scheduled_pending", table_name="posts")
    op.drop_index("idx_posts_linkedin_post_id", table_name="posts")
    op.drop_index("idx_posts_scheduler_job_name", table_name="posts")

    # Drop columns
    op.drop_column("posts", "sharing_error")
    op.drop_column("posts", "linkedin_post_id")
    op.drop_column("posts", "scheduler_job_name")
