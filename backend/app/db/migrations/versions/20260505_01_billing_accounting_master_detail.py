"""billing accounting master detail

Revision ID: 20260505_01
Revises: 20260428_01
Create Date: 2026-05-05 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260505_01"
down_revision: Union[str, Sequence[str], None] = "20260428_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "billing_heads",
        sa.Column("BillingHeadID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("HeadName", sa.String(length=150), nullable=False),
        sa.Column("HeadType", sa.String(length=20), nullable=False),
        sa.Column("FeeAmount", sa.Numeric(18, 2), nullable=False),
        sa.Column("EffectiveFromMonth", sa.Integer(), nullable=True),
        sa.Column("EffectiveFromYear", sa.Integer(), nullable=True),
        sa.Column("EffectiveFromDate", sa.Date(), nullable=True),
        sa.Column("IsActive", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("CreatedAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("CreatedBy", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["CreatedBy"], ["auth.users.id"]),
        sa.PrimaryKeyConstraint("BillingHeadID"),
        sa.UniqueConstraint("HeadName"),
        schema="billing",
    )
    op.create_index("ix_billing_heads_is_active", "billing_heads", ["IsActive"], schema="billing")

    op.create_table(
        "billing_head_coa_mappings",
        sa.Column("MappingID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("BillingHeadID", sa.Integer(), nullable=False),
        sa.Column("COAID", sa.Integer(), nullable=False),
        sa.Column("IsActive", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("CreatedAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("CreatedBy", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["BillingHeadID"], ["billing.billing_heads.BillingHeadID"]),
        sa.ForeignKeyConstraint(["COAID"], ["accounting.accounts.id"]),
        sa.ForeignKeyConstraint(["CreatedBy"], ["auth.users.id"]),
        sa.PrimaryKeyConstraint("MappingID"),
        schema="billing",
    )
    op.create_index("ix_billing_head_coa_mappings_head", "billing_head_coa_mappings", ["BillingHeadID", "IsActive"], schema="billing")
    op.create_index("ix_billing_head_coa_mappings_coa", "billing_head_coa_mappings", ["COAID"], schema="billing")

    op.create_table(
        "billing_invoices",
        sa.Column("InvoiceID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("InvoiceNo", sa.String(length=50), nullable=False),
        sa.Column("MemberID", sa.Integer(), nullable=False),
        sa.Column("InvoiceDate", sa.Date(), nullable=False),
        sa.Column("SubtotalAmount", sa.Numeric(18, 2), nullable=False),
        sa.Column("DiscountAmount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("NetAmount", sa.Numeric(18, 2), nullable=False),
        sa.Column("TotalReceiveAmount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("TotalDueAmount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("IsCancelled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("CancelReason", sa.String(length=255), nullable=True),
        sa.Column("CreatedAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("CreatedBy", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["MemberID"], ["society.members.id"]),
        sa.ForeignKeyConstraint(["CreatedBy"], ["auth.users.id"]),
        sa.PrimaryKeyConstraint("InvoiceID"),
        sa.UniqueConstraint("InvoiceNo"),
        schema="billing",
    )
    op.create_index("ix_billing_invoices_member", "billing_invoices", ["MemberID"], schema="billing")
    op.create_index("ix_billing_invoices_invoice_date", "billing_invoices", ["InvoiceDate"], schema="billing")

    op.create_table(
        "billing_invoice_details",
        sa.Column("InvoiceDetailID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("InvoiceID", sa.Integer(), nullable=False),
        sa.Column("MemberID", sa.Integer(), nullable=False),
        sa.Column("BillingHeadID", sa.Integer(), nullable=False),
        sa.Column("HeadNameSnapshot", sa.String(length=150), nullable=False),
        sa.Column("HeadType", sa.String(length=20), nullable=False),
        sa.Column("PeriodDate", sa.Date(), nullable=True),
        sa.Column("PeriodDisplay", sa.String(length=20), nullable=True),
        sa.Column("FeeAmount", sa.Numeric(18, 2), nullable=False),
        sa.Column("ReceiveAmount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("DueAmount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("DiscountAmount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("COAIDSnapshot", sa.Integer(), nullable=True),
        sa.Column("IsIncomeTransferred", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("CreatedAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("CreatedBy", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["InvoiceID"], ["billing.billing_invoices.InvoiceID"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["MemberID"], ["society.members.id"]),
        sa.ForeignKeyConstraint(["BillingHeadID"], ["billing.billing_heads.BillingHeadID"]),
        sa.ForeignKeyConstraint(["COAIDSnapshot"], ["accounting.accounts.id"]),
        sa.ForeignKeyConstraint(["CreatedBy"], ["auth.users.id"]),
        sa.PrimaryKeyConstraint("InvoiceDetailID"),
        schema="billing",
    )
    op.create_index("ix_billing_invoice_details_member", "billing_invoice_details", ["MemberID"], schema="billing")
    op.create_index("ix_billing_invoice_details_head_period", "billing_invoice_details", ["BillingHeadID", "PeriodDate"], schema="billing")
    op.create_index("ix_billing_invoice_details_coa", "billing_invoice_details", ["COAIDSnapshot"], schema="billing")

    op.create_table(
        "income_entries",
        sa.Column("IncomeID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("IncomeDate", sa.Date(), nullable=False),
        sa.Column("COAID", sa.Integer(), nullable=False),
        sa.Column("Amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("Remarks", sa.String(length=255), nullable=True),
        sa.Column("CreatedAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("CreatedBy", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["COAID"], ["accounting.accounts.id"]),
        sa.ForeignKeyConstraint(["CreatedBy"], ["auth.users.id"]),
        sa.PrimaryKeyConstraint("IncomeID"),
        schema="accounting",
    )
    op.create_table(
        "income_entry_details",
        sa.Column("IncomeDetailID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("IncomeID", sa.Integer(), nullable=False),
        sa.Column("BillingDetailID", sa.Integer(), nullable=False),
        sa.Column("Amount", sa.Numeric(18, 2), nullable=False),
        sa.ForeignKeyConstraint(["IncomeID"], ["accounting.income_entries.IncomeID"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["BillingDetailID"], ["billing.billing_invoice_details.InvoiceDetailID"]),
        sa.PrimaryKeyConstraint("IncomeDetailID"),
        schema="accounting",
    )
    op.create_table(
        "expense_entries",
        sa.Column("ExpenseID", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ExpenseDate", sa.Date(), nullable=False),
        sa.Column("COAID", sa.Integer(), nullable=False),
        sa.Column("Amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("Remarks", sa.String(length=255), nullable=True),
        sa.Column("CreatedAt", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("CreatedBy", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["COAID"], ["accounting.accounts.id"]),
        sa.ForeignKeyConstraint(["CreatedBy"], ["auth.users.id"]),
        sa.PrimaryKeyConstraint("ExpenseID"),
        schema="accounting",
    )


def downgrade() -> None:
    op.drop_table("expense_entries", schema="accounting")
    op.drop_table("income_entry_details", schema="accounting")
    op.drop_table("income_entries", schema="accounting")
    op.drop_table("billing_invoice_details", schema="billing")
    op.drop_table("billing_invoices", schema="billing")
    op.drop_table("billing_head_coa_mappings", schema="billing")
    op.drop_table("billing_heads", schema="billing")
