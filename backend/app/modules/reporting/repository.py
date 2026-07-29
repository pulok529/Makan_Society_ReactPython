from decimal import Decimal

from sqlalchemy import Select, and_, case, func, select
from sqlalchemy.orm import Session

from app.modules.accounting.models import Account, ExpenseEntry, IncomeEntry
from app.modules.billing.models import BillingHead, BillingInvoice, BillingInvoiceDetail, BillingPeriod, Charge, Receipt, ReceiptLine, BillingDueTracker
from app.modules.categories.models import MemberCategory
from app.modules.members.models import Member, MemberNominee, MemberPackage
from app.modules.packages.models import Package


class ReportingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _serialize_rows(rows) -> list[dict]:
        serialized: list[dict] = []
        for row in rows:
            item: dict = {}
            for key, value in dict(row).items():
                item[key] = float(value) if isinstance(value, Decimal) else value
            serialized.append(item)
        return serialized

    def list_members(
        self,
        *,
        member_id: int | None = None,
        category_id: int | None = None,
        plot_no: str | None = None,
    ) -> list[Member]:
        statement: Select[tuple[Member]] = select(Member).order_by(Member.member_code.asc(), Member.full_name.asc())
        if member_id is not None:
            statement = statement.where(Member.id == member_id)
        if category_id is not None:
            statement = statement.where(Member.category_id == category_id)
        if plot_no is not None and plot_no.strip():
            statement = statement.where(
                (Member.plot_no.ilike(f"%{plot_no.strip()}%")) | (Member.member_id_text.ilike(f"%{plot_no.strip()}%"))
            )
        return list(self.db.scalars(statement))

    def list_categories(self) -> list[MemberCategory]:
        return list(self.db.scalars(select(MemberCategory).order_by(MemberCategory.code.asc(), MemberCategory.name.asc())))

    def list_accounts(self) -> list[Account]:
        return list(self.db.scalars(select(Account).order_by(Account.code.asc(), Account.name.asc())))

    def list_packages(self) -> list[Package]:
        return list(self.db.scalars(select(Package).order_by(Package.id.asc(), Package.name.asc())))

    def list_member_packages(self) -> list[MemberPackage]:
        return list(self.db.scalars(select(MemberPackage).order_by(MemberPackage.id.asc())))

    def get_member_nominee(self, member_id: int) -> MemberNominee | None:
        statement = select(MemberNominee).where(MemberNominee.member_id == member_id)
        return self.db.scalar(statement)

    def list_periods(self) -> list[BillingPeriod]:
        return list(self.db.scalars(select(BillingPeriod).order_by(BillingPeriod.year.desc(), BillingPeriod.month.desc())))

    def list_charges(
        self,
        *,
        member_id: int | None = None,
        billing_period_id: int | None = None,
        from_date=None,
        to_date=None,
    ) -> list[Charge]:
        statement: Select[tuple[Charge]] = select(Charge).order_by(Charge.created_at.desc(), Charge.id.desc())
        if member_id is not None:
            statement = statement.where(Charge.member_id == member_id)
        if billing_period_id is not None:
            statement = statement.where(Charge.billing_period_id == billing_period_id)
        if from_date is not None:
            statement = statement.where(Charge.created_at >= from_date)
        if to_date is not None:
            statement = statement.where(Charge.created_at <= to_date)
        return list(self.db.scalars(statement))

    def list_receipts(self, *, member_id: int | None = None, from_date=None, to_date=None) -> list[Receipt]:
        statement: Select[tuple[Receipt]] = select(Receipt).order_by(Receipt.payment_date.desc(), Receipt.id.desc())
        conditions = []
        if member_id is not None:
            conditions.append(Receipt.member_id == member_id)
        if from_date is not None:
            conditions.append(Receipt.payment_date >= from_date)
        if to_date is not None:
            conditions.append(Receipt.payment_date <= to_date)
        if conditions:
            statement = statement.where(and_(*conditions))
        return list(self.db.scalars(statement))

    def list_invoices_for_collection(
        self,
        *,
        member_id: int | None = None,
        from_date=None,
        to_date=None,
    ) -> list[BillingInvoice]:
        """Return non-cancelled invoices that have received payment (live collection flow)."""
        statement: Select[tuple[BillingInvoice]] = (
            select(BillingInvoice)
            .where(
                BillingInvoice.is_cancelled == False,  # noqa: E712
                BillingInvoice.total_receive_amount > 0,
            )
            .order_by(BillingInvoice.invoice_date.desc(), BillingInvoice.id.desc())
        )
        if member_id is not None:
            statement = statement.where(BillingInvoice.member_id == member_id)
        if from_date is not None:
            statement = statement.where(BillingInvoice.invoice_date >= from_date)
        if to_date is not None:
            statement = statement.where(BillingInvoice.invoice_date <= to_date)
        return list(self.db.scalars(statement))

    def list_income_entries(self, *, from_date=None, to_date=None) -> list[IncomeEntry]:
        statement: Select[tuple[IncomeEntry]] = select(IncomeEntry).order_by(IncomeEntry.income_date.desc(), IncomeEntry.id.desc())
        conditions = []
        if from_date is not None:
            conditions.append(IncomeEntry.income_date >= from_date)
        if to_date is not None:
            conditions.append(IncomeEntry.income_date <= to_date)
        if conditions:
            statement = statement.where(and_(*conditions))
        return list(self.db.scalars(statement))

    def list_expense_entries(self, *, from_date=None, to_date=None) -> list[ExpenseEntry]:
        statement: Select[tuple[ExpenseEntry]] = select(ExpenseEntry).order_by(ExpenseEntry.expense_date.desc(), ExpenseEntry.id.desc())
        conditions = []
        if from_date is not None:
            conditions.append(ExpenseEntry.expense_date >= from_date)
        if to_date is not None:
            conditions.append(ExpenseEntry.expense_date <= to_date)
        if conditions:
            statement = statement.where(and_(*conditions))
        return list(self.db.scalars(statement))

    def get_receipt(self, receipt_id: int) -> Receipt | None:
        return self.db.get(Receipt, receipt_id)

    def list_receipt_lines(self, receipt_id: int) -> list[ReceiptLine]:
        statement = select(ReceiptLine).where(ReceiptLine.receipt_id == receipt_id).order_by(ReceiptLine.id.asc())
        return list(self.db.scalars(statement))

    def list_invoices(self, *, member_id: int | None = None, from_date=None, to_date=None) -> list[BillingInvoice]:
        statement: Select[tuple[BillingInvoice]] = select(BillingInvoice).where(BillingInvoice.is_cancelled == False)  # noqa: E712
        conditions = []
        if member_id is not None:
            conditions.append(BillingInvoice.member_id == member_id)
        if from_date is not None:
            conditions.append(BillingInvoice.invoice_date >= from_date)
        if to_date is not None:
            conditions.append(BillingInvoice.invoice_date <= to_date)
        if conditions:
            statement = statement.where(and_(*conditions))
        statement = statement.order_by(BillingInvoice.invoice_date.asc(), BillingInvoice.id.asc())
        return list(self.db.scalars(statement))

    def list_invoice_details(self, invoice_id: int | None = None, member_id: int | None = None) -> list[BillingInvoiceDetail]:
        statement: Select[tuple[BillingInvoiceDetail]] = select(BillingInvoiceDetail)
        conditions = []
        if invoice_id is not None:
            conditions.append(BillingInvoiceDetail.invoice_id == invoice_id)
        if member_id is not None:
            conditions.append(BillingInvoiceDetail.member_id == member_id)
        if conditions:
            statement = statement.where(and_(*conditions))
        statement = statement.order_by(BillingInvoiceDetail.period_date.asc(), BillingInvoiceDetail.id.asc())
        return list(self.db.scalars(statement))

    def _base_income_detail_query(self, from_date=None, to_date=None) -> tuple[dict, str]:
        date_filter_i = ""
        date_filter_e = ""
        params = {}

        if from_date:
            date_filter_i += " AND i.InvoiceDate >= :from_date"
            date_filter_e += " AND CAST(e.created_at AS DATE) >= :from_date"
            params["from_date"] = from_date
        if to_date:
            date_filter_i += " AND i.InvoiceDate <= :to_date"
            date_filter_e += " AND CAST(e.created_at AS DATE) <= :to_date"
            params["to_date"] = to_date

        sql = f"""
            SELECT 
                i.InvoiceDate AS income_date,
                a.code AS account_code,
                a.name AS account_name,
                d.ReceiveAmount AS amount,
                'Invoice: ' + i.InvoiceNo AS remarks
            FROM billing.billing_invoice_details d
            JOIN billing.billing_invoices i ON d.InvoiceID = i.InvoiceID
            JOIN accounting.accounts a ON d.COAIDSnapshot = a.id
            WHERE i.IsCancelled = 0 {date_filter_i}
            AND d.ReceiveAmount > 0

            UNION ALL

            SELECT 
                CAST(e.created_at AS DATE) AS income_date,
                a.code AS account_code,
                a.name AS account_name,
                e.amount AS amount,
                e.remarks AS remarks
            FROM accounting.income_expense_entries e
            JOIN accounting.accounts a ON e.account_id = a.id
            WHERE e.entry_type = 'income' 
            AND a.name != 'Billing Collection Income'
            AND e.remarks NOT LIKE '(void invoice)%%'
            AND e.remarks NOT LIKE 'LegacyIncomeExpenseId=%%'
            AND e.amount > 0
            AND e.id NOT IN (
                SELECT e2.id 
                FROM accounting.income_expense_entries e2
                JOIN accounting.accounting_voucher_details vd ON e2.account_id = vd.COAID AND e2.amount = vd.Amount
                JOIN accounting.accounting_vouchers v ON vd.VoucherID = v.VoucherID
                WHERE e2.entry_type = 'income' AND v.VoucherType = 'income' 
                AND v.VoucherID IN (SELECT DISTINCT IncomeVoucherID FROM billing.billing_invoice_details WHERE IncomeVoucherID IS NOT NULL)
            )
            {date_filter_e}
        """
        return params, sql

    def paged_income_detail(self, *, from_date=None, to_date=None, limit: int = 50, offset: int = 0) -> tuple[int, float, list[dict]]:
        params, base_sql = self._base_income_detail_query(from_date, to_date)
        from sqlalchemy import text
        
        count_sql = f"SELECT COUNT(*) FROM ({base_sql}) t"
        total_sql = f"SELECT ISNULL(SUM(amount), 0) FROM ({base_sql}) t"
        rows_sql = f"SELECT * FROM ({base_sql}) t ORDER BY income_date ASC, account_code ASC OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
        
        params["limit"] = limit
        params["offset"] = offset

        total_count = self.db.execute(text(count_sql), params).scalar() or 0
        total_amount = self.db.execute(text(total_sql), params).scalar() or 0
        rows = self.db.execute(text(rows_sql), params).mappings().all()

        return int(total_count), float(total_amount), self._serialize_rows(rows)

    def income_detail(self, *, from_date=None, to_date=None) -> tuple[int, float, list[dict]]:
        params, base_sql = self._base_income_detail_query(from_date, to_date)
        from sqlalchemy import text
        
        count_sql = f"SELECT COUNT(*) FROM ({base_sql}) t"
        total_sql = f"SELECT ISNULL(SUM(amount), 0) FROM ({base_sql}) t"
        rows_sql = f"SELECT * FROM ({base_sql}) t ORDER BY income_date ASC, account_code ASC"
        
        total_count = self.db.execute(text(count_sql), params).scalar() or 0
        total_amount = self.db.execute(text(total_sql), params).scalar() or 0
        rows = self.db.execute(text(rows_sql), params).mappings().all()

        return int(total_count), float(total_amount), self._serialize_rows(rows)

    def paged_expense_detail(self, *, from_date=None, to_date=None, limit: int = 50, offset: int = 0) -> tuple[int, float, list[dict]]:
        conditions = []
        if from_date is not None:
            conditions.append(ExpenseEntry.expense_date >= from_date)
        if to_date is not None:
            conditions.append(ExpenseEntry.expense_date <= to_date)

        count_stmt = select(func.count()).select_from(ExpenseEntry)
        total_stmt = select(func.coalesce(func.sum(ExpenseEntry.amount), 0)).select_from(ExpenseEntry)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
            total_stmt = total_stmt.where(and_(*conditions))

        rows = self.db.execute(
            select(
                ExpenseEntry.id.label("expense_id"),
                ExpenseEntry.expense_date.label("expense_date"),
                Account.code.label("account_code"),
                Account.name.label("account_name"),
                ExpenseEntry.amount.label("amount"),
                ExpenseEntry.remarks.label("remarks"),
                ExpenseEntry.created_at.label("created_at"),
            )
            .select_from(ExpenseEntry)
            .outerjoin(Account, Account.id == ExpenseEntry.coa_id)
            .where(and_(*conditions) if conditions else True)
            .order_by(ExpenseEntry.expense_date.desc(), ExpenseEntry.id.desc())
            .offset(offset)
            .limit(limit)
        ).mappings().all()
        return int(self.db.scalar(count_stmt) or 0), float(self.db.scalar(total_stmt) or 0), self._serialize_rows(rows)

    def _get_electricity_head_ids(self) -> list[int]:
        stmt = select(BillingHead.id).where(BillingHead.head_name.ilike("%Electric%"))
        return list(self.db.scalars(stmt).all())

    def _base_electricity_collection_query(
        self,
        *,
        member_id: int | None = None,
        plot_no: str | None = None,
        from_date=None,
        to_date=None,
    ) -> tuple[list, Select, Select]:
        conditions = [
            BillingInvoice.is_cancelled == False,  # noqa: E712
            BillingInvoiceDetail.receive_amount > 0,
        ]
        
        electricity_head_ids = self._get_electricity_head_ids()
        if electricity_head_ids:
            conditions.append(BillingInvoiceDetail.billing_head_id.in_(electricity_head_ids))
        else:
            # Fallback to name search if no heads match directly by ID
            conditions.append(BillingInvoiceDetail.head_name_snapshot.ilike("%Electric%"))
            
        if member_id is not None:
            conditions.append(BillingInvoice.member_id == member_id)
        if plot_no is not None and plot_no.strip():
            conditions.append((Member.plot_no.ilike(f"%{plot_no.strip()}%")) | (Member.member_code.ilike(f"%{plot_no.strip()}%")))
        if from_date is not None:
            conditions.append(BillingInvoice.invoice_date >= from_date)
        if to_date is not None:
            conditions.append(BillingInvoice.invoice_date <= to_date)

        base = (
            select(BillingInvoiceDetail.id)
            .select_from(BillingInvoiceDetail)
            .join(BillingInvoice, BillingInvoice.id == BillingInvoiceDetail.invoice_id)
            .join(Member, Member.id == BillingInvoice.member_id)
        )
        total_stmt = (
            select(
                func.coalesce(func.sum(BillingInvoiceDetail.fee_amount), 0),
                func.coalesce(func.sum(BillingInvoiceDetail.receive_amount), 0),
            )
            .select_from(BillingInvoiceDetail)
            .join(BillingInvoice, BillingInvoice.id == BillingInvoiceDetail.invoice_id)
            .join(Member, Member.id == BillingInvoice.member_id)
        )
        if conditions:
            base = base.where(and_(*conditions))
            total_stmt = total_stmt.where(and_(*conditions))
            
        return conditions, base, total_stmt

    def paged_electricity_collection(
        self,
        *,
        member_id: int | None = None,
        plot_no: str | None = None,
        from_date=None,
        to_date=None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, float, float, list[dict]]:
        conditions, base, total_stmt = self._base_electricity_collection_query(
            member_id=member_id, plot_no=plot_no, from_date=from_date, to_date=to_date
        )

        count_stmt = select(func.count()).select_from(base.subquery())
        
        rows_stmt = (
            select(
                BillingInvoice.invoice_date.label("collection_date"),
                Member.plot_no.label("plot_no"),
                Member.member_code.label("member_id"),
                Member.full_name.label("member_name"),
                BillingInvoice.invoice_no.label("invoice_no"),
                BillingInvoiceDetail.fee_amount.label("electricity_bill_amount"),
                BillingInvoiceDetail.receive_amount.label("paid_amount"),
            )
            .select_from(BillingInvoiceDetail)
            .join(BillingInvoice, BillingInvoice.id == BillingInvoiceDetail.invoice_id)
            .join(Member, Member.id == BillingInvoice.member_id)
        )
        if conditions:
            rows_stmt = rows_stmt.where(and_(*conditions))
            
        rows_stmt = rows_stmt.order_by(BillingInvoice.invoice_date.asc(), BillingInvoice.invoice_no.asc()).limit(limit).offset(offset)

        total_count = self.db.scalar(count_stmt) or 0
        total_bill, total_paid = self.db.execute(total_stmt).one_or_none() or (0, 0)
        rows = self.db.execute(rows_stmt).mappings().all()

        return total_count, float(total_bill), float(total_paid), self._serialize_rows(rows)

    def electricity_collection(
        self,
        *,
        member_id: int | None = None,
        plot_no: str | None = None,
        from_date=None,
        to_date=None,
    ) -> tuple[int, float, float, list[dict]]:
        conditions, base, total_stmt = self._base_electricity_collection_query(
            member_id=member_id, plot_no=plot_no, from_date=from_date, to_date=to_date
        )

        rows_stmt = (
            select(
                BillingInvoice.invoice_date.label("collection_date"),
                Member.plot_no.label("plot_no"),
                Member.member_code.label("member_id"),
                Member.full_name.label("member_name"),
                BillingInvoice.invoice_no.label("invoice_no"),
                BillingInvoiceDetail.fee_amount.label("electricity_bill_amount"),
                BillingInvoiceDetail.receive_amount.label("paid_amount"),
            )
            .select_from(BillingInvoiceDetail)
            .join(BillingInvoice, BillingInvoice.id == BillingInvoiceDetail.invoice_id)
            .join(Member, Member.id == BillingInvoice.member_id)
        )
        if conditions:
            rows_stmt = rows_stmt.where(and_(*conditions))
            
        rows_stmt = rows_stmt.order_by(BillingInvoice.invoice_date.asc(), BillingInvoice.invoice_no.asc())

        total_count = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        total_bill, total_paid = self.db.execute(total_stmt).one_or_none() or (0, 0)
        rows = self.db.execute(rows_stmt).mappings().all()

        return total_count, float(total_bill), float(total_paid), self._serialize_rows(rows)

    def paged_collections(
        self,
        *,
        member_id: int | None = None,
        category_id: int | None = None,
        plot_no: str | None = None,
        from_date=None,
        to_date=None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, float, float, list[dict]]:
        conditions = []
        if member_id is not None:
            conditions.append(Receipt.member_id == member_id)
        if category_id is not None:
            conditions.append(Member.category_id == category_id)
        if plot_no is not None and plot_no.strip():
            conditions.append((Member.plot_no.ilike(f"%{plot_no.strip()}%")) | (Member.member_id_text.ilike(f"%{plot_no.strip()}%")))
        if from_date is not None:
            conditions.append(Receipt.payment_date >= from_date)
        if to_date is not None:
            conditions.append(Receipt.payment_date <= to_date)

        base = select(Receipt.id).select_from(Receipt).join(Member, Member.id == Receipt.member_id)
        total_stmt = select(
            func.coalesce(func.sum(Receipt.total_amount), 0),
            func.coalesce(func.sum(Receipt.discount_amount), 0),
        ).select_from(Receipt).join(Member, Member.id == Receipt.member_id)
        if conditions:
            base = base.where(and_(*conditions))
            total_stmt = total_stmt.where(and_(*conditions))
        count_stmt = select(func.count()).select_from(base.subquery())

        rows = self.db.execute(
            select(
                Receipt.member_id.label("member_id"),
                Member.member_code.label("member_code"),
                Member.full_name.label("member_name"),
                Receipt.receipt_no.label("receipt_no"),
                Receipt.payment_date.label("payment_date"),
                Receipt.total_amount.label("total_amount"),
                Receipt.discount_amount.label("discount_amount"),
            )
            .select_from(Receipt)
            .join(Member, Member.id == Receipt.member_id)
            .where(and_(*conditions) if conditions else True)
            .order_by(Member.member_code.asc(), Receipt.payment_date.asc(), Receipt.receipt_no.asc())
            .offset(offset)
            .limit(limit)
        ).mappings().all()
        total_amount, discount_amount = self.db.execute(total_stmt).one()
        return int(self.db.scalar(count_stmt) or 0), float(total_amount or 0), float(discount_amount or 0), self._serialize_rows(rows)

    def paged_charge_register(
        self,
        *,
        member_id: int | None = None,
        category_id: int | None = None,
        billing_period_id: int | None = None,
        plot_no: str | None = None,
        from_date=None,
        to_date=None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, float, float, list[dict]]:
        conditions = []
        if member_id is not None:
            conditions.append(Charge.member_id == member_id)
        if category_id is not None:
            conditions.append(Member.category_id == category_id)
        if billing_period_id is not None:
            conditions.append(Charge.billing_period_id == billing_period_id)
        if plot_no is not None and plot_no.strip():
            conditions.append((Member.plot_no.ilike(f"%{plot_no.strip()}%")) | (Member.member_id_text.ilike(f"%{plot_no.strip()}%")))
        if from_date is not None:
            conditions.append(Charge.created_at >= from_date)
        if to_date is not None:
            conditions.append(Charge.created_at <= to_date)

        base = select(Charge.id).select_from(Charge).join(Member, Member.id == Charge.member_id)
        total_stmt = select(
            func.coalesce(func.sum(Charge.net_amount), 0),
            func.coalesce(func.sum(Charge.due_amount), 0),
        ).select_from(Charge).join(Member, Member.id == Charge.member_id)
        if conditions:
            base = base.where(and_(*conditions))
            total_stmt = total_stmt.where(and_(*conditions))
        count_stmt = select(func.count()).select_from(base.subquery())

        rows = self.db.execute(
            select(
                Charge.id.label("charge_id"),
                Charge.created_at.label("created_at"),
                Charge.member_id.label("member_id"),
                Member.member_code.label("member_code"),
                Member.full_name.label("member_name"),
                BillingPeriod.period_name.label("billing_period_name"),
                Charge.charge_type.label("charge_type"),
                Charge.status.label("status"),
                Charge.net_amount.label("net_amount"),
                Charge.due_amount.label("due_amount"),
            )
            .select_from(Charge)
            .join(Member, Member.id == Charge.member_id)
            .outerjoin(BillingPeriod, BillingPeriod.id == Charge.billing_period_id)
            .where(and_(*conditions) if conditions else True)
            .order_by(Member.member_code.asc(), Charge.created_at.asc(), Charge.id.asc())
            .offset(offset)
            .limit(limit)
        ).mappings().all()
        net_amount, due_amount = self.db.execute(total_stmt).one()
        return int(self.db.scalar(count_stmt) or 0), float(net_amount or 0), float(due_amount or 0), self._serialize_rows(rows)

    def paged_due_members(
        self,
        *,
        member_id: int | None = None,
        category_id: int | None = None,
        billing_period_id: int | None = None,
        plot_no: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, float, list[dict]]:
        conditions = [Charge.due_amount > 0]
        if member_id is not None:
            conditions.append(Charge.member_id == member_id)
        if category_id is not None:
            conditions.append(Member.category_id == category_id)
        if billing_period_id is not None:
            conditions.append(Charge.billing_period_id == billing_period_id)
        if plot_no is not None and plot_no.strip():
            conditions.append((Member.plot_no.ilike(f"%{plot_no.strip()}%")) | (Member.member_id_text.ilike(f"%{plot_no.strip()}%")))

        grouped = (
            select(
                Member.id.label("member_id"),
                Member.member_code.label("member_code"),
                Member.full_name.label("member_name"),
                MemberCategory.name.label("category_name"),
                Member.cell_no.label("cell_no"),
                func.coalesce(func.sum(Charge.net_amount), 0).label("total_charged"),
                func.coalesce(func.sum(Charge.due_amount), 0).label("total_due"),
                func.count(Charge.id).label("open_charge_count"),
            )
            .select_from(Charge)
            .join(Member, Member.id == Charge.member_id)
            .outerjoin(MemberCategory, MemberCategory.id == Member.category_id)
            .where(and_(*conditions))
            .group_by(Member.id, Member.member_code, Member.full_name, MemberCategory.name, Member.cell_no)
        ).subquery()

        count_stmt = select(func.count()).select_from(grouped)
        total_stmt = select(func.coalesce(func.sum(grouped.c.total_due), 0)).select_from(grouped)
        rows = self.db.execute(
            select(grouped)
            .order_by(grouped.c.member_code.asc(), grouped.c.member_name.asc())
            .offset(offset)
            .limit(limit)
        ).mappings().all()
        return int(self.db.scalar(count_stmt) or 0), float(self.db.scalar(total_stmt) or 0), self._serialize_rows(rows)

    def paged_total_due(
        self,
        *,
        member_id: int | None = None,
        category_id: int | None = None,
        billing_period_id: int | None = None,
        plot_no: str | None = None,
        from_date=None,
        to_date=None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, float, float, float, list[dict]]:
        conditions = [BillingDueTracker.due_amount > 0]
        if member_id is not None:
            conditions.append(BillingDueTracker.member_id == member_id)
        if category_id is not None:
            conditions.append(Member.category_id == category_id)
        if plot_no is not None and plot_no.strip():
            conditions.append((Member.plot_no.ilike(f"%{plot_no.strip()}%")) | (Member.member_id_text.ilike(f"%{plot_no.strip()}%")))
        if from_date is not None:
            conditions.append(BillingDueTracker.period_date >= from_date)
        if to_date is not None:
            conditions.append(BillingDueTracker.period_date <= to_date)

        grouped = (
            select(
                Member.id.label("member_id"),
                Member.member_code.label("member_code"),
                Member.full_name.label("member_name"),
                func.coalesce(Member.plot_no, Member.member_id_text).label("plot_no"),
                func.coalesce(func.sum(BillingDueTracker.fee_amount), 0).label("total_billed_amount"),
                func.coalesce(func.sum(BillingDueTracker.paid_amount), 0).label("total_received_amount"),
                func.coalesce(func.sum(BillingDueTracker.due_amount), 0).label("total_due_amount"),
            )
            .select_from(BillingDueTracker)
            .join(Member, Member.id == BillingDueTracker.member_id)
            .where(and_(*conditions))
            .group_by(Member.id, Member.member_code, Member.full_name, Member.plot_no, Member.member_id_text)
        ).subquery()

        count_stmt = select(func.count()).select_from(grouped)
        total_stmt = select(
            func.coalesce(func.sum(grouped.c.total_billed_amount), 0),
            func.coalesce(func.sum(grouped.c.total_received_amount), 0),
            func.coalesce(func.sum(grouped.c.total_due_amount), 0)
        ).select_from(grouped)
        
        rows = self.db.execute(
            select(grouped)
            .order_by(grouped.c.member_code.asc(), grouped.c.member_name.asc())
            .offset(offset)
            .limit(limit)
        ).mappings().all()
        
        total_billed, total_received, total_due = self.db.execute(total_stmt).one_or_none() or (0, 0, 0)
        return int(self.db.scalar(count_stmt) or 0), float(total_billed), float(total_received), float(total_due), self._serialize_rows(rows)

    def paged_total_collection(
        self,
        *,
        member_id: int | None = None,
        category_id: int | None = None,
        plot_no: str | None = None,
        from_date=None,
        to_date=None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, float, list[dict]]:
        conditions = []
        if member_id is not None:
            conditions.append(BillingInvoice.member_id == member_id)
        if category_id is not None:
            conditions.append(Member.category_id == category_id)
        if plot_no is not None and plot_no.strip():
            conditions.append((Member.plot_no.ilike(f"%{plot_no.strip()}%")) | (Member.member_id_text.ilike(f"%{plot_no.strip()}%")))
        if from_date is not None:
            conditions.append(BillingInvoice.invoice_date >= from_date)
        if to_date is not None:
            conditions.append(BillingInvoice.invoice_date <= to_date)

        grouped = (
            select(
                Member.id.label("member_id"),
                Member.member_code.label("member_code"),
                Member.full_name.label("member_name"),
                func.coalesce(Member.plot_no, Member.member_id_text).label("plot_no"),
                func.coalesce(func.sum(BillingInvoice.total_receive_amount), 0).label("total_collection_amount"),
            )
            .select_from(BillingInvoice)
            .join(Member, Member.id == BillingInvoice.member_id)
            .where(
                BillingInvoice.is_cancelled == False,  # noqa: E712
                BillingInvoice.total_receive_amount > 0,
                *(conditions),
            )
            .group_by(Member.id, Member.member_code, Member.full_name, Member.plot_no, Member.member_id_text)
        ).subquery()

        count_stmt = select(func.count()).select_from(grouped)
        total_stmt = select(func.coalesce(func.sum(grouped.c.total_collection_amount), 0)).select_from(grouped)
        rows = self.db.execute(
            select(grouped)
            .order_by(grouped.c.member_code.asc(), grouped.c.member_name.asc())
            .offset(offset)
            .limit(limit)
        ).mappings().all()
        return int(self.db.scalar(count_stmt) or 0), float(self.db.scalar(total_stmt) or 0), self._serialize_rows(rows)

    def paged_member_register(
        self,
        *,
        member_id: int | None = None,
        category_id: int | None = None,
        plot_no: str | None = None,
        from_date=None,
        to_date=None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, dict[str, float | int], list[dict]]:
        from app.modules.billing.models import BillingDueTracker, BillingInvoice
        due_tracker_totals = (
            select(
                BillingDueTracker.member_id.label("member_id"),
                func.coalesce(func.sum(BillingDueTracker.due_amount), 0).label("total_due_amount"),
            )
            .group_by(BillingDueTracker.member_id)
        ).subquery()

        collection_totals = (
            select(
                BillingInvoice.member_id.label("member_id"),
                func.coalesce(func.sum(BillingInvoice.total_receive_amount), 0).label("total_collection_amount"),
            )
            .where(BillingInvoice.is_cancelled == False)  # noqa: E712
            .group_by(BillingInvoice.member_id)
        ).subquery()

        conditions = []
        if member_id is not None:
            conditions.append(Member.id == member_id)
        if category_id is not None:
            conditions.append(Member.category_id == category_id)
        if plot_no is not None and plot_no.strip():
            conditions.append((Member.plot_no.ilike(f"%{plot_no.strip()}%")) | (Member.member_id_text.ilike(f"%{plot_no.strip()}%")))

        base = (
            select(
                Member.id.label("member_id"),
                Member.member_code.label("member_code"),
                Member.full_name.label("full_name"),
                func.coalesce(Member.plot_no, Member.member_id_text).label("plot_no"),
                Member.cell_no.label("cell_no"),
                func.coalesce(collection_totals.c.total_collection_amount, 0).label("total_collection_amount"),
                func.coalesce(due_tracker_totals.c.total_due_amount, 0).label("total_due_amount"),
            )
            .select_from(Member)
            .outerjoin(due_tracker_totals, due_tracker_totals.c.member_id == Member.id)
            .outerjoin(collection_totals, collection_totals.c.member_id == Member.id)
        )
        if conditions:
            base = base.where(and_(*conditions))
        base_subquery = base.subquery()

        count_stmt = select(func.count()).select_from(base_subquery)
        totals_stmt = select(
            func.count().label("member_count"),
            func.coalesce(func.sum(base_subquery.c.total_collection_amount), 0).label("total_collection_amount"),
            func.coalesce(func.sum(base_subquery.c.total_due_amount), 0).label("total_due_amount"),
        ).select_from(base_subquery)
        
        rows = self.db.execute(
            select(base_subquery)
            .order_by(base_subquery.c.member_code.asc(), base_subquery.c.full_name.asc())
        ).mappings().all()
        totals = self.db.execute(totals_stmt).mappings().one()
        return int(self.db.scalar(count_stmt) or 0), {
            "member_count": int(totals["member_count"] or 0),
            "total_collection_amount": float(totals["total_collection_amount"] or 0),
            "total_due_amount": float(totals["total_due_amount"] or 0),
        }, self._serialize_rows(rows)
