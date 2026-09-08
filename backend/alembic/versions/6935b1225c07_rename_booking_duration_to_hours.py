"""rename booking duration to hours

Revision ID: 6935b1225c07
Revises: 180815037cf5
Create Date: 2026-09-08 10:35:48.720862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6935b1225c07'
down_revision: Union[str, Sequence[str], None] = '180815037cf5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "services",
        "minimum_duration_minutes",
        new_column_name="minimum_duration_hours",
    )
    op.execute(
        "UPDATE services "
        "SET minimum_duration_hours = minimum_duration_hours / 60"
    )


def downgrade() -> None:
    op.alter_column(
        "services",
        "minimum_duration_hours",
        new_column_name="minimum_duration_minutes",
    )
    op.alter_column(
        "services",
        "minimum_duration_hours",
        new_column_name="minimum_duration_minutes",
    )
