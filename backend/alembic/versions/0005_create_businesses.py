"""Create businesses / business_hours, add business_id + sender to message_logs.

Revision ID: 0005_create_businesses
Revises: 0004_add_users_is_admin
Create Date: 2026-09-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_create_businesses"
down_revision: str | None = "0004_add_users_is_admin"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "businesses",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("business_type", sa.String(length=30), nullable=False),
        sa.Column("contact_phone_number", sa.String(length=20), nullable=False),
        sa.Column("plan", sa.String(length=30), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending_setup",
        ),
        sa.Column("evolution_instance_name", sa.String(length=255), nullable=True),
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
            ["user_id"], ["users.id"], name="fk_businesses_user_id_users"
        ),
        sa.UniqueConstraint(
            "evolution_instance_name", name="uq_businesses_evolution_instance_name"
        ),
    )
    op.create_index("ix_businesses_user_id", "businesses", ["user_id"])

    op.create_table(
        "business_hours",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("opens_at", sa.Time(), nullable=True),
        sa.Column("closes_at", sa.Time(), nullable=True),
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
            name="fk_business_hours_business_id_businesses",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_business_hours_business_id", "business_hours", ["business_id"])

    op.add_column("message_logs", sa.Column("business_id", sa.Integer(), nullable=True))
    op.add_column(
        "message_logs", sa.Column("sender", sa.String(length=20), nullable=True)
    )
    op.create_foreign_key(
        "fk_message_logs_business_id_businesses",
        "message_logs",
        "businesses",
        ["business_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_message_logs_business_id", "message_logs", ["business_id"])


def downgrade() -> None:
    op.drop_index("ix_message_logs_business_id", table_name="message_logs")
    op.drop_constraint(
        "fk_message_logs_business_id_businesses", "message_logs", type_="foreignkey"
    )
    op.drop_column("message_logs", "sender")
    op.drop_column("message_logs", "business_id")

    op.drop_index("ix_business_hours_business_id", table_name="business_hours")
    op.drop_table("business_hours")

    op.drop_index("ix_businesses_user_id", table_name="businesses")
    op.drop_table("businesses")
