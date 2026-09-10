"""Create phone numbers table.

Revision ID: 0002_create_phone_numbers
Revises: 0001_create_users
Create Date: 2026-09-10
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_create_phone_numbers"
down_revision: str | None = "0001_create_users"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "phone_numbers",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
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
            ["user_id"],
            ["users.id"],
            name="fk_phone_numbers_user_id_users",
        ),
        sa.UniqueConstraint("phone_number", name="uq_phone_numbers_phone_number"),
    )
    op.create_index("ix_phone_numbers_user_id", "phone_numbers", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_phone_numbers_user_id", table_name="phone_numbers")
    op.drop_table("phone_numbers")
