"""Create business_info.

Revision ID: 0007_create_business_info
Revises: 0006_create_business_hours
Create Date: 2026-09-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_create_business_info"
down_revision: str | None = "0006_create_business_hours"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "business_info",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
            name="fk_business_info_business_id_businesses",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("business_id", name="uq_business_info_business_id"),
    )


def downgrade() -> None:
    op.drop_table("business_info")
