"""add income voucher tracking to billing invoice details

Revision ID: 20260510_01
Revises: 20260505_01
Create Date: 2026-05-10
"""

from alembic import op
import sqlalchemy as sa


revision = "20260510_01"
down_revision = "20260505_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "billing_invoice_details",
        sa.Column("IncomeVoucherID", sa.Integer(), nullable=True),
        schema="billing",
    )
    op.create_foreign_key(
        "fk_billing_invoice_details_income_voucher",
        "billing_invoice_details",
        "accounting_vouchers",
        ["IncomeVoucherID"],
        ["VoucherID"],
        source_schema="billing",
        referent_schema="accounting",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_billing_invoice_details_income_voucher",
        "billing_invoice_details",
        schema="billing",
        type_="foreignkey",
    )
    op.drop_column("billing_invoice_details", "IncomeVoucherID", schema="billing")
