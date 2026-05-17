"""add member plot count and billing due tracker

Revision ID: 20260517_01
Revises: 20260516_01
Create Date: 2026-05-17
"""

from alembic import op
import sqlalchemy as sa


revision = "20260517_01"
down_revision = "20260516_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    member_columns = {column["name"] for column in inspector.get_columns("members", schema="society")}
    if "plot_count" not in member_columns:
        op.add_column(
            "members",
            sa.Column("plot_count", sa.Integer(), nullable=False, server_default="1"),
            schema="society",
        )
        op.execute("UPDATE society.members SET plot_count = 1 WHERE plot_count IS NULL OR plot_count < 1")

    table_names = set(inspector.get_table_names(schema="billing"))
    if "billing_due_tracker" not in table_names:
        op.create_table(
            "billing_due_tracker",
            sa.Column("DueID", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("MemberID", sa.Integer(), sa.ForeignKey("society.members.id"), nullable=False),
            sa.Column("BillingHeadID", sa.Integer(), sa.ForeignKey("billing.billing_heads.BillingHeadID"), nullable=False),
            sa.Column("PeriodDate", sa.Date(), nullable=True),
            sa.Column("PeriodDisplay", sa.String(length=20), nullable=True),
            sa.Column("HeadNameSnapshot", sa.String(length=150), nullable=False),
            sa.Column("HeadType", sa.String(length=20), nullable=False),
            sa.Column("BillingMode", sa.String(length=20), nullable=False),
            sa.Column("PlotCountSnapshot", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("BaseFeeAmount", sa.Numeric(18, 2), nullable=False, server_default="0"),
            sa.Column("FeeAmount", sa.Numeric(18, 2), nullable=False, server_default="0"),
            sa.Column("PaidAmount", sa.Numeric(18, 2), nullable=False, server_default="0"),
            sa.Column("DiscountAmount", sa.Numeric(18, 2), nullable=False, server_default="0"),
            sa.Column("DueAmount", sa.Numeric(18, 2), nullable=False, server_default="0"),
            sa.Column("Status", sa.String(length=20), nullable=False, server_default="open"),
            sa.Column("LastInvoiceID", sa.Integer(), sa.ForeignKey("billing.billing_invoices.InvoiceID"), nullable=True),
            sa.Column("CreatedAt", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("UpdatedAt", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("MemberID", "BillingHeadID", "PeriodDate", name="uq_billing_due_tracker_member_head_period"),
            schema="billing",
        )
        op.create_index(
            "ix_billing_due_tracker_member_status",
            "billing_due_tracker",
            ["MemberID", "Status"],
            unique=False,
            schema="billing",
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    table_names = set(inspector.get_table_names(schema="billing"))
    if "billing_due_tracker" in table_names:
        op.drop_index("ix_billing_due_tracker_member_status", table_name="billing_due_tracker", schema="billing")
        op.drop_table("billing_due_tracker", schema="billing")

    member_columns = {column["name"] for column in inspector.get_columns("members", schema="society")}
    if "plot_count" in member_columns:
        op.drop_column("members", "plot_count", schema="society")
