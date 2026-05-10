from datetime import date, datetime

from pydantic import BaseModel, Field


class ReportFilter(BaseModel):
    from_date: date | None = None
    to_date: date | None = None
    member_id: int | None = None
    category_id: int | None = None
    billing_period_id: int | None = None
    plot_no: str | None = None


class DueMemberRow(BaseModel):
    member_id: int
    member_code: str
    member_name: str
    category_name: str | None
    cell_no: str | None
    total_charged: float
    total_due: float
    open_charge_count: int


class CollectionRow(BaseModel):
    member_id: int | None
    member_code: str | None
    member_name: str | None
    receipt_no: str
    payment_date: date
    total_amount: float
    discount_amount: float


class ChargeRegisterRow(BaseModel):
    charge_id: int
    created_at: datetime
    member_id: int
    member_code: str
    member_name: str
    billing_period_name: str | None
    charge_type: str
    status: str
    net_amount: float
    due_amount: float


class MemberRegisterRow(BaseModel):
    member_id: int
    member_code: str
    full_name: str
    category_name: str | None
    cell_no: str | None
    email: str | None
    joined_on: date | None
    is_active: bool
    active_package_name: str | None


class TotalCollectionRow(BaseModel):
    member_id: int
    member_code: str
    member_name: str
    plot_no: str | None
    total_collection_amount: float


class TotalDueRow(BaseModel):
    member_id: int
    member_code: str
    member_name: str
    plot_no: str | None
    total_due_amount: float


class SingleMemberDueHistoryRow(BaseModel):
    head_name: str
    period_display: str | None
    total_bill: float
    paid_amount: float
    due_amount: float


class SingleMemberPaymentHistoryRow(BaseModel):
    receipt_no: str
    payment_date: date
    amount: float
    discount_amount: float


class SingleMemberStatementReport(BaseModel):
    member_id: int
    member_code: str
    member_name: str
    plot_no: str | None
    total_bill: float
    paid_amount: float
    due_amount: float
    applied_filters: dict[str, str] = Field(default_factory=dict)
    due_history: list[SingleMemberDueHistoryRow]
    payment_history: list[SingleMemberPaymentHistoryRow]


class ReceiptDetailLine(BaseModel):
    line_type: str
    amount: float
    charge_id: int | None


class ReceiptDetailReport(BaseModel):
    receipt_id: int
    receipt_no: str
    payment_date: date
    member_name: str | None
    member_code: str | None
    subtotal_amount: float
    discount_amount: float
    total_amount: float
    applied_filters: dict[str, str] = Field(default_factory=dict)
    lines: list[ReceiptDetailLine]


class ReportEnvelope(BaseModel):
    report_type: str
    title: str
    generated_at: datetime
    row_count: int
    totals: dict[str, float | int]
    applied_filters: dict[str, str] = Field(default_factory=dict)
    rows: list[dict]


class ExportRequest(BaseModel):
    format: str = Field(pattern="^(json|html|xlsx)$")
    filters: ReportFilter = Field(default_factory=ReportFilter)
