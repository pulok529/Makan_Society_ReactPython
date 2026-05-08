from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.accounting.schemas import (
    AccountCreate,
    AccountRead,
    AccountUpdate,
    AccountingSummary,
    ExpenseEntryCreate,
    ExpenseEntryRead,
    AccountingVoucherCreate,
    AccountingVoucherRead,
    IncomeExpenseComparisonReport,
    IncomeEntryCreate,
    IncomeEntryRead,
    IncomeExpenseEntryCreate,
    IncomeExpenseEntryRead,
    IncomeTransferPendingRead,
)
from app.modules.accounting.service import AccountingService
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.auth.models import User

router = APIRouter(prefix="/accounting", tags=["accounting"])


@router.get("/accounts", response_model=list[AccountRead])
def list_accounts(
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AccountRead]:
    return AccountingService(db).list_accounts()


@router.post(
    "/accounts",
    response_model=AccountRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("admin:manage"))],
)
def create_account(
    payload: AccountCreate,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountRead:
    return AccountingService(db).create_account(payload)


@router.put(
    "/accounts/{account_id}",
    response_model=AccountRead,
    dependencies=[Depends(require_permission("admin:manage"))],
)
def update_account(
    account_id: int,
    payload: AccountUpdate,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountRead:
    return AccountingService(db).update_account(account_id, payload)


@router.delete(
    "/accounts/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("admin:manage"))],
)
def delete_account(
    account_id: int,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    AccountingService(db).delete_account(account_id)


@router.get("/entries", response_model=list[IncomeExpenseEntryRead])
def list_entries(
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[IncomeExpenseEntryRead]:
    return AccountingService(db).list_entries()


@router.post(
    "/entries",
    response_model=IncomeExpenseEntryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("billing:manage"))],
)
def create_entry(
    payload: IncomeExpenseEntryCreate,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IncomeExpenseEntryRead:
    return AccountingService(db).create_entry(payload)


@router.delete(
    "/entries/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("billing:manage"))],
)
def delete_entry(
    entry_id: int,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    AccountingService(db).delete_entry(entry_id)


@router.get("/summary", response_model=AccountingSummary)
def get_summary(
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountingSummary:
    return AccountingService(db).summary()


@router.get("/income-transfer-pending", response_model=list[IncomeTransferPendingRead])
def pending_income_transfers(
    coa_id: int | None = None,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[IncomeTransferPendingRead]:
    return AccountingService(db).pending_income_transfers(coa_id=coa_id)


@router.get("/income", response_model=list[IncomeEntryRead])
def list_income(
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[IncomeEntryRead]:
    return AccountingService(db).list_income()


@router.post(
    "/income",
    response_model=IncomeEntryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("billing:manage"))],
)
def create_income(
    payload: IncomeEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IncomeEntryRead:
    return AccountingService(db).create_income(payload, current_user.id)


@router.get("/expense", response_model=list[ExpenseEntryRead])
def list_expense(
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ExpenseEntryRead]:
    return AccountingService(db).list_expense()


@router.post(
    "/expense",
    response_model=ExpenseEntryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("billing:manage"))],
)
def create_expense(
    payload: ExpenseEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExpenseEntryRead:
    return AccountingService(db).create_expense(payload, current_user.id)


@router.get("/vouchers/{voucher_type}", response_model=list[AccountingVoucherRead])
def list_vouchers(
    voucher_type: str,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AccountingVoucherRead]:
    return AccountingService(db).list_vouchers(voucher_type)


@router.post(
    "/vouchers/{voucher_type}",
    response_model=AccountingVoucherRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("billing:manage"))],
)
def create_voucher(
    voucher_type: str,
    payload: AccountingVoucherCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountingVoucherRead:
    return AccountingService(db).create_voucher(voucher_type, payload, current_user.id)


@router.get("/income-expense-report", response_model=IncomeExpenseComparisonReport)
def income_expense_report(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IncomeExpenseComparisonReport:
    return AccountingService(db).income_expense_report(from_date=from_date, to_date=to_date)
