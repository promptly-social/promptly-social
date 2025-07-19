"""add_import_platform_to_writing_style_analysis

Revision ID: a2db5c6cc8b4
Revises: h8c9d0e1f2g3
Create Date: 2025-07-19 03:03:39.262569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a2db5c6cc8b4"
down_revision: Union[str, None] = "h8c9d0e1f2g3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing check constraint
    op.drop_constraint(
        "writing_style_analysis_platform_check", "writing_style_analysis", type_="check"
    )

    # Create new check constraint with 'import' included
    op.create_check_constraint(
        "writing_style_analysis_platform_check",
        "writing_style_analysis",
        "platform IN ('substack', 'linkedin', 'import')",
    )


def downgrade() -> None:
    # Drop the updated check constraint
    op.drop_constraint(
        "writing_style_analysis_platform_check", "writing_style_analysis", type_="check"
    )

    # Restore original check constraint without 'import'
    op.create_check_constraint(
        "writing_style_analysis_platform_check",
        "writing_style_analysis",
        "platform IN ('substack', 'linkedin')",
    )
