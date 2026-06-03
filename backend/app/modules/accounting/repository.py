from datetime import date

from sqlalchemy import Date, String, cast, func, literal, or_, select
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

    def list_entries(
        self,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[IncomeExpenseEntry]:
        statement = select(IncomeExpenseEntry).order_by(
            IncomeExpenseEntry.created_at.desc(),
            IncomeExpenseEntry.id.desc(),
        )
        if from_date is not None:
            statement = statement.where(cast(IncomeExpenseEntry.created_at, Date) >= from_date)
        if to_date is not None:
            statement = statement.where(cast(IncomeExpenseEntry.created_at, Date) <= to_date)
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

    def list_pending_income_transfers(self, coa_id: int | None = None, as_of_date: date | None = None):
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
        if as_of_date is not None:
            statement = statement.where(BillingInvoice.invoice_date <= as_of_date)
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

    def paged_voucher_register(
        self,
        *,
        voucher_type: str,
        from_date: date | None,
        to_date: date | None,
        search: str,
        order_key: str,
        order_dir: str,
        start: int,
        length: int,
    ) -> tuple[int, int, list[dict[str, object]], dict[str, float], str]:
        voucher_count = int(
            self.db.scalar(select(func.count(AccountingVoucher.id)).where(AccountingVoucher.voucher_type == voucher_type)) or 0
        )
        if voucher_count > 0:
            summary = (
                select(
                    AccountingVoucherDetail.voucher_id.label("voucher_id"),
                    func.string_agg(Account.name, literal(", ", String(10))).label("head_name"),
                    func.count(AccountingVoucherDetail.id).label("line_count"),
                )
                .join(Account, Account.id == AccountingVoucherDetail.coa_id)
                .group_by(AccountingVoucherDetail.voucher_id)
                .subquery()
            )
            base = (
                select(
                    AccountingVoucher.id.label("id"),
                    AccountingVoucher.voucher_no.label("reference_no"),
                    AccountingVoucher.voucher_date.label("transaction_date"),
                    func.coalesce(summary.c.head_name, "").label("head_name"),
                    AccountingVoucher.total_amount.label("amount"),
                    AccountingVoucher.remarks.label("remarks"),
                    func.coalesce(summary.c.line_count, 0).label("line_count"),
                    literal(True).label("is_voucher"),
                )
                .outerjoin(summary, summary.c.voucher_id == AccountingVoucher.id)
                .where(AccountingVoucher.voucher_type == voucher_type)
            )
            if from_date is not None:
                base = base.where(AccountingVoucher.voucher_date >= from_date)
            if to_date is not None:
                base = base.where(AccountingVoucher.voucher_date <= to_date)
        else:
            entry_model = IncomeEntry if voucher_type == "income" else ExpenseEntry
            date_column = entry_model.income_date if voucher_type == "income" else entry_model.expense_date
            base = (
                select(
                    entry_model.id.label("id"),
                    literal("INC-" if voucher_type == "income" else "EXP-").concat(cast(entry_model.id, String)).label("reference_no"),
                    date_column.label("transaction_date"),
                    func.coalesce(Account.name, "").label("head_name"),
                    entry_model.amount.label("amount"),
                    entry_model.remarks.label("remarks"),
                    literal(1).label("line_count"),
                    literal(False).label("is_voucher"),
                )
                .join(Account, Account.id == entry_model.coa_id)
            )
            if from_date is not None:
                base = base.where(date_column >= from_date)
            if to_date is not None:
                base = base.where(date_column <= to_date)
        total_records = int(self.db.scalar(select(func.count()).select_from(base.subquery())) or 0)
        if search:
            needle = f"%{search.lower()}%"
            sub = base.subquery()
            base = select(sub).where(
                or_(
                    func.lower(cast(sub.c.reference_no, String)).like(needle),
                    func.lower(cast(sub.c.head_name, String)).like(needle),
                    func.lower(func.coalesce(cast(sub.c.remarks, String), "")).like(needle),
                    cast(sub.c.transaction_date, String).like(needle),
                )
            )
        filtered_records = int(self.db.scalar(select(func.count()).select_from(base.subquery())) or 0)
        subquery = base.subquery()
        order_map = {
            "reference": subquery.c.reference_no,
            "date": subquery.c.transaction_date,
            "head": subquery.c.head_name,
            "amount": subquery.c.amount,
            "remarks": subquery.c.remarks,
            "lines": subquery.c.line_count,
        }
        order_expr = order_map.get(order_key, subquery.c.transaction_date)
        rows = self.db.execute(
            select(subquery)
            .order_by(order_expr.asc() if order_dir == "asc" else order_expr.desc(), subquery.c.id.desc())
            .offset(start)
            .limit(length)
        ).mappings().all()
        totals = self.db.execute(select(func.coalesce(func.sum(subquery.c.amount), 0).label("grand_total"))).one()
        return total_records, filtered_records, [dict(row) for row in rows], {"grand_total": float(totals.grand_total or 0)}, "voucher" if voucher_count > 0 else "entry"
