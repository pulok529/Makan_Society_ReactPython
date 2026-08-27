from datetime import date

from sqlalchemy import (
    Date,
    Select,
    String,
    and_,
    asc,
    case,
    cast,
    column,
    desc,
    func,
    literal,
    or_,
    select,
    text,
)
from sqlalchemy.orm import Session

from app.modules.accounting.models import Account
from app.modules.billing.models import (
    BillingDueTracker,
    BillingHead,
    BillingHeadCoaMapping,
    BillingInvoice,
    BillingInvoiceDetail,
    BillingPeriod,
    Charge,
    ChargeItem,
    Receipt,
    ReceiptLine,
    BillingVoidedInvoice,
    BillingVoidedInvoiceDetail,
)
from app.modules.members.models import Member, MemberPackage


class BillingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_periods(self) -> list[BillingPeriod]:
        statement = select(BillingPeriod).order_by(BillingPeriod.year.desc(), BillingPeriod.month.desc())
        return list(self.db.scalars(statement))

    def get_period(self, period_id: int) -> BillingPeriod | None:
        return self.db.get(BillingPeriod, period_id)

    def get_period_by_year_month(self, year: int, month: int) -> BillingPeriod | None:
        statement = select(BillingPeriod).where(BillingPeriod.year == year, BillingPeriod.month == month)
        return self.db.scalar(statement)

    def add_period(self, period: BillingPeriod) -> BillingPeriod:
        self.db.add(period)
        self.db.flush()
        self.db.refresh(period)
        return period

    def list_charges(
        self,
        billing_period_id: int | None = None,
        member_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        due_only: bool = False,
        limit: int | None = None,
    ) -> list[Charge]:
        statement: Select[tuple[Charge]] = select(Charge).order_by(Charge.created_at.desc(), Charge.id.desc())
        if billing_period_id is not None:
            statement = statement.where(Charge.billing_period_id == billing_period_id)
        if member_id is not None:
            statement = statement.where(Charge.member_id == member_id)
        if from_date is not None:
            statement = statement.where(cast(Charge.created_at, Date) >= from_date)
        if to_date is not None:
            statement = statement.where(cast(Charge.created_at, Date) <= to_date)
        if due_only:
            statement = statement.where(Charge.due_amount > 0)
        if limit is not None:
            statement = statement.limit(limit)
        return list(self.db.scalars(statement))

    def get_charge(self, charge_id: int) -> Charge | None:
        return self.db.get(Charge, charge_id)

    def get_existing_member_charge(
        self,
        *,
        member_id: int,
        billing_period_id: int,
        charge_type: str,
    ) -> Charge | None:
        statement = select(Charge).where(
            Charge.member_id == member_id,
            Charge.billing_period_id == billing_period_id,
            Charge.charge_type == charge_type,
        )
        return self.db.scalar(statement)

    def list_charge_items(self, charge_id: int) -> list[ChargeItem]:
        statement = select(ChargeItem).where(ChargeItem.charge_id == charge_id).order_by(ChargeItem.id.asc())
        return list(self.db.scalars(statement))

    def add_charge(self, charge: Charge) -> Charge:
        self.db.add(charge)
        self.db.flush()
        self.db.refresh(charge)
        return charge

    def add_charge_item(self, item: ChargeItem) -> ChargeItem:
        self.db.add(item)
        self.db.flush()
        self.db.refresh(item)
        return item

    def list_active_member_packages_for_period(self, starts_on, ends_on) -> list[MemberPackage]:
        statement = select(MemberPackage).where(
            MemberPackage.is_active == True,  # noqa: E712
            MemberPackage.assigned_on <= ends_on,
            (MemberPackage.ended_on.is_(None) | (MemberPackage.ended_on >= starts_on)),
        )
        return list(self.db.scalars(statement))

    def list_active_members(self) -> list[Member]:
        statement = select(Member).where(Member.is_active == True).order_by(Member.member_code.asc(), Member.full_name.asc())  # noqa: E712
        return list(self.db.scalars(statement))

    def list_receipts(
        self,
        member_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        limit: int | None = None,
    ) -> list[Receipt]:
        statement = select(Receipt).order_by(Receipt.payment_date.desc(), Receipt.id.desc())
        if member_id is not None:
            statement = statement.where(Receipt.member_id == member_id)
        if from_date is not None:
            statement = statement.where(Receipt.payment_date >= from_date)
        if to_date is not None:
            statement = statement.where(Receipt.payment_date <= to_date)
        if limit is not None:
            statement = statement.limit(limit)
        return list(self.db.scalars(statement))

    def get_receipt(self, receipt_id: int) -> Receipt | None:
        return self.db.get(Receipt, receipt_id)

    def add_receipt(self, receipt: Receipt) -> Receipt:
        self.db.add(receipt)
        self.db.flush()
        self.db.refresh(receipt)
        return receipt

    def add_receipt_line(self, line: ReceiptLine) -> ReceiptLine:
        self.db.add(line)
        self.db.flush()
        self.db.refresh(line)
        return line

    def list_receipt_lines(self, receipt_id: int) -> list[ReceiptLine]:
        statement = select(ReceiptLine).where(ReceiptLine.receipt_id == receipt_id).order_by(ReceiptLine.id.asc())
        return list(self.db.scalars(statement))

    def count_receipts(self) -> int:
        # Count live collections from billing_invoices (the operational collection flow)
        statement = select(func.count(BillingInvoice.id)).where(
            BillingInvoice.is_cancelled == False,  # noqa: E712
            BillingInvoice.total_receive_amount > 0,
        )
        return int(self.db.scalar(statement) or 0)

    def sum_receipts(self) -> float:
        # Sum live collections from billing_invoices (the operational collection flow)
        statement = select(
            func.coalesce(func.sum(BillingInvoice.total_receive_amount), 0)
        ).where(
            BillingInvoice.is_cancelled == False,  # noqa: E712
        )
        return float(self.db.scalar(statement) or 0)

    def summarize_open_charges(self) -> tuple[int, float]:
        statement = select(func.count(Charge.id), func.coalesce(func.sum(Charge.due_amount), 0)).where(
            Charge.due_amount > 0
        )
        result = self.db.execute(statement).one()
        return int(result[0] or 0), float(result[1] or 0)

    def summarize_members_with_due(self) -> int:
        statement = select(func.count(func.distinct(Charge.member_id))).where(Charge.due_amount > 0)
        return int(self.db.scalar(statement) or 0)

    def list_member_due_summaries(self) -> list[tuple[int, str, str, float, float, int]]:
        statement = (
            select(
                Member.id,
                Member.member_code,
                Member.full_name,
                func.coalesce(func.sum(Charge.net_amount), 0),
                func.coalesce(func.sum(Charge.due_amount), 0),
                func.count(Charge.id),
            )
            .join(Charge, Charge.member_id == Member.id)
            .group_by(Member.id, Member.member_code, Member.full_name)
            .having(func.coalesce(func.sum(Charge.due_amount), 0) > 0)
            .order_by(Member.member_code.asc(), Member.full_name.asc())
        )
        return [tuple(row) for row in self.db.execute(statement).all()]

    def list_billing_heads(self, active_only: bool = False) -> list[BillingHead]:
        sequence = {
            "Monthly Subscription": 1,
            "Registration Fee": 2,
            "Other Charges": 3,
            "Electric Service": 4,
            "Development Charge": 5,
        }
        heads = list(self.db.scalars(select(BillingHead)))
        if active_only:
            heads = [head for head in heads if head.is_active]
        return sorted(
            heads,
            key=lambda head: (
                sequence.get(head.head_name, 99),
                head.head_name.lower(),
                head.id,
            ),
        )

    def get_billing_head(self, head_id: int) -> BillingHead | None:
        return self.db.get(BillingHead, head_id)

    def add_billing_head(self, head: BillingHead) -> BillingHead:
        self.db.add(head)
        self.db.flush()
        self.db.refresh(head)
        return head

    def list_head_mappings(self, active_only: bool = False) -> list[BillingHeadCoaMapping]:
        statement = select(BillingHeadCoaMapping).order_by(BillingHeadCoaMapping.id.desc())
        if active_only:
            statement = statement.where(BillingHeadCoaMapping.is_active == True)  # noqa: E712
        return list(self.db.scalars(statement))

    def get_head_mapping(self, mapping_id: int) -> BillingHeadCoaMapping | None:
        return self.db.get(BillingHeadCoaMapping, mapping_id)

    def get_active_head_mapping(self, head_id: int) -> BillingHeadCoaMapping | None:
        statement = select(BillingHeadCoaMapping).where(
            BillingHeadCoaMapping.billing_head_id == head_id,
            BillingHeadCoaMapping.is_active == True,  # noqa: E712
        )
        return self.db.scalar(statement)

    def add_head_mapping(self, mapping: BillingHeadCoaMapping) -> BillingHeadCoaMapping:
        self.db.add(mapping)
        self.db.flush()
        self.db.refresh(mapping)
        return mapping

    def add_invoice(self, invoice: BillingInvoice) -> BillingInvoice:
        self.db.add(invoice)
        self.db.flush()
        self.db.refresh(invoice)
        return invoice

    def add_invoice_detail(self, detail: BillingInvoiceDetail) -> BillingInvoiceDetail:
        self.db.add(detail)
        self.db.flush()
        self.db.refresh(detail)
        return detail

    def get_invoice(self, invoice_id: int) -> BillingInvoice | None:
        return self.db.get(BillingInvoice, invoice_id)

    def get_invoice_by_no(self, invoice_no: str) -> BillingInvoice | None:
        return self.db.scalar(select(BillingInvoice).where(BillingInvoice.invoice_no == invoice_no))

    def list_invoices(
        self,
        member_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        limit: int | None = None,
    ) -> list[BillingInvoice]:
        statement = select(BillingInvoice).order_by(BillingInvoice.invoice_date.desc(), BillingInvoice.id.desc())
        if member_id is not None:
            statement = statement.where(BillingInvoice.member_id == member_id)
        if from_date is not None:
            statement = statement.where(BillingInvoice.invoice_date >= from_date)
        if to_date is not None:
            statement = statement.where(BillingInvoice.invoice_date <= to_date)
        if limit is not None:
            statement = statement.limit(limit)
        return list(self.db.scalars(statement))

    def list_invoice_details(self, invoice_id: int | None = None) -> list[BillingInvoiceDetail]:
        statement = select(BillingInvoiceDetail).order_by(BillingInvoiceDetail.period_date.asc(), BillingInvoiceDetail.id.asc())
        if invoice_id is not None:
            statement = statement.where(BillingInvoiceDetail.invoice_id == invoice_id)
        return list(self.db.scalars(statement))

    def get_next_invoice_sequence(self) -> int:
        result = self.db.execute(text("SELECT NEXT VALUE FOR billing.invoice_sequence"))
        return result.scalar()

    def count_invoices(self) -> int:
        return int(self.db.scalar(select(func.count(BillingInvoice.id))) or 0)

    def paged_charge_register(
        self,
        *,
        from_date: date | None,
        to_date: date | None,
        search: str,
        order_key: str,
        order_dir: str,
        start: int,
        length: int,
    ) -> tuple[int, int, list[dict[str, object]], dict[str, float]]:
        item_summary = (
            select(
                ChargeItem.charge_id.label("charge_id"),
                func.string_agg(func.coalesce(ChargeItem.description, ChargeItem.item_type), literal(", ", String(10))).label("head_summary"),
            )
            .group_by(ChargeItem.charge_id)
            .subquery()
        )
        paid_amount = Charge.net_amount - Charge.due_amount
        status_rank = case((Charge.due_amount <= 0, 0), (paid_amount > 0, 1), else_=2)
        base = (
            select(
                Charge.id.label("id"),
                Member.full_name.label("member_name"),
                Member.member_code.label("member_code"),
                Member.plot_no.label("plot_no"),
                Charge.created_at.label("created_at"),
                BillingPeriod.period_name.label("billing_period_name"),
                func.coalesce(item_summary.c.head_summary, Charge.charge_type).label("head_summary"),
                Charge.net_amount.label("net_amount"),
                paid_amount.label("paid_amount"),
                Charge.due_amount.label("due_amount"),
                Charge.status.label("status"),
            )
            .join(Member, Member.id == Charge.member_id)
            .outerjoin(BillingPeriod, BillingPeriod.id == Charge.billing_period_id)
            .outerjoin(item_summary, item_summary.c.charge_id == Charge.id)
        )
        if from_date is not None:
            base = base.where(cast(Charge.created_at, Date) >= from_date)
        if to_date is not None:
            base = base.where(cast(Charge.created_at, Date) <= to_date)
        total_records = int(self.db.scalar(select(func.count()).select_from(base.subquery())) or 0)
        if search:
            needle = f"%{search.lower()}%"
            base = base.where(
                or_(
                    func.lower(Member.full_name).like(needle),
                    func.lower(Member.member_code).like(needle),
                    func.lower(func.coalesce(Member.plot_no, "")).like(needle),
                    func.lower(func.coalesce(BillingPeriod.period_name, "")).like(needle),
                    func.lower(func.coalesce(item_summary.c.head_summary, Charge.charge_type)).like(needle),
                    func.lower(Charge.status).like(needle),
                    cast(cast(Charge.created_at, Date), String).like(needle),
                )
            )
        filtered_records = int(self.db.scalar(select(func.count()).select_from(base.subquery())) or 0)
        order_map = {
            "member": literal_column_safe("member_name"),
            "date": literal_column_safe("created_at"),
            "period": literal_column_safe("billing_period_name"),
            "head": literal_column_safe("head_summary"),
            "net": literal_column_safe("net_amount"),
            "paid": literal_column_safe("paid_amount"),
            "due": literal_column_safe("due_amount"),
            "status": status_rank,
        }
        order_expr = order_map.get(order_key, literal_column_safe("created_at"))
        ordered = base.order_by(order_expr.asc() if order_dir == "asc" else order_expr.desc(), literal_column_safe("id").desc())
        rows = self.db.execute(ordered.offset(start).limit(length)).mappings().all()
        totals_row = self.db.execute(
            select(
                func.coalesce(func.sum(base.subquery().c.net_amount), 0).label("total_bill_amount"),
                func.coalesce(func.sum(base.subquery().c.paid_amount), 0).label("total_paid"),
                func.coalesce(func.sum(base.subquery().c.due_amount), 0).label("total_due"),
            )
        ).one()
        return total_records, filtered_records, [dict(row) for row in rows], {
            "total_bill_amount": float(totals_row.total_bill_amount or 0),
            "total_paid": float(totals_row.total_paid or 0),
            "total_due": float(totals_row.total_due or 0),
        }

    def paged_receipt_register(
        self,
        *,
        from_date: date | None,
        to_date: date | None,
        search: str,
        order_key: str,
        order_dir: str,
        start: int,
        length: int,
    ) -> tuple[int, int, list[dict[str, object]], dict[str, float]]:
        base = (
            select(
                Receipt.id.label("id"),
                Receipt.receipt_no.label("receipt_no"),
                Member.full_name.label("member_name"),
                Member.member_code.label("member_code"),
                Member.plot_no.label("plot_no"),
                Receipt.payment_date.label("payment_date"),
                Receipt.total_amount.label("total_amount"),
                Receipt.notes.label("notes"),
            )
            .outerjoin(Member, Member.id == Receipt.member_id)
        )
        if from_date is not None:
            base = base.where(Receipt.payment_date >= from_date)
        if to_date is not None:
            base = base.where(Receipt.payment_date <= to_date)
        total_records = int(self.db.scalar(select(func.count()).select_from(base.subquery())) or 0)
        if search:
            needle = f"%{search.lower()}%"
            base = base.where(
                or_(
                    func.lower(Receipt.receipt_no).like(needle),
                    func.lower(func.coalesce(Member.full_name, "")).like(needle),
                    func.lower(func.coalesce(Member.member_code, "")).like(needle),
                    func.lower(func.coalesce(Member.plot_no, "")).like(needle),
                    cast(Receipt.payment_date, String).like(needle),
                    func.lower(func.coalesce(Receipt.notes, "")).like(needle),
                )
            )
        filtered_records = int(self.db.scalar(select(func.count()).select_from(base.subquery())) or 0)
        order_map = {
            "receipt": literal_column_safe("receipt_no"),
            "member": literal_column_safe("member_name"),
            "plot": literal_column_safe("plot_no"),
            "date": literal_column_safe("payment_date"),
            "total": literal_column_safe("total_amount"),
        }
        order_expr = order_map.get(order_key, literal_column_safe("payment_date"))
        ordered = base.order_by(order_expr.asc() if order_dir == "asc" else order_expr.desc(), literal_column_safe("id").desc())
        rows = self.db.execute(ordered.offset(start).limit(length)).mappings().all()
        totals_row = self.db.execute(select(func.coalesce(func.sum(base.subquery().c.total_amount), 0).label("total_collection"))).one()
        return total_records, filtered_records, [dict(row) for row in rows], {
            "total_collection": float(totals_row.total_collection or 0),
        }

    def paged_invoice_register(
        self,
        *,
        member_id: int | None,
        from_date: date | None,
        to_date: date | None,
        search: str,
        order_key: str,
        order_dir: str,
        start: int,
        length: int,
    ) -> tuple[int, int, list[dict[str, object]], dict[str, float]]:
        status_text = case(
            (BillingInvoice.is_cancelled == True, "Cancelled"),  # noqa: E712
            (BillingInvoice.total_due_amount <= 0, "Paid"),
            (BillingInvoice.total_receive_amount > 0, "Partial"),
            else_="Due",
        )
        base = select(
            BillingInvoice.id.label("id"),
            BillingInvoice.member_id.label("member_id"),
            BillingInvoice.invoice_no.label("invoice_no"),
            BillingInvoice.invoice_date.label("invoice_date"),
            BillingInvoice.subtotal_amount.label("subtotal_amount"),
            BillingInvoice.discount_amount.label("discount_amount"),
            BillingInvoice.total_receive_amount.label("total_receive_amount"),
            BillingInvoice.total_due_amount.label("total_due_amount"),
            status_text.label("status"),
        ).where(
            BillingInvoice.is_cancelled == False,  # noqa: E712
        )
        if member_id is not None:
            base = base.where(BillingInvoice.member_id == member_id)
        if from_date is not None:
            base = base.where(BillingInvoice.invoice_date >= from_date)
        if to_date is not None:
            base = base.where(BillingInvoice.invoice_date <= to_date)
        total_records = int(self.db.scalar(select(func.count()).select_from(base.subquery())) or 0)
        if search:
            needle = f"%{search.lower()}%"
            base = base.where(
                or_(
                    func.lower(BillingInvoice.invoice_no).like(needle),
                    cast(BillingInvoice.invoice_date, String).like(needle),
                    func.lower(status_text).like(needle),
                )
            )
        filtered_records = int(self.db.scalar(select(func.count()).select_from(base.subquery())) or 0)
        order_map = {
            "invoice": literal_column_safe("invoice_no"),
            "date": literal_column_safe("invoice_date"),
            "subtotal": literal_column_safe("subtotal_amount"),
            "discount": literal_column_safe("discount_amount"),
            "received": literal_column_safe("total_receive_amount"),
            "due": literal_column_safe("total_due_amount"),
            "status": literal_column_safe("status"),
        }
        order_expr = order_map.get(order_key, literal_column_safe("invoice_date"))
        ordered = base.order_by(order_expr.asc() if order_dir == "asc" else order_expr.desc(), literal_column_safe("id").desc())
        rows = self.db.execute(ordered.offset(start).limit(length)).mappings().all()
        base_subq = base.subquery()
        detail_q = select(
            func.max(BillingInvoiceDetail.fee_amount).label("max_fee")
        ).join(
            base_subq, base_subq.c.id == BillingInvoiceDetail.invoice_id
        ).group_by(
            base_subq.c.member_id,
            BillingInvoiceDetail.billing_head_id,
            func.coalesce(cast(BillingInvoiceDetail.period_date, String), "1900-01-01"),
            func.coalesce(BillingInvoiceDetail.period_display, "OneTime")
        ).subquery()
        
        total_bill = float(self.db.scalar(select(func.coalesce(func.sum(detail_q.c.max_fee), 0))) or 0.0)
        
        totals_row = self.db.execute(
            select(
                func.coalesce(func.sum(base_subq.c.total_receive_amount), 0).label("total_paid"),
                func.coalesce(func.sum(base_subq.c.discount_amount), 0).label("total_discount"),
            )
        ).one()
        
        total_paid = float(totals_row.total_paid or 0)
        total_discount = float(totals_row.total_discount or 0)
        total_due = max(total_bill - total_paid - total_discount, 0.0)
        
        return total_records, filtered_records, [dict(row) for row in rows], {
            "total_bill_amount": total_bill,
            "total_paid": total_paid,
            "total_due": total_due,
        }
    def get_member_outstanding_due(self, member_id: int) -> float:
        base = select(
            BillingInvoice.id.label("id"),
            BillingInvoice.member_id.label("member_id"),
            BillingInvoice.discount_amount.label("discount_amount"),
            BillingInvoice.total_receive_amount.label("total_receive_amount"),
        ).where(
            BillingInvoice.is_cancelled == False,  # noqa: E712
            BillingInvoice.member_id == member_id,
        )
        base_subq = base.subquery()
        detail_q = select(
            func.max(BillingInvoiceDetail.fee_amount).label("max_fee")
        ).join(
            base_subq, base_subq.c.id == BillingInvoiceDetail.invoice_id
        ).group_by(
            base_subq.c.member_id,
            BillingInvoiceDetail.billing_head_id,
            func.coalesce(cast(BillingInvoiceDetail.period_date, String), "1900-01-01"),
            func.coalesce(BillingInvoiceDetail.period_display, "OneTime")
        ).subquery()
        
        total_bill = float(self.db.scalar(select(func.coalesce(func.sum(detail_q.c.max_fee), 0))) or 0.0)
        
        totals_row = self.db.execute(
            select(
                func.coalesce(func.sum(base_subq.c.total_receive_amount), 0).label("total_paid"),
                func.coalesce(func.sum(base_subq.c.discount_amount), 0).label("total_discount"),
            )
        ).one_or_none()
        
        if totals_row is None:
            total_paid = 0.0
            total_discount = 0.0
        else:
            total_paid = float(totals_row.total_paid or 0)
            total_discount = float(totals_row.total_discount or 0)
            
        return max(total_bill - total_paid - total_discount, 0.0)

    def get_period_payment_totals(self, member_id: int, head_id: int, period_date) -> float:
        statement = (
            select(
                func.coalesce(func.sum(BillingInvoiceDetail.receive_amount + BillingInvoiceDetail.discount_amount), 0)
            )
            .join(BillingInvoice, BillingInvoice.id == BillingInvoiceDetail.invoice_id)
            .where(
                BillingInvoice.is_cancelled == False,  # noqa: E712
                BillingInvoiceDetail.member_id == member_id,
                BillingInvoiceDetail.billing_head_id == head_id,
                BillingInvoiceDetail.period_date == period_date,
            )
        )
        paid = self.db.scalar(statement)
        return float(paid or 0)

    def get_all_period_payment_totals(self, member_id: int) -> dict[tuple[int, date], float]:
        statement = (
            select(
                BillingInvoiceDetail.billing_head_id,
                BillingInvoiceDetail.period_date,
                func.coalesce(func.sum(BillingInvoiceDetail.receive_amount + BillingInvoiceDetail.discount_amount), 0),
            )
            .join(BillingInvoice, BillingInvoice.id == BillingInvoiceDetail.invoice_id)
            .where(
                BillingInvoice.is_cancelled == False,  # noqa: E712
                BillingInvoiceDetail.member_id == member_id,
                BillingInvoiceDetail.period_date.is_not(None),
            )
            .group_by(BillingInvoiceDetail.billing_head_id, BillingInvoiceDetail.period_date)
        )
        rows = self.db.execute(statement).all()
        return {(head_id, period_date): float(paid or 0) for head_id, period_date, paid in rows}

    def get_one_time_payment_totals(self, member_id: int, head_id: int) -> float:
        statement = (
            select(
                func.coalesce(func.sum(BillingInvoiceDetail.receive_amount + BillingInvoiceDetail.discount_amount), 0)
            )
            .join(BillingInvoice, BillingInvoice.id == BillingInvoiceDetail.invoice_id)
            .where(
                BillingInvoice.is_cancelled == False,  # noqa: E712
                BillingInvoiceDetail.member_id == member_id,
                BillingInvoiceDetail.billing_head_id == head_id,
                BillingInvoiceDetail.period_date.is_(None),
            )
        )
        paid = self.db.scalar(statement)
        return float(paid or 0)

    def get_all_one_time_payment_totals(self, member_id: int) -> dict[int, float]:
        statement = (
            select(
                BillingInvoiceDetail.billing_head_id,
                func.coalesce(func.sum(BillingInvoiceDetail.receive_amount + BillingInvoiceDetail.discount_amount), 0),
            )
            .join(BillingInvoice, BillingInvoice.id == BillingInvoiceDetail.invoice_id)
            .where(
                BillingInvoice.is_cancelled == False,  # noqa: E712
                BillingInvoiceDetail.member_id == member_id,
                BillingInvoiceDetail.period_date.is_(None),
            )
            .group_by(BillingInvoiceDetail.billing_head_id)
        )
        rows = self.db.execute(statement).all()
        return {head_id: float(paid or 0) for head_id, paid in rows}

    def list_accounts(self) -> list[Account]:
        return list(self.db.scalars(select(Account).order_by(Account.code.asc())))

    def get_due_tracker(self, member_id: int, head_id: int, period_date) -> BillingDueTracker | None:
        statement = select(BillingDueTracker).where(
            BillingDueTracker.member_id == member_id,
            BillingDueTracker.billing_head_id == head_id,
            BillingDueTracker.period_date == period_date,
        )
        return self.db.scalar(statement)

    def add_due_tracker(self, due: BillingDueTracker) -> BillingDueTracker:
        self.db.add(due)
        self.db.flush()
        self.db.refresh(due)
        return due

    def list_due_trackers(self, member_id: int | None = None) -> list[BillingDueTracker]:
        statement = select(BillingDueTracker).order_by(BillingDueTracker.member_id.asc(), BillingDueTracker.period_date.asc(), BillingDueTracker.id.asc())
        if member_id is not None:
            statement = statement.where(BillingDueTracker.member_id == member_id)
        return list(self.db.scalars(statement))

    def unlink_invoice_from_due_tracker(self, invoice_id: int) -> None:
        self.db.query(BillingDueTracker).filter(BillingDueTracker.last_invoice_id == invoice_id).update({"last_invoice_id": None})
        self.db.flush()

    def add_voided_invoice(self, voided_invoice: BillingVoidedInvoice) -> BillingVoidedInvoice:
        self.db.add(voided_invoice)
        self.db.flush()
        self.db.refresh(voided_invoice)
        return voided_invoice

    def add_voided_invoice_detail(self, voided_detail: BillingVoidedInvoiceDetail) -> BillingVoidedInvoiceDetail:
        self.db.add(voided_detail)
        self.db.flush()
        self.db.refresh(voided_detail)
        return voided_detail

    def delete_invoice(self, invoice: BillingInvoice) -> None:
        # Unlink from Accounting IncomeEntryDetails to avoid Foreign Key violation
        from app.modules.accounting.models import IncomeEntryDetail
        self.db.query(IncomeEntryDetail).filter(
            IncomeEntryDetail.billing_detail_id.in_(
                self.db.query(BillingInvoiceDetail.id).filter(BillingInvoiceDetail.invoice_id == invoice.id)
            )
        ).update({"billing_detail_id": None}, synchronize_session=False)
        self.db.flush()

        self.db.delete(invoice)
        self.db.flush()


def literal_column_safe(column_name: str):
    return column(column_name)
