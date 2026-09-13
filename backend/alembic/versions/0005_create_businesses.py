"""Create businesses, add business_id + sender to message_logs.

Revision ID: 0005_create_businesses
Revises: 0003_create_message_logs
Create Date: 2026-09-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_create_businesses"
down_revision: str | None = "0003_create_message_logs"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "businesses",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("evolution_instance_name", sa.String(length=255), nullable=True),
        sa.Column("business_type", sa.String(length=30), nullable=False),
        sa.Column("contact_phone_number", sa.String(length=20), nullable=False),
        sa.Column("plan", sa.String(length=30), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending_setup",
        ),
        sa.Column(
            "visibility",
            sa.String(length=20),
            nullable=False,
            server_default="public",
        ),
        sa.Column("user_id", sa.Integer(), nullable=True),
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
        sa.UniqueConstraint(
            "contact_phone_number", name="uq_businesses_contact_phone_number"
        ),
    )
    op.create_index("ix_businesses_user_id", "businesses", ["user_id"])

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
    op.create_index("ix_phone_numbers_business_id", "phone_numbers", ["business_id"])

    op.drop_constraint("uq_phone_numbers_phone_number", "phone_numbers", type_="unique")
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

    op.drop_index("ix_message_logs_business_id", table_name="message_logs")
    op.drop_constraint(
        "fk_message_logs_business_id_businesses", "message_logs", type_="foreignkey"
    )
    op.drop_column("message_logs", "sender")
    op.drop_column("message_logs", "business_id")

    op.drop_index("ix_businesses_user_id", table_name="businesses")
    op.drop_table("businesses")
