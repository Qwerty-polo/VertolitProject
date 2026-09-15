"""prevent overlapping confirmed bookings

Revision ID: 0fddd4bccbe9
Revises: 565985043c24
Create Date: 2026-09-15 10:13:08.361470

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0fddd4bccbe9'
down_revision: Union[str, Sequence[str], None] = '565985043c24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE EXTENSION IF NOT EXISTS btree_gist"
    )

    op.execute(
        """
        ALTER TABLE bookings
        ADD CONSTRAINT
        exclude_overlapping_confirmed_bookings
        EXCLUDE USING gist (
            service_id WITH =,
            tstzrange(
                starts_at,
                ends_at,
                '[)'
            ) WITH &&
        )
        WHERE (status = 'confirmed')
        """
    )


def downgrade() -> None:
    op.drop_constraint(
        "exclude_overlapping_confirmed_bookings",
        "bookings",
    )
