"""merge_supabase_sync_migrations

Revision ID: 010a96bb7115
Revises: 3d3a9cb38525, e5f6a7b8c9d0
Create Date: 2025-07-18 12:48:53.070346

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "010a96bb7115"
down_revision: Union[str, None] = ("3d3a9cb38525", "e5f6a7b8c9d0")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
