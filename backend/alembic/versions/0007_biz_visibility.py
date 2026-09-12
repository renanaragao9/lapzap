"""Add businesses.visibility, phone_numbers.business_id.

Revision ID: 0007_biz_visibility
Revises: 0006_business_user_id_nullable
Create Date: 2026-09-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_biz_visibility"
down_revision: str | None = "0006_business_user_id_nullable"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "businesses",
        sa.Column(
            "visibility",
            sa.String(length=20),
            nullable=False,
            server_default="public",
        ),
    )
    op.add_column(  
        "phone_numbers", sa.Column("business_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_phone_numbers_business_id_businesses",
        "phone_numbers",
        "businesses",
        ["business_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_phone_numbers_business_id", "phone_numbers", ["business_id"]
    )

    # era unique GLOBAL (nenhum outro negócio podia cadastrar o mesmo número
    # de cliente) - vira unique por negócio
    op.drop_constraint(
        "uq_phone_numbers_phone_number", "phone_numbers", type_="unique"
    )
    op.create_unique_constraint(
        "uq_phone_numbers_business_id_phone_number",
        "phone_numbers",
        ["business_id", "phone_number"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_phone_numbers_business_id_phone_number",
        "phone_numbers",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_phone_numbers_phone_number", "phone_numbers", ["phone_number"]
    )

    op.drop_index("ix_phone_numbers_business_id", table_name="phone_numbers")
    op.drop_constraint(
        "fk_phone_numbers_business_id_businesses", "phone_numbers", type_="foreignkey"
    )
    op.drop_column("phone_numbers", "business_id")
    op.drop_column("businesses", "visibility")
