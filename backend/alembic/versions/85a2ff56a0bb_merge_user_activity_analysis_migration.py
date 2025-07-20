"""merge user activity analysis migration

Revision ID: 85a2ff56a0bb
Revises: a99758fa2ea0, i9d0e1f2g3h4
Create Date: 2025-07-20 13:48:39.399865

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "85a2ff56a0bb"
down_revision: Union[str, None] = ("a99758fa2ea0", "i9d0e1f2g3h4")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
