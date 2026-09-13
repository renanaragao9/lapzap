"""Create business_integrations.

Revision ID: 0008_business_integrations
Revises: 0007_create_business_info
Create Date: 2026-09-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_business_integrations"
down_revision: str | None = "0007_create_business_info"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "business_integrations",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("host", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("encrypted_secret", sa.Text(), nullable=True),
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
            name="fk_business_integrations_business_id_businesses",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "business_id", "name", name="uq_business_integrations_business_id_name"
        ),
    )
    op.create_index(
        "ix_business_integrations_business_id",
        "business_integrations",
        ["business_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_business_integrations_business_id", table_name="business_integrations"
    )
    op.drop_table("business_integrations")
