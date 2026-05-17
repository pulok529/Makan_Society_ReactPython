from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class BillingPeriodCreate(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    starts_on: date
    ends_on: date


class BillingPeriodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    year: int
    month: int
    period_name: str
    starts_on: date
    ends_on: date
    is_closed: bool


class ChargeItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    package_id: int | None
    package_name: str | None
    item_type: str
    description: str | None
    quantity: int
    unit_amount: float
    line_amount: float


class ChargeRead(BaseModel):
    id: int
    member_id: int
    member_name: str
    member_code: str
    billing_period_id: int | None
    billing_period_name: str | None
    charge_type: str
    status: str
    total_amount: float
    discount_amount: float
    net_amount: float
    due_amount: float
    created_at: datetime
    items: list[ChargeItemRead]


class BillingGenerationRequest(BaseModel):
    billing_period_id: int
    charge_type: str = "monthly"


class ReceiptPaymentLineCreate(BaseModel):
    charge_id: int
    amount: float = Field(gt=0)


class ReceiptCreate(BaseModel):
    member_id: int
    payment_date: date
    notes: str | None = None
    discount_amount: float = Field(default=0, ge=0)
    lines: list[ReceiptPaymentLineCreate]


class ReceiptLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    charge_id: int | None
    charge_item_id: int | None
    line_type: str
    amount: float


class ReceiptRead(BaseModel):
    id: int
    receipt_no: str
    member_id: int | None
    member_name: str | None
    collected_by_user_id: int | None
    receipt_type: str
    payment_date: date
    subtotal_amount: float
    discount_amount: float
    total_amount: float
    notes: str | None
    created_at: datetime
    lines: list[ReceiptLineRead]


class BillingMemberSummary(BaseModel):
    member_id: int
    member_code: str
    member_name: str
    total_charged: float
    total_due: float
    open_charge_count: int


class BillingDashboardRead(BaseModel):
    total_members_with_due: int
    total_due_amount: float
    total_open_charges: int
    total_receipts: int


class BillingHeadCreate(BaseModel):
    head_name: str = Field(min_length=2, max_length=150)
    head_type: str = Field(pattern="^(Period|OneTime)$")
    billing_mode: str = Field(pattern="^(Mandatory|Optional)$")
    fee_amount: float = Field(ge=0)
    effective_from_month: int | None = Field(default=None, ge=1, le=12)
    effective_from_year: int | None = Field(default=None, ge=1900, le=2100)
    effective_from_date: date | None = None
    is_active: bool = True


class BillingHeadRead(BillingHeadCreate):
    id: int
    created_at: datetime
    created_by: int | None


class BillingHeadMappingCreate(BaseModel):
    billing_head_id: int
    coa_id: int
    is_active: bool = True


class BillingHeadMappingRead(BaseModel):
    id: int
    billing_head_id: int
    billing_head_name: str
    coa_id: int
    coa_name: str
    is_active: bool
    created_at: datetime
    created_by: int | None


class BillingDueLineRead(BaseModel):
    member_id: int
    billing_head_id: int
    head_name: str
    head_type: str
    billing_mode: str
    period_date: date | None
    period_display: str | None
    plot_count: int
    base_fee_amount: float
    fee_amount: float
    paid_amount: float
    due_amount: float
    coa_id_snapshot: int | None


class BillingInvoiceLineCreate(BaseModel):
    billing_head_id: int
    period_date: date | None = None
    fee_amount: float = Field(gt=0)
    receive_amount: float = Field(default=0, ge=0)
    discount_amount: float = Field(default=0, ge=0)


class BillingInvoiceCreate(BaseModel):
    member_id: int
    invoice_date: date
    discount_amount: float = Field(default=0, ge=0)
    lines: list[BillingInvoiceLineCreate] = Field(min_length=1)


class BillingInvoiceDetailRead(BaseModel):
    id: int
    invoice_id: int
    member_id: int
    billing_head_id: int
    head_name_snapshot: str
    head_type: str
    period_date: date | None
    period_display: str | None
    fee_amount: float
    receive_amount: float
    due_amount: float
    discount_amount: float
    coa_id_snapshot: int | None
    income_voucher_id: int | None
    is_income_transferred: bool
    created_at: datetime
    created_by: int | None


class BillingInvoiceRead(BaseModel):
    id: int
    invoice_no: str
    member_id: int
    member_name: str
    invoice_date: date
    subtotal_amount: float
    discount_amount: float
    net_amount: float
    total_receive_amount: float
    total_due_amount: float
    is_cancelled: bool
    cancel_reason: str | None
    created_at: datetime
    created_by: int | None
    details: list[BillingInvoiceDetailRead]


class BillingInvoiceCancel(BaseModel):
    cancel_reason: str = Field(min_length=2, max_length=255)


class BillingReportRow(BaseModel):
    data: dict[str, str | int | float | None]


class BillingReportRead(BaseModel):
    report_type: str
    row_count: int
    rows: list[dict[str, str | int | float | None]]
