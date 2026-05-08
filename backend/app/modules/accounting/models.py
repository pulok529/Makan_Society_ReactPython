from datetime import datetime

from datetime import date

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = {"schema": "accounting"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    account_type: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class IncomeExpenseEntry(Base):
    __tablename__ = "income_expense_entries"
    __table_args__ = {"schema": "accounting"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounting.accounts.id"))
    entry_type: Mapped[str] = mapped_column(String(30))
    amount: Mapped[float] = mapped_column(Numeric(18, 2))
    remarks: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IncomeEntry(Base):
    __tablename__ = "income_entries"
    __table_args__ = {"schema": "accounting"}

    id: Mapped[int] = mapped_column("IncomeID", primary_key=True, autoincrement=True)
    income_date: Mapped[date] = mapped_column("IncomeDate", Date)
    coa_id: Mapped[int] = mapped_column("COAID", ForeignKey("accounting.accounts.id"))
    amount: Mapped[float] = mapped_column("Amount", Numeric(18, 2))
    remarks: Mapped[str | None] = mapped_column("Remarks", String(255))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[int | None] = mapped_column("CreatedBy", ForeignKey("auth.users.id"))


class IncomeEntryDetail(Base):
    __tablename__ = "income_entry_details"
    __table_args__ = {"schema": "accounting"}

    id: Mapped[int] = mapped_column("IncomeDetailID", primary_key=True, autoincrement=True)
    income_id: Mapped[int] = mapped_column("IncomeID", ForeignKey("accounting.income_entries.IncomeID", ondelete="CASCADE"))
    billing_detail_id: Mapped[int] = mapped_column("BillingDetailID", ForeignKey("billing.billing_invoice_details.InvoiceDetailID"))
    amount: Mapped[float] = mapped_column("Amount", Numeric(18, 2))


class ExpenseEntry(Base):
    __tablename__ = "expense_entries"
    __table_args__ = {"schema": "accounting"}

    id: Mapped[int] = mapped_column("ExpenseID", primary_key=True, autoincrement=True)
    expense_date: Mapped[date] = mapped_column("ExpenseDate", Date)
    coa_id: Mapped[int] = mapped_column("COAID", ForeignKey("accounting.accounts.id"))
    amount: Mapped[float] = mapped_column("Amount", Numeric(18, 2))
    remarks: Mapped[str | None] = mapped_column("Remarks", String(255))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[int | None] = mapped_column("CreatedBy", ForeignKey("auth.users.id"))


class AccountingVoucher(Base):
    __tablename__ = "accounting_vouchers"
    __table_args__ = {"schema": "accounting"}

    id: Mapped[int] = mapped_column("VoucherID", primary_key=True, autoincrement=True)
    voucher_no: Mapped[str] = mapped_column("VoucherNo", String(50), unique=True, index=True)
    voucher_type: Mapped[str] = mapped_column("VoucherType", String(20))
    voucher_date: Mapped[date] = mapped_column("VoucherDate", Date)
    total_amount: Mapped[float] = mapped_column("TotalAmount", Numeric(18, 2), default=0)
    remarks: Mapped[str | None] = mapped_column("Remarks", String(255))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[int | None] = mapped_column("CreatedBy", ForeignKey("auth.users.id"))


class AccountingVoucherDetail(Base):
    __tablename__ = "accounting_voucher_details"
    __table_args__ = {"schema": "accounting"}

    id: Mapped[int] = mapped_column("VoucherDetailID", primary_key=True, autoincrement=True)
    voucher_id: Mapped[int] = mapped_column("VoucherID", ForeignKey("accounting.accounting_vouchers.VoucherID", ondelete="CASCADE"))
    coa_id: Mapped[int] = mapped_column("COAID", ForeignKey("accounting.accounts.id"))
    amount: Mapped[float] = mapped_column("Amount", Numeric(18, 2))
    remarks: Mapped[str | None] = mapped_column("Remarks", String(255))
