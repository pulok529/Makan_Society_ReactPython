"""add transaction table indexes for server-side paging

Revision ID: 20260603_01
Revises: 20260520_01
Create Date: 2026-06-03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260603_01"
down_revision = "20260520_01"
branch_labels = None
depends_on = None


def _index_names(inspector, table_name: str, schema: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name, schema=schema)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    charge_indexes = _index_names(inspector, "charges", "billing")
    if "ix_billing_charges_created_at" not in charge_indexes:
        op.create_index("ix_billing_charges_created_at", "charges", ["created_at"], schema="billing")
    if "ix_billing_charges_member_due_created" not in charge_indexes:
        op.create_index("ix_billing_charges_member_due_created", "charges", ["member_id", "due_amount", "created_at"], schema="billing")

    receipt_indexes = _index_names(inspector, "receipts", "billing")
    if "ix_billing_receipts_payment_date_member" not in receipt_indexes:
        op.create_index("ix_billing_receipts_payment_date_member", "receipts", ["payment_date", "member_id"], schema="billing")

    invoice_indexes = _index_names(inspector, "billing_invoices", "billing")
    if "ix_billing_invoices_member_date_status" not in invoice_indexes:
        op.create_index("ix_billing_invoices_member_date_status", "billing_invoices", ["MemberID", "InvoiceDate", "IsCancelled"], schema="billing")

    income_indexes = _index_names(inspector, "income_entries", "accounting")
    if "ix_accounting_income_entries_date_coa" not in income_indexes:
        op.create_index("ix_accounting_income_entries_date_coa", "income_entries", ["IncomeDate", "COAID"], schema="accounting")

    expense_indexes = _index_names(inspector, "expense_entries", "accounting")
    if "ix_accounting_expense_entries_date_coa" not in expense_indexes:
        op.create_index("ix_accounting_expense_entries_date_coa", "expense_entries", ["ExpenseDate", "COAID"], schema="accounting")

    voucher_indexes = _index_names(inspector, "accounting_vouchers", "accounting")
    if "ix_accounting_vouchers_type_date" not in voucher_indexes:
        op.create_index("ix_accounting_vouchers_type_date", "accounting_vouchers", ["VoucherType", "VoucherDate"], schema="accounting")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    charge_indexes = _index_names(inspector, "charges", "billing")
    if "ix_billing_charges_created_at" in charge_indexes:
        op.drop_index("ix_billing_charges_created_at", table_name="charges", schema="billing")
    if "ix_billing_charges_member_due_created" in charge_indexes:
        op.drop_index("ix_billing_charges_member_due_created", table_name="charges", schema="billing")

    receipt_indexes = _index_names(inspector, "receipts", "billing")
    if "ix_billing_receipts_payment_date_member" in receipt_indexes:
        op.drop_index("ix_billing_receipts_payment_date_member", table_name="receipts", schema="billing")

    invoice_indexes = _index_names(inspector, "billing_invoices", "billing")
    if "ix_billing_invoices_member_date_status" in invoice_indexes:
        op.drop_index("ix_billing_invoices_member_date_status", table_name="billing_invoices", schema="billing")

    income_indexes = _index_names(inspector, "income_entries", "accounting")
    if "ix_accounting_income_entries_date_coa" in income_indexes:
        op.drop_index("ix_accounting_income_entries_date_coa", table_name="income_entries", schema="accounting")

    expense_indexes = _index_names(inspector, "expense_entries", "accounting")
    if "ix_accounting_expense_entries_date_coa" in expense_indexes:
        op.drop_index("ix_accounting_expense_entries_date_coa", table_name="expense_entries", schema="accounting")

    voucher_indexes = _index_names(inspector, "accounting_vouchers", "accounting")
    if "ix_accounting_vouchers_type_date" in voucher_indexes:
        op.drop_index("ix_accounting_vouchers_type_date", table_name="accounting_vouchers", schema="accounting")
