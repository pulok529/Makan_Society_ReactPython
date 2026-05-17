"""add member plot and entry timestamp plus billing mode

Revision ID: 20260516_01
Revises: 20260510_01
Create Date: 2026-05-16
"""

from alembic import op
import sqlalchemy as sa


revision = "20260516_01"
down_revision = "20260510_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    member_columns = {column["name"] for column in inspector.get_columns("members", schema="society")}
    member_indexes = {index["name"] for index in inspector.get_indexes("members", schema="society")}
    billing_head_columns = {column["name"] for column in inspector.get_columns("billing_heads", schema="billing")}

    if "plot_no" not in member_columns:
        op.add_column("members", sa.Column("plot_no", sa.String(length=100), nullable=True), schema="society")
    if "ix_society_members_plot_no" not in member_indexes:
        op.create_index("ix_society_members_plot_no", "members", ["plot_no"], unique=False, schema="society")

    if "entry_at" not in member_columns:
        op.add_column(
            "members",
            sa.Column("entry_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
            schema="society",
        )
    op.execute("UPDATE society.members SET entry_at = ISNULL(created_at, CURRENT_TIMESTAMP) WHERE entry_at IS NULL")
    op.alter_column("members", "entry_at", existing_type=sa.DateTime(timezone=True), nullable=False, schema="society")

    if "BillingMode" not in billing_head_columns:
        op.add_column(
            "billing_heads",
            sa.Column("BillingMode", sa.String(length=20), nullable=False, server_default="Mandatory"),
            schema="billing",
        )

    op.execute(
        """
        UPDATE society.members
        SET plot_no = CASE
            WHEN plot_no IS NOT NULL AND LTRIM(RTRIM(plot_no)) <> '' THEN plot_no
            WHEN member_id_text IS NULL OR LTRIM(RTRIM(member_id_text)) = '' THEN NULL
            WHEN member_id_text LIKE 'Reg-%' THEN SUBSTRING(member_id_text, 5, LEN(member_id_text))
            ELSE member_id_text
        END
        WHERE plot_no IS NULL OR LTRIM(RTRIM(plot_no)) = ''
        """
    )


def downgrade() -> None:
    op.drop_column("billing_heads", "BillingMode", schema="billing")
    op.drop_column("members", "entry_at", schema="society")
    op.drop_index("ix_society_members_plot_no", table_name="members", schema="society")
    op.drop_column("members", "plot_no", schema="society")
