from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from datetime import date
from collections import defaultdict

from app.modules.accounting.models import Account, AccountingVoucher, AccountingVoucherDetail, ExpenseEntry, IncomeEntry, IncomeEntryDetail, IncomeExpenseEntry
from app.modules.accounting.repository import AccountingRepository
from app.modules.accounting.schemas import (
    AccountCreate,
    AccountUpdate,
    AccountRead,
    AccountingSummary,
    ExpenseEntryCreate,
    ExpenseEntryRead,
    AccountingVoucherCreate,
    AccountingVoucherRead,
    AccountingVoucherLineRead,
    IncomeExpenseComparisonReport,
    IncomeExpenseReportSection,
    IncomeEntryCreate,
    IncomeEntryRead,
    IncomeExpenseEntryCreate,
    IncomeExpenseEntryRead,
    IncomeTransferPendingRead,
)


class AccountingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AccountingRepository(db)

    def list_accounts(self) -> list[AccountRead]:
        return [AccountRead.model_validate(item) for item in self.repository.list_accounts()]

    def create_account(self, payload: AccountCreate) -> AccountRead:
        if self.repository.get_account_by_code(payload.code.strip()) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account code already exists")
        account = Account(
            code=payload.code.strip(),
            name=payload.name.strip(),
            account_type=payload.account_type.strip(),
            is_active=payload.is_active,
        )
        self.repository.add_account(account)
        self.db.commit()
        return AccountRead.model_validate(account)

    def update_account(self, account_id: int, payload: AccountUpdate) -> AccountRead:
        account = self.repository.get_account(account_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        existing = self.repository.get_account_by_code(payload.code.strip())
        if existing is not None and existing.id != account_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account code already exists")

        account.code = payload.code.strip()
        account.name = payload.name.strip()
        account.account_type = payload.account_type.strip()
        account.is_active = payload.is_active
        self.db.commit()
        return AccountRead.model_validate(account)

    def delete_account(self, account_id: int) -> None:
        account = self.repository.get_account(account_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        try:
            self.repository.delete_account(account)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account has entries. Make it inactive instead.",
            ) from exc

    def list_entries(self) -> list[IncomeExpenseEntryRead]:
        accounts = {account.id: account for account in self.repository.list_accounts()}
        return [
            IncomeExpenseEntryRead(
                id=item.id,
                account_id=item.account_id,
                account_name=accounts[item.account_id].name if item.account_id in accounts else None,
                entry_type=item.entry_type,
                amount=float(item.amount),
                remarks=item.remarks,
                created_at=item.created_at,
            )
            for item in self.repository.list_entries()
        ]

    def create_entry(self, payload: IncomeExpenseEntryCreate) -> IncomeExpenseEntryRead:
        account = self.repository.get_account(payload.account_id) if payload.account_id is not None else None
        if account is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is required")
        if not account.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account is inactive")
        if account.account_type not in {payload.entry_type, "both"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account type does not match entry type")

        entry = IncomeExpenseEntry(
            account_id=payload.account_id,
            entry_type=payload.entry_type,
            amount=payload.amount,
            remarks=payload.remarks.strip() if payload.remarks else None,
        )
        self.repository.add_entry(entry)
        self.db.commit()
        return self.list_entries()[0]

    def delete_entry(self, entry_id: int) -> None:
        entry = self.repository.get_entry(entry_id)
        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
        self.repository.delete_entry(entry)
        self.db.commit()

    def summary(self) -> AccountingSummary:
        income, expense = self.repository.get_summary()
        return AccountingSummary(total_income=income, total_expense=expense, net_balance=income - expense)

    def post_billing_collection(self, amount: float, receipt_no: str) -> None:
        income_account = self.repository.get_account_by_code("BILLING-COLLECTION")
        if income_account is None:
            income_account = Account(
                code="BILLING-COLLECTION",
                name="Billing Collection Income",
                account_type="income",
                is_active=True,
            )
            self.repository.add_account(income_account)

        self.repository.add_entry(
            IncomeExpenseEntry(
                account_id=income_account.id,
                entry_type="income",
                amount=amount,
                remarks=f"Auto-post from receipt {receipt_no}",
            )
        )

    def pending_income_transfers(self, coa_id: int | None = None, as_of_date: date | None = None) -> list[IncomeTransferPendingRead]:
        return [
            IncomeTransferPendingRead(
                billing_detail_id=detail.id,
                invoice_no=invoice.invoice_no,
                member_name=member.full_name,
                coa_id=detail.coa_id_snapshot or 0,
                amount=float(detail.receive_amount),
                head_name=detail.head_name_snapshot,
                period_display=detail.period_display,
            )
            for detail, invoice, member in self.repository.list_pending_income_transfers(coa_id=coa_id, as_of_date=as_of_date)
        ]

    def _next_voucher_no(self, voucher_type: str, voucher_date: date) -> str:
        prefix = "RV" if voucher_type == "income" else "PV"
        return f"{prefix}-{voucher_date:%Y%m%d}-{self.repository.count_vouchers(voucher_type) + 1:05d}"

    def _create_single_line_voucher(
        self,
        *,
        voucher_type: str,
        voucher_date: date,
        coa_id: int,
        amount: float,
        remarks: str | None,
        created_by: int | None,
    ) -> AccountingVoucher:
        voucher = AccountingVoucher(
            voucher_no=self._next_voucher_no(voucher_type, voucher_date),
            voucher_type=voucher_type,
            voucher_date=voucher_date,
            total_amount=amount,
            remarks=remarks,
            created_by=created_by,
        )
        self.repository.add_voucher(voucher)
        self.repository.add_voucher_detail(
            AccountingVoucherDetail(
                voucher_id=voucher.id,
                coa_id=coa_id,
                amount=amount,
                remarks=remarks,
            )
        )
        return voucher

    def create_income(self, payload: IncomeEntryCreate, created_by: int | None = None) -> IncomeEntryRead:
        account = self.repository.get_account(payload.coa_id)
        if account is None or account.account_type not in {"income", "both", "income_expense"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Income COA is required")
        pending = self.repository.list_pending_income_transfers(coa_id=payload.coa_id, as_of_date=payload.income_date)
        remaining = payload.amount
        income = IncomeEntry(
            income_date=payload.income_date,
            coa_id=payload.coa_id,
            amount=payload.amount,
            remarks=payload.remarks,
            created_by=created_by,
        )
        self.repository.add_income(income)
        voucher = self._create_single_line_voucher(
            voucher_type="income",
            voucher_date=payload.income_date,
            coa_id=payload.coa_id,
            amount=payload.amount,
            remarks=payload.remarks or "Transferred from billing collections",
            created_by=created_by,
        )
        for detail, _invoice, _member in pending:
            if remaining <= 0:
                break
            transfer_amount = min(float(detail.receive_amount), remaining)
            self.repository.add_income_detail(
                IncomeEntryDetail(income_id=income.id, billing_detail_id=detail.id, amount=transfer_amount)
            )
            detail.is_income_transferred = True
            detail.income_voucher_id = voucher.id
            remaining -= transfer_amount
        self.repository.add_entry(
                IncomeExpenseEntry(
                    account_id=payload.coa_id,
                    entry_type="income",
                    amount=payload.amount,
                    remarks=payload.remarks or voucher.voucher_no,
                )
        )
        self.db.commit()
        return self._serialize_income(income)

    def list_income(self) -> list[IncomeEntryRead]:
        return [self._serialize_income(item) for item in self.repository.list_income_entries()]

    def create_expense(self, payload: ExpenseEntryCreate, created_by: int | None = None) -> ExpenseEntryRead:
        account = self.repository.get_account(payload.coa_id)
        if account is None or account.account_type not in {"expense", "both", "income_expense"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expense COA is required")
        expense = ExpenseEntry(
            expense_date=payload.expense_date,
            coa_id=payload.coa_id,
            amount=payload.amount,
            remarks=payload.remarks,
            created_by=created_by,
        )
        self.repository.add_expense(expense)
        voucher = self._create_single_line_voucher(
            voucher_type="expense",
            voucher_date=payload.expense_date,
            coa_id=payload.coa_id,
            amount=payload.amount,
            remarks=payload.remarks,
            created_by=created_by,
        )
        self.repository.add_entry(
            IncomeExpenseEntry(
                account_id=payload.coa_id,
                entry_type="expense",
                amount=payload.amount,
                remarks=payload.remarks or voucher.voucher_no,
            )
        )
        self.db.commit()
        return self._serialize_expense(expense)

    def list_expense(self) -> list[ExpenseEntryRead]:
        return [self._serialize_expense(item) for item in self.repository.list_expense_entries()]

    def list_vouchers(self, voucher_type: str) -> list[AccountingVoucherRead]:
        return [self._serialize_voucher(item) for item in self.repository.list_vouchers(voucher_type)]

    def create_voucher(self, voucher_type: str, payload: AccountingVoucherCreate, created_by: int | None = None) -> AccountingVoucherRead:
        if voucher_type not in {"income", "expense"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid voucher type")
        account_types = {"income": {"income", "both", "income_expense"}, "expense": {"expense", "both", "income_expense"}}[voucher_type]
        for line in payload.lines:
            account = self.repository.get_account(line.coa_id)
            if account is None or not account.is_active or account.account_type not in account_types:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or inactive COA selected")

        pending_by_coa: dict[int, list] = {}
        if voucher_type == "income":
            requested_by_coa: dict[int, float] = defaultdict(float)
            for line in payload.lines:
                requested_by_coa[line.coa_id] += float(line.amount)

            for coa_id, requested_total in requested_by_coa.items():
                pending = self.repository.list_pending_income_transfers(coa_id=coa_id, as_of_date=payload.voucher_date)
                pending_by_coa[coa_id] = pending
                pending_total = round(sum(float(detail.receive_amount) for detail, _invoice, _member in pending), 2)
                if pending_total > 0 and round(requested_total, 2) != pending_total:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Income amount for selected COA must equal mapped billing collection total {pending_total:.2f}",
                    )

        total = sum(line.amount for line in payload.lines)
        prefix = "RV" if voucher_type == "income" else "PV"
        voucher = AccountingVoucher(
            voucher_no=f"{prefix}-{payload.voucher_date:%Y%m%d}-{self.repository.count_vouchers(voucher_type) + 1:05d}",
            voucher_type=voucher_type,
            voucher_date=payload.voucher_date,
            total_amount=total,
            remarks=payload.remarks,
            created_by=created_by,
        )
        self.repository.add_voucher(voucher)
        for line in payload.lines:
            self.repository.add_voucher_detail(AccountingVoucherDetail(voucher_id=voucher.id, coa_id=line.coa_id, amount=line.amount, remarks=line.remarks))
            self.repository.add_entry(IncomeExpenseEntry(account_id=line.coa_id, entry_type=voucher_type, amount=line.amount, remarks=line.remarks or voucher.voucher_no))

        if voucher_type == "income":
            for coa_id, pending in pending_by_coa.items():
                for detail, _invoice, _member in pending:
                    detail.is_income_transferred = True
                    detail.income_voucher_id = voucher.id

        self.db.commit()
        return self._serialize_voucher(voucher)

    def income_expense_report(self, from_date: date | None = None, to_date: date | None = None) -> IncomeExpenseComparisonReport:
        vouchers = self.repository.list_vouchers()
        accounts = {account.id: account for account in self.repository.list_accounts()}
        income_totals: dict[int, float] = {}
        expense_totals: dict[int, float] = {}
        for voucher in vouchers:
            if from_date and voucher.voucher_date < from_date:
                continue
            if to_date and voucher.voucher_date > to_date:
                continue
            target = income_totals if voucher.voucher_type == "income" else expense_totals if voucher.voucher_type == "expense" else None
            if target is None:
                continue
            for detail in self.repository.list_voucher_details(voucher.id):
                target[detail.coa_id] = target.get(detail.coa_id, 0) + float(detail.amount)
        def section(totals: dict[int, float]) -> IncomeExpenseReportSection:
            rows = [{"coa_id": coa_id, "coa_name": accounts.get(coa_id).name if coa_id in accounts else "Unknown", "amount": amount} for coa_id, amount in sorted(totals.items(), key=lambda item: accounts.get(item[0]).name if item[0] in accounts else "")]
            return IncomeExpenseReportSection(rows=rows, subtotal=sum(totals.values()))
        income = section(income_totals)
        expense = section(expense_totals)
        return IncomeExpenseComparisonReport(from_date=from_date, to_date=to_date, income=income, expense=expense, net_amount=income.subtotal - expense.subtotal)

    def _serialize_income(self, item: IncomeEntry) -> IncomeEntryRead:
        account = self.repository.get_account(item.coa_id)
        return IncomeEntryRead(
            id=item.id,
            income_date=item.income_date,
            coa_id=item.coa_id,
            coa_name=account.name if account else None,
            amount=float(item.amount),
            remarks=item.remarks,
            created_at=item.created_at,
        )

    def _serialize_expense(self, item: ExpenseEntry) -> ExpenseEntryRead:
        account = self.repository.get_account(item.coa_id)
        return ExpenseEntryRead(
            id=item.id,
            expense_date=item.expense_date,
            coa_id=item.coa_id,
            coa_name=account.name if account else None,
            amount=float(item.amount),
            remarks=item.remarks,
            created_at=item.created_at,
        )

    def _serialize_voucher(self, item: AccountingVoucher) -> AccountingVoucherRead:
        accounts = {account.id: account for account in self.repository.list_accounts()}
        return AccountingVoucherRead(
            id=item.id,
            voucher_no=item.voucher_no,
            voucher_type=item.voucher_type,
            voucher_date=item.voucher_date,
            total_amount=float(item.total_amount),
            remarks=item.remarks,
            created_at=item.created_at,
            created_by=item.created_by,
            lines=[
                AccountingVoucherLineRead(
                    id=detail.id,
                    coa_id=detail.coa_id,
                    coa_name=accounts[detail.coa_id].name if detail.coa_id in accounts else None,
                    amount=float(detail.amount),
                    remarks=detail.remarks,
                )
                for detail in self.repository.list_voucher_details(item.id)
            ],
        )
