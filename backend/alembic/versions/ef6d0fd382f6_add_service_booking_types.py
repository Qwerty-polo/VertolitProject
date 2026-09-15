"""add service booking types

Revision ID: ef6d0fd382f6
Revises: 0fddd4bccbe9
Create Date: 2026-09-15 11:32:16.455374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = 'ef6d0fd382f6'
down_revision: Union[str, Sequence[str], None] = '0fddd4bccbe9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "services",
        sa.Column(
            "booking_type",
            sa.String(length=20),
            server_default=sa.text("'hourly'"),
            nullable=False,
        ),
    )

    op.add_column(
        "services",
        sa.Column(
            "minimum_duration_days",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.alter_column(
        "services",
        "price",
        existing_type=sa.Integer(),
        nullable=True,
    )

    op.alter_column(
        "services",
        "minimum_duration_hours",
        existing_type=sa.Integer(),
        nullable=True,
    )

    op.create_check_constraint(
        "ck_services_booking_type",
        "services",
        "booking_type IN "
        "('hourly', 'daily', 'phone_only')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_services_booking_type",
        "services",
        type_="check",
    )

    op.execute(
        """
        UPDATE services
        SET price = 0
        WHERE price IS NULL
        """
    )

    op.execute(
        """
        UPDATE services
        SET minimum_duration_hours = 1
        WHERE minimum_duration_hours IS NULL
        """
    )

    op.alter_column(
        "services",
        "minimum_duration_hours",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "services",
        "price",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.drop_column(
        "services",
        "minimum_duration_days",
    )

    op.drop_column(
        "services",
        "booking_type",
    )