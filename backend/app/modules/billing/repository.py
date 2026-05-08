from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.modules.accounting.models import Account
from app.modules.billing.models import (
    BillingHead,
    BillingHeadCoaMapping,
    BillingInvoice,
    BillingInvoiceDetail,
    BillingPeriod,
    Charge,
    ChargeItem,
    Receipt,
    ReceiptLine,
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

    def list_charges(self, billing_period_id: int | None = None, member_id: int | None = None) -> list[Charge]:
        statement: Select[tuple[Charge]] = select(Charge).order_by(Charge.created_at.desc(), Charge.id.desc())
        if billing_period_id is not None:
            statement = statement.where(Charge.billing_period_id == billing_period_id)
        if member_id is not None:
            statement = statement.where(Charge.member_id == member_id)
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

    def list_receipts(self, member_id: int | None = None) -> list[Receipt]:
        statement = select(Receipt).order_by(Receipt.payment_date.desc(), Receipt.id.desc())
        if member_id is not None:
            statement = statement.where(Receipt.member_id == member_id)
        return list(self.db.scalars(statement))

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
        statement = select(func.count(Receipt.id))
        return int(self.db.scalar(statement) or 0)

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

    def list_invoices(self, member_id: int | None = None) -> list[BillingInvoice]:
        statement = select(BillingInvoice).order_by(BillingInvoice.invoice_date.desc(), BillingInvoice.id.desc())
        if member_id is not None:
            statement = statement.where(BillingInvoice.member_id == member_id)
        return list(self.db.scalars(statement))

    def list_invoice_details(self, invoice_id: int | None = None) -> list[BillingInvoiceDetail]:
        statement = select(BillingInvoiceDetail).order_by(BillingInvoiceDetail.period_date.asc(), BillingInvoiceDetail.id.asc())
        if invoice_id is not None:
            statement = statement.where(BillingInvoiceDetail.invoice_id == invoice_id)
        return list(self.db.scalars(statement))

    def count_invoices(self) -> int:
        return int(self.db.scalar(select(func.count(BillingInvoice.id))) or 0)

    def get_period_payment_totals(self, member_id: int, head_id: int, period_date) -> tuple[float, float]:
        statement = (
            select(
                func.coalesce(func.sum(BillingInvoiceDetail.receive_amount + BillingInvoiceDetail.discount_amount), 0),
                func.coalesce(func.max(BillingInvoiceDetail.fee_amount), 0),
            )
            .join(BillingInvoice, BillingInvoice.id == BillingInvoiceDetail.invoice_id)
            .where(
                BillingInvoice.is_cancelled == False,  # noqa: E712
                BillingInvoiceDetail.member_id == member_id,
                BillingInvoiceDetail.billing_head_id == head_id,
                BillingInvoiceDetail.period_date == period_date,
            )
        )
        paid, fee = self.db.execute(statement).one()
        paid_total = float(paid or 0)
        due_total = max(float(fee or 0) - paid_total, 0)
        return paid_total, due_total

    def list_accounts(self) -> list[Account]:
        return list(self.db.scalars(select(Account).order_by(Account.code.asc())))
