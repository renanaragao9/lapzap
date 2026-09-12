"""Make businesses.user_id nullable (cadastro público não tem login ainda).

Revision ID: 0006_business_user_id_nullable
Revises: 0005_create_businesses
Create Date: 2026-09-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_business_user_id_nullable"
down_revision: str | None = "0005_create_businesses"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "businesses", "user_id", existing_type=sa.Integer(), nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        "businesses", "user_id", existing_type=sa.Integer(), nullable=False
    )
