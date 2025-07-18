"""add_missing_social_connections_columns

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2025-07-18 12:57:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "g7b8c9d0e1f2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to social_connections table if they don't exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [col['name'] for col in inspector.get_columns('social_connections')]
    
    if "analysis_started_at" not in existing_columns:
        op.add_column(
            "social_connections", 
            sa.Column("analysis_started_at", sa.DateTime(timezone=True), nullable=True)
        )
    
    if "analysis_completed_at" not in existing_columns:
        op.add_column(
            "social_connections", 
            sa.Column("analysis_completed_at", sa.DateTime(timezone=True), nullable=True)
        )
    
    if "analysis_status" not in existing_columns:
        op.add_column(
            "social_connections", 
            sa.Column("analysis_status", sa.String(), nullable=False, server_default=sa.text("'not_started'"))
        )


def downgrade() -> None:
    op.drop_column("social_connections", "analysis_status")
    op.drop_column("social_connections", "analysis_completed_at")
    op.drop_column("social_connections", "analysis_started_at")
