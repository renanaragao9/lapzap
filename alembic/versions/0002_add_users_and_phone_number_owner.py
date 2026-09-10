"""Add users and phone number owner.

Revision ID: 0002_add_users_and_phone_number_owner
Revises: 0001_create_phone_numbers
Create Date: 2026-09-09
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_add_users_and_phone_number_owner"
down_revision: str | None = "0001_create_phone_numbers"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
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
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.add_column(
        "phone_numbers",
        sa.Column("user_id", sa.Integer(), nullable=False),
    )
    op.create_index("ix_phone_numbers_user_id", "phone_numbers", ["user_id"])
    op.create_foreign_key(
        "fk_phone_numbers_user_id_users",
        "phone_numbers",
        "users",
        ["user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_phone_numbers_user_id_users", "phone_numbers", type_="foreignkey"
    )
    op.drop_index("ix_phone_numbers_user_id", table_name="phone_numbers")
    op.drop_column("phone_numbers", "user_id")
    op.drop_table("users")
