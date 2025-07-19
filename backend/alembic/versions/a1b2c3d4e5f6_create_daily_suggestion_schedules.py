"""create_daily_suggestion_schedules

Revision ID: a1b2c3d4e5f6
Revises: d6e4f83a4b21
Create Date: 2025-07-18 12:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "d6e4f83a4b21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create daily_suggestion_schedules table if it doesn't exist
    # Check if table exists first
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    if "daily_suggestion_schedules" not in existing_tables:
        op.create_table(
            "daily_suggestion_schedules",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("cron_expression", sa.Text(), nullable=False),
            sa.Column(
                "timezone", sa.Text(), nullable=False, server_default=sa.text("'UTC'")
            ),
            sa.Column("last_run_at", sa.TIMESTAMP(timezone=True), nullable=True),
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
            sa.PrimaryKeyConstraint("id", name="pk_daily_suggestion_schedules"),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
                name="fk_daily_suggestion_schedules_user_id",
                ondelete="CASCADE",
            ),
            sa.UniqueConstraint(
                "user_id", name="daily_suggestion_schedules_user_unique"
            ),
            sa.CheckConstraint(
                "cron_expression <> ''",
                name="daily_suggestion_schedules_cron_expression_check",
            ),
        )


def downgrade() -> None:
    op.drop_table("daily_suggestion_schedules")
