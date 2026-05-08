from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BillingPeriod(Base):
    __tablename__ = "billing_periods"
    __table_args__ = (UniqueConstraint("year", "month"), {"schema": "billing"})

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    year: Mapped[int]
    month: Mapped[int]
    period_name: Mapped[str] = mapped_column(String(30))
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date] = mapped_column(Date)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Charge(Base):
    __tablename__ = "charges"
    __table_args__ = {"schema": "billing"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("society.members.id"))
    billing_period_id: Mapped[int | None] = mapped_column(ForeignKey("billing.billing_periods.id"))
    charge_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="open")
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2))
    discount_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    net_amount: Mapped[float] = mapped_column(Numeric(18, 2))
    due_amount: Mapped[float] = mapped_column(Numeric(18, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChargeItem(Base):
    __tablename__ = "charge_items"
    __table_args__ = {"schema": "billing"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    charge_id: Mapped[int] = mapped_column(ForeignKey("billing.charges.id", ondelete="CASCADE"))
    package_id: Mapped[int | None] = mapped_column(ForeignKey("society.packages.id"))
    item_type: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(default=1)
    unit_amount: Mapped[float] = mapped_column(Numeric(18, 2))
    line_amount: Mapped[float] = mapped_column(Numeric(18, 2))


class Receipt(Base):
    __tablename__ = "receipts"
    __table_args__ = {"schema": "billing"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    receipt_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    member_id: Mapped[int | None] = mapped_column(ForeignKey("society.members.id"))
    collected_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("auth.users.id"))
    receipt_type: Mapped[str] = mapped_column(String(50))
    payment_date: Mapped[date] = mapped_column(Date)
    subtotal_amount: Mapped[float] = mapped_column(Numeric(18, 2))
    discount_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2))
    notes: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReceiptLine(Base):
    __tablename__ = "receipt_lines"
    __table_args__ = {"schema": "billing"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("billing.receipts.id", ondelete="CASCADE"))
    charge_id: Mapped[int | None] = mapped_column(ForeignKey("billing.charges.id"))
    charge_item_id: Mapped[int | None] = mapped_column(ForeignKey("billing.charge_items.id"))
    line_type: Mapped[str] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Numeric(18, 2))


class BillingHead(Base):
    __tablename__ = "billing_heads"
    __table_args__ = (
        Index("ix_billing_heads_is_active", "IsActive"),
        {"schema": "billing"},
    )

    id: Mapped[int] = mapped_column("BillingHeadID", primary_key=True, autoincrement=True)
    head_name: Mapped[str] = mapped_column("HeadName", String(150), unique=True)
    head_type: Mapped[str] = mapped_column("HeadType", String(20))
    fee_amount: Mapped[float] = mapped_column("FeeAmount", Numeric(18, 2))
    effective_from_month: Mapped[int | None] = mapped_column("EffectiveFromMonth")
    effective_from_year: Mapped[int | None] = mapped_column("EffectiveFromYear")
    effective_from_date: Mapped[date | None] = mapped_column("EffectiveFromDate", Date)
    is_active: Mapped[bool] = mapped_column("IsActive", Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[int | None] = mapped_column("CreatedBy", ForeignKey("auth.users.id"))


class BillingHeadCoaMapping(Base):
    __tablename__ = "billing_head_coa_mappings"
    __table_args__ = (
        Index("ix_billing_head_coa_mappings_head", "BillingHeadID", "IsActive"),
        Index("ix_billing_head_coa_mappings_coa", "COAID"),
        {"schema": "billing"},
    )

    id: Mapped[int] = mapped_column("MappingID", primary_key=True, autoincrement=True)
    billing_head_id: Mapped[int] = mapped_column("BillingHeadID", ForeignKey("billing.billing_heads.BillingHeadID"))
    coa_id: Mapped[int] = mapped_column("COAID", ForeignKey("accounting.accounts.id"))
    is_active: Mapped[bool] = mapped_column("IsActive", Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[int | None] = mapped_column("CreatedBy", ForeignKey("auth.users.id"))


class BillingInvoice(Base):
    __tablename__ = "billing_invoices"
    __table_args__ = (
        Index("ix_billing_invoices_member", "MemberID"),
        Index("ix_billing_invoices_invoice_date", "InvoiceDate"),
        {"schema": "billing"},
    )

    id: Mapped[int] = mapped_column("InvoiceID", primary_key=True, autoincrement=True)
    invoice_no: Mapped[str] = mapped_column("InvoiceNo", String(50), unique=True, index=True)
    member_id: Mapped[int] = mapped_column("MemberID", ForeignKey("society.members.id"))
    invoice_date: Mapped[date] = mapped_column("InvoiceDate", Date)
    subtotal_amount: Mapped[float] = mapped_column("SubtotalAmount", Numeric(18, 2))
    discount_amount: Mapped[float] = mapped_column("DiscountAmount", Numeric(18, 2), default=0)
    net_amount: Mapped[float] = mapped_column("NetAmount", Numeric(18, 2))
    total_receive_amount: Mapped[float] = mapped_column("TotalReceiveAmount", Numeric(18, 2), default=0)
    total_due_amount: Mapped[float] = mapped_column("TotalDueAmount", Numeric(18, 2), default=0)
    is_cancelled: Mapped[bool] = mapped_column("IsCancelled", Boolean, default=False, nullable=False)
    cancel_reason: Mapped[str | None] = mapped_column("CancelReason", String(255))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[int | None] = mapped_column("CreatedBy", ForeignKey("auth.users.id"))


class BillingInvoiceDetail(Base):
    __tablename__ = "billing_invoice_details"
    __table_args__ = (
        Index("ix_billing_invoice_details_member", "MemberID"),
        Index("ix_billing_invoice_details_head_period", "BillingHeadID", "PeriodDate"),
        Index("ix_billing_invoice_details_coa", "COAIDSnapshot"),
        {"schema": "billing"},
    )

    id: Mapped[int] = mapped_column("InvoiceDetailID", primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column("InvoiceID", ForeignKey("billing.billing_invoices.InvoiceID", ondelete="CASCADE"))
    member_id: Mapped[int] = mapped_column("MemberID", ForeignKey("society.members.id"))
    billing_head_id: Mapped[int] = mapped_column("BillingHeadID", ForeignKey("billing.billing_heads.BillingHeadID"))
    head_name_snapshot: Mapped[str] = mapped_column("HeadNameSnapshot", String(150))
    head_type: Mapped[str] = mapped_column("HeadType", String(20))
    period_date: Mapped[date | None] = mapped_column("PeriodDate", Date)
    period_display: Mapped[str | None] = mapped_column("PeriodDisplay", String(20))
    fee_amount: Mapped[float] = mapped_column("FeeAmount", Numeric(18, 2))
    receive_amount: Mapped[float] = mapped_column("ReceiveAmount", Numeric(18, 2), default=0)
    due_amount: Mapped[float] = mapped_column("DueAmount", Numeric(18, 2), default=0)
    discount_amount: Mapped[float] = mapped_column("DiscountAmount", Numeric(18, 2), default=0)
    coa_id_snapshot: Mapped[int | None] = mapped_column("COAIDSnapshot", ForeignKey("accounting.accounts.id"))
    is_income_transferred: Mapped[bool] = mapped_column("IsIncomeTransferred", Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[int | None] = mapped_column("CreatedBy", ForeignKey("auth.users.id"))


class BillingReportExport(Base):
    __tablename__ = "billing_report_exports"
    __table_args__ = {"schema": "billing"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    report_type: Mapped[str] = mapped_column(String(100))
    parameters: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
