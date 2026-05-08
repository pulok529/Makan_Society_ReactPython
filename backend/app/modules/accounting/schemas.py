from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class AccountCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=200)
    account_type: str = Field(pattern="^(income|expense|both|income_expense)$")
    is_active: bool = True


class AccountUpdate(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=200)
    account_type: str = Field(pattern="^(income|expense|both|income_expense)$")
    is_active: bool = True


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    account_type: str
    is_active: bool


class IncomeExpenseEntryCreate(BaseModel):
    account_id: int | None = None
    entry_type: str = Field(pattern="^(income|expense)$")
    amount: float = Field(gt=0)
    remarks: str | None = None


class IncomeExpenseEntryRead(BaseModel):
    id: int
    account_id: int | None
    account_name: str | None
    entry_type: str
    amount: float
    remarks: str | None
    created_at: datetime


class AccountingSummary(BaseModel):
    total_income: float
    total_expense: float
    net_balance: float


class IncomeTransferPendingRead(BaseModel):
    billing_detail_id: int
    invoice_no: str
    member_name: str
    coa_id: int
    amount: float
    head_name: str
    period_display: str | None


class IncomeEntryCreate(BaseModel):
    income_date: date
    coa_id: int
    amount: float = Field(gt=0)
    remarks: str | None = None


class IncomeEntryRead(BaseModel):
    id: int
    income_date: date
    coa_id: int
    coa_name: str | None
    amount: float
    remarks: str | None
    created_at: datetime


class ExpenseEntryCreate(BaseModel):
    expense_date: date
    coa_id: int
    amount: float = Field(gt=0)
    remarks: str | None = None


class ExpenseEntryRead(BaseModel):
    id: int
    expense_date: date
    coa_id: int
    coa_name: str | None
    amount: float
    remarks: str | None
    created_at: datetime


class AccountingVoucherLineCreate(BaseModel):
    coa_id: int
    amount: float = Field(gt=0)
    remarks: str | None = None


class AccountingVoucherCreate(BaseModel):
    voucher_date: date
    remarks: str | None = None
    lines: list[AccountingVoucherLineCreate] = Field(min_length=1)


class AccountingVoucherLineRead(BaseModel):
    id: int
    coa_id: int
    coa_name: str | None
    amount: float
    remarks: str | None


class AccountingVoucherRead(BaseModel):
    id: int
    voucher_no: str
    voucher_type: str
    voucher_date: date
    total_amount: float
    remarks: str | None
    created_at: datetime
    created_by: int | None
    lines: list[AccountingVoucherLineRead]


class IncomeExpenseReportSection(BaseModel):
    rows: list[dict[str, str | float | int | None]]
    subtotal: float


class IncomeExpenseComparisonReport(BaseModel):
    from_date: date | None
    to_date: date | None
    income: IncomeExpenseReportSection
    expense: IncomeExpenseReportSection
    net_amount: float
