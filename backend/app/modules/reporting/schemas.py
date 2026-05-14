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
    plot_no: str | None
    category_name: str | None
    national_id: str | None
    cell_no: str | None
    joined_on: date | None
    is_active: bool
    active_package_name: str | None
    total_collection_amount: float
    total_due_amount: float


class IncomeDetailRow(BaseModel):
    income_id: int
    income_date: date
    account_code: str | None
    account_name: str | None
    amount: float
    remarks: str | None
    created_at: datetime


class ExpenseDetailRow(BaseModel):
    expense_id: int
    expense_date: date
    account_code: str | None
    account_name: str | None
    amount: float
    remarks: str | None
    created_at: datetime


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
    notes: str | None


class MemberSmsHistoryRow(BaseModel):
    created_at: datetime
    recipient: str
    template_name: str | None
    message_body: str
    status: str


class MemberInformationSummary(BaseModel):
    member_code: str
    full_name: str
    plot_no: str | None
    category_name: str | None
    national_id: str | None
    cell_no: str | None
    email: str | None
    member_class: str | None
    joined_on: date | None
    is_active: bool
    father_name: str | None
    mother_name: str | None
    present_address: str | None
    permanent_address: str | None
    reference: str | None
    nominee_name: str | None
    nominee_cell: str | None
    active_package_name: str | None
    total_collection_amount: float
    total_due_amount: float


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


class MemberInformationDetailReport(BaseModel):
    member_id: int
    applied_filters: dict[str, str] = Field(default_factory=dict)
    member_info: MemberInformationSummary
    payment_history: list[SingleMemberPaymentHistoryRow]
    due_history: list[SingleMemberDueHistoryRow]
    sms_history: list[MemberSmsHistoryRow]


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
