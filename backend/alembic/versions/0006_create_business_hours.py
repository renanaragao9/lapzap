"""Create business_hours.

Revision ID: 0006_create_business_hours
Revises: 0005_create_businesses
Create Date: 2026-09-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_create_business_hours"
down_revision: str | None = "0005_create_businesses"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "business_hours",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("opens_at", sa.Time(), nullable=True),
        sa.Column("closes_at", sa.Time(), nullable=True),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
            name="fk_business_hours_business_id_businesses",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_business_hours_business_id", "business_hours", ["business_id"])


def downgrade() -> None:
    op.drop_index("ix_business_hours_business_id", table_name="business_hours")
    op.drop_table("business_hours")
