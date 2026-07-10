"""add_voided_invoice_tables

Revision ID: 9959268af13a
Revises: 20260603_03
Create Date: 2026-07-10 22:03:13.388345
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '9959268af13a'
down_revision: Union[str, Sequence[str], None] = '20260603_03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'billing_voided_invoices',
        sa.Column('VoidedInvoiceID', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('OriginalInvoiceID', sa.Integer(), nullable=False),
        sa.Column('InvoiceNo', sa.String(length=50), nullable=False),
        sa.Column('MemberID', sa.Integer(), nullable=False),
        sa.Column('InvoiceDate', sa.Date(), nullable=False),
        sa.Column('SubtotalAmount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('DiscountAmount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('NetAmount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('TotalReceiveAmount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('TotalDueAmount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('CancelReason', sa.String(length=255), nullable=True),
        sa.Column('CreatedAt', sa.DateTime(timezone=True), nullable=False),
        sa.Column('CreatedBy', sa.Integer(), nullable=True),
        sa.Column('VoidedAt', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('VoidedBy', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['MemberID'], ['society.members.id'], ),
        sa.ForeignKeyConstraint(['CreatedBy'], ['auth.users.id'], ),
        sa.ForeignKeyConstraint(['VoidedBy'], ['auth.users.id'], ),
        sa.PrimaryKeyConstraint('VoidedInvoiceID'),
        schema='billing'
    )
    op.create_index(op.f('ix_billing_voided_invoices_InvoiceNo'), 'billing_voided_invoices', ['InvoiceNo'], unique=False, schema='billing')
    op.create_index('ix_billing_voided_invoices_member', 'billing_voided_invoices', ['MemberID'], unique=False, schema='billing')
    op.create_index('ix_billing_voided_invoices_invoice_date', 'billing_voided_invoices', ['InvoiceDate'], unique=False, schema='billing')

    op.create_table(
        'billing_voided_invoice_details',
        sa.Column('VoidedInvoiceDetailID', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('VoidedInvoiceID', sa.Integer(), nullable=False),
        sa.Column('OriginalInvoiceDetailID', sa.Integer(), nullable=False),
        sa.Column('MemberID', sa.Integer(), nullable=False),
        sa.Column('BillingHeadID', sa.Integer(), nullable=False),
        sa.Column('HeadNameSnapshot', sa.String(length=150), nullable=False),
        sa.Column('HeadType', sa.String(length=20), nullable=False),
        sa.Column('PeriodDate', sa.Date(), nullable=True),
        sa.Column('PeriodDisplay', sa.String(length=20), nullable=True),
        sa.Column('FeeAmount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('ReceiveAmount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('DueAmount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('DiscountAmount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('COAIDSnapshot', sa.Integer(), nullable=True),
        sa.Column('IncomeVoucherID', sa.Integer(), nullable=True),
        sa.Column('IsIncomeTransferred', sa.Boolean(), nullable=False),
        sa.Column('CreatedAt', sa.DateTime(timezone=True), nullable=False),
        sa.Column('CreatedBy', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['BillingHeadID'], ['billing.billing_heads.BillingHeadID'], ),
        sa.ForeignKeyConstraint(['COAIDSnapshot'], ['accounting.accounts.id'], ),
        sa.ForeignKeyConstraint(['CreatedBy'], ['auth.users.id'], ),
        sa.ForeignKeyConstraint(['IncomeVoucherID'], ['accounting.accounting_vouchers.VoucherID'], ),
        sa.ForeignKeyConstraint(['MemberID'], ['society.members.id'], ),
        sa.ForeignKeyConstraint(['VoidedInvoiceID'], ['billing.billing_voided_invoices.VoidedInvoiceID'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('VoidedInvoiceDetailID'),
        schema='billing'
    )
    op.create_index('ix_billing_voided_invoice_details_member', 'billing_voided_invoice_details', ['MemberID'], unique=False, schema='billing')


def downgrade() -> None:
    op.drop_index('ix_billing_voided_invoice_details_member', table_name='billing_voided_invoice_details', schema='billing')
    op.drop_table('billing_voided_invoice_details', schema='billing')
    op.drop_index('ix_billing_voided_invoices_invoice_date', table_name='billing_voided_invoices', schema='billing')
    op.drop_index('ix_billing_voided_invoices_member', table_name='billing_voided_invoices', schema='billing')
    op.drop_index(op.f('ix_billing_voided_invoices_InvoiceNo'), table_name='billing_voided_invoices', schema='billing')
    op.drop_table('billing_voided_invoices', schema='billing')
