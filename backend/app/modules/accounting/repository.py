from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.accounting.models import Account, AccountingVoucher, AccountingVoucherDetail, ExpenseEntry, IncomeEntry, IncomeEntryDetail, IncomeExpenseEntry
from app.modules.billing.models import BillingInvoice, BillingInvoiceDetail
from app.modules.members.models import Member


class AccountingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_accounts(self) -> list[Account]:
        statement = select(Account).order_by(Account.code.asc(), Account.name.asc())
        return list(self.db.scalars(statement))

    def get_account(self, account_id: int) -> Account | None:
        return self.db.get(Account, account_id)

    def get_account_by_code(self, code: str) -> Account | None:
        return self.db.scalar(select(Account).where(Account.code == code))

    def add_account(self, account: Account) -> Account:
        self.db.add(account)
        self.db.flush()
        self.db.refresh(account)
        return account

    def delete_account(self, account: Account) -> None:
        self.db.delete(account)
        self.db.flush()

    def list_entries(self) -> list[IncomeExpenseEntry]:
        statement = select(IncomeExpenseEntry).order_by(
            IncomeExpenseEntry.created_at.desc(),
            IncomeExpenseEntry.id.desc(),
        )
        return list(self.db.scalars(statement))

    def add_entry(self, entry: IncomeExpenseEntry) -> IncomeExpenseEntry:
        self.db.add(entry)
        self.db.flush()
        self.db.refresh(entry)
        return entry

    def get_entry(self, entry_id: int) -> IncomeExpenseEntry | None:
        return self.db.get(IncomeExpenseEntry, entry_id)

    def delete_entry(self, entry: IncomeExpenseEntry) -> None:
        self.db.delete(entry)
        self.db.flush()

    def get_summary(self) -> tuple[float, float]:
        income_statement = select(func.coalesce(func.sum(IncomeExpenseEntry.amount), 0)).where(
            IncomeExpenseEntry.entry_type == "income"
        )
        expense_statement = select(func.coalesce(func.sum(IncomeExpenseEntry.amount), 0)).where(
            IncomeExpenseEntry.entry_type == "expense"
        )
        income = float(self.db.scalar(income_statement) or 0)
        expense = float(self.db.scalar(expense_statement) or 0)
        return income, expense

    def list_pending_income_transfers(self, coa_id: int | None = None):
        statement = (
            select(BillingInvoiceDetail, BillingInvoice, Member)
            .join(BillingInvoice, BillingInvoice.id == BillingInvoiceDetail.invoice_id)
            .join(Member, Member.id == BillingInvoice.member_id)
            .where(
                BillingInvoice.is_cancelled == False,  # noqa: E712
                BillingInvoiceDetail.receive_amount > 0,
                BillingInvoiceDetail.is_income_transferred == False,  # noqa: E712
            )
            .order_by(BillingInvoice.invoice_date.asc(), BillingInvoiceDetail.id.asc())
        )
        if coa_id is not None:
            statement = statement.where(BillingInvoiceDetail.coa_id_snapshot == coa_id)
        return list(self.db.execute(statement).all())

    def add_income(self, income: IncomeEntry) -> IncomeEntry:
        self.db.add(income)
        self.db.flush()
        self.db.refresh(income)
        return income

    def add_income_detail(self, detail: IncomeEntryDetail) -> IncomeEntryDetail:
        self.db.add(detail)
        self.db.flush()
        self.db.refresh(detail)
        return detail

    def list_income_entries(self) -> list[IncomeEntry]:
        return list(self.db.scalars(select(IncomeEntry).order_by(IncomeEntry.income_date.desc(), IncomeEntry.id.desc())))

    def add_expense(self, expense: ExpenseEntry) -> ExpenseEntry:
        self.db.add(expense)
        self.db.flush()
        self.db.refresh(expense)
        return expense

    def list_expense_entries(self) -> list[ExpenseEntry]:
        return list(self.db.scalars(select(ExpenseEntry).order_by(ExpenseEntry.expense_date.desc(), ExpenseEntry.id.desc())))

    def add_voucher(self, voucher: AccountingVoucher) -> AccountingVoucher:
        self.db.add(voucher)
        self.db.flush()
        self.db.refresh(voucher)
        return voucher

    def add_voucher_detail(self, detail: AccountingVoucherDetail) -> AccountingVoucherDetail:
        self.db.add(detail)
        self.db.flush()
        self.db.refresh(detail)
        return detail

    def count_vouchers(self, voucher_type: str) -> int:
        return int(self.db.scalar(select(func.count(AccountingVoucher.id)).where(AccountingVoucher.voucher_type == voucher_type)) or 0)

    def list_vouchers(self, voucher_type: str | None = None) -> list[AccountingVoucher]:
        statement = select(AccountingVoucher).order_by(AccountingVoucher.voucher_date.desc(), AccountingVoucher.id.desc())
        if voucher_type:
            statement = statement.where(AccountingVoucher.voucher_type == voucher_type)
        return list(self.db.scalars(statement))

    def get_voucher(self, voucher_id: int) -> AccountingVoucher | None:
        return self.db.get(AccountingVoucher, voucher_id)

    def list_voucher_details(self, voucher_id: int) -> list[AccountingVoucherDetail]:
        return list(self.db.scalars(select(AccountingVoucherDetail).where(AccountingVoucherDetail.voucher_id == voucher_id).order_by(AccountingVoucherDetail.id.asc())))
