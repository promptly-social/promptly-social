"""create_idea_banks_and_posts_tables

Revision ID: 2febca08b852
Revises: 172ee7536e6c
Create Date: 2025-07-18 10:09:30.312553

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "2febca08b852"
down_revision: Union[str, None] = "172ee7536e6c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create update_updated_at_column function
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    # Create idea_banks table
    op.create_table(
        "idea_banks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # Create indexes for idea_banks table
    op.create_index("idx_idea_banks_user_id", "idea_banks", ["user_id"])
    op.create_index(
        "idx_idea_banks_data", "idea_banks", ["data"], postgresql_using="gin"
    )

    # Create trigger for idea_banks updated_at
    op.execute(
        """
        CREATE TRIGGER update_idea_banks_updated_at 
            BEFORE UPDATE ON idea_banks 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
    """
    )

    # Create posts table (formerly suggested_posts)
    op.create_table(
        "posts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("idea_bank_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "recommendation_score",
            sa.Integer(),
            nullable=True,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "platform", sa.Text(), nullable=False, server_default=sa.text("'linkedin'")
        ),
        sa.Column(
            "topics",
            postgresql.ARRAY(sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "status", sa.Text(), nullable=True, server_default=sa.text("'suggested'")
        ),
        sa.Column("user_feedback", sa.String(20), nullable=True),
        sa.Column("feedback_comment", sa.Text(), nullable=True),
        sa.Column("feedback_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("posted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("article_url", sa.Text(), nullable=True),
        sa.Column("linkedin_article_url", sa.Text(), nullable=True),
        sa.Column("scheduler_job_name", sa.String(255), nullable=True),
        sa.Column("linkedin_post_id", sa.String(255), nullable=True),
        sa.Column("sharing_error", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["idea_bank_id"], ["idea_banks.id"], ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            "user_feedback IN ('positive', 'negative') OR user_feedback IS NULL",
            name="posts_user_feedback_check",
        ),
    )

    # Create indexes for posts table
    op.create_index("idx_posts_user_id", "posts", ["user_id"])
    op.create_index("idx_posts_topics", "posts", ["topics"], postgresql_using="gin")
    op.create_index("idx_posts_idea_bank_id", "posts", ["idea_bank_id"])
    op.create_index("idx_posts_platform", "posts", ["platform"])
    op.create_index(
        "idx_posts_recommendation_score",
        "posts",
        ["recommendation_score"],
        postgresql_ops={"recommendation_score": "DESC"},
    )
    op.create_index(
        "idx_posts_user_feedback",
        "posts",
        ["user_feedback"],
        postgresql_where=sa.text("user_feedback IS NOT NULL"),
    )
    op.create_index(
        "idx_posts_updated_at",
        "posts",
        ["updated_at"],
        postgresql_ops={"updated_at": "DESC"},
    )
    op.create_index(
        "idx_posts_scheduled_at",
        "posts",
        ["scheduled_at"],
        postgresql_where=sa.text("scheduled_at IS NOT NULL"),
    )
    op.create_index(
        "idx_posts_status_scheduled_at",
        "posts",
        ["status", "scheduled_at"],
        postgresql_where=sa.text("scheduled_at IS NOT NULL"),
    )
    op.create_index(
        "idx_posts_scheduler_job_name",
        "posts",
        ["scheduler_job_name"],
        postgresql_where=sa.text("scheduler_job_name IS NOT NULL"),
    )
    op.create_index(
        "idx_posts_linkedin_post_id",
        "posts",
        ["linkedin_post_id"],
        postgresql_where=sa.text("linkedin_post_id IS NOT NULL"),
    )
    op.create_index(
        "idx_posts_scheduled_pending",
        "posts",
        ["scheduled_at", "status"],
        postgresql_where=sa.text("scheduled_at IS NOT NULL AND status = 'scheduled'"),
    )

    # Create trigger for posts updated_at
    op.execute(
        """
        CREATE TRIGGER trigger_update_posts_updated_at
            BEFORE UPDATE ON posts
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """
    )

    # Create post_media table
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # Create indexes for post_media table
    op.create_index("idx_post_media_post_id", "post_media", ["post_id"])
    op.create_index("idx_post_media_user_id", "post_media", ["user_id"])

    # Create trigger for post_media updated_at
    op.execute(
        """
        CREATE TRIGGER trigger_update_post_media_updated_at
            BEFORE UPDATE ON post_media
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """
    )


def downgrade() -> None:
    # Drop triggers
    op.execute(
        "DROP TRIGGER IF EXISTS trigger_update_post_media_updated_at ON post_media;"
    )
    op.execute("DROP TRIGGER IF EXISTS trigger_update_posts_updated_at ON posts;")
    op.execute("DROP TRIGGER IF EXISTS update_idea_banks_updated_at ON idea_banks;")

    # Drop indexes and tables in reverse order
    op.drop_index("idx_post_media_user_id", table_name="post_media")
    op.drop_index("idx_post_media_post_id", table_name="post_media")
    op.drop_table("post_media")

    op.drop_index("idx_posts_scheduled_pending", table_name="posts")
    op.drop_index("idx_posts_linkedin_post_id", table_name="posts")
    op.drop_index("idx_posts_scheduler_job_name", table_name="posts")
    op.drop_index("idx_posts_status_scheduled_at", table_name="posts")
    op.drop_index("idx_posts_scheduled_at", table_name="posts")
    op.drop_index("idx_posts_updated_at", table_name="posts")
    op.drop_index("idx_posts_user_feedback", table_name="posts")
    op.drop_index("idx_posts_recommendation_score", table_name="posts")
    op.drop_index("idx_posts_platform", table_name="posts")
    op.drop_index("idx_posts_idea_bank_id", table_name="posts")
    op.drop_index("idx_posts_topics", table_name="posts")
    op.drop_index("idx_posts_user_id", table_name="posts")
    op.drop_table("posts")

    op.drop_index("idx_idea_banks_data", table_name="idea_banks")
    op.drop_index("idx_idea_banks_user_id", table_name="idea_banks")
    op.drop_table("idea_banks")

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
