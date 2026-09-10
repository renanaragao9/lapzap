"""Create message logs.

Revision ID: 0003_create_message_logs
Revises: 0002_add_users_and_phone_number_owner
Create Date: 2026-09-09
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_create_message_logs"
down_revision: str | None = "0002_add_users_and_phone_number_owner"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "message_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("message_type", sa.String(length=20), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("phone_number_id", sa.Integer(), nullable=True),
        sa.Column("external_message_id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["phone_number_id"],
            ["phone_numbers.id"],
            name="fk_message_logs_phone_number_id_phone_numbers",
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_message_logs_phone_number_id",
        "message_logs",
        ["phone_number_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_message_logs_phone_number_id", table_name="message_logs")
    op.drop_table("message_logs")
