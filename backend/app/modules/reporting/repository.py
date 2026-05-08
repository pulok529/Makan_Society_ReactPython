from sqlalchemy import Select, and_, select
from sqlalchemy.orm import Session

from app.modules.billing.models import BillingPeriod, Charge, Receipt, ReceiptLine
from app.modules.categories.models import MemberCategory
from app.modules.members.models import Member, MemberPackage
from app.modules.packages.models import Package


class ReportingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_members(self, *, member_id: int | None = None, category_id: int | None = None) -> list[Member]:
        statement: Select[tuple[Member]] = select(Member).order_by(Member.full_name.asc())
        if member_id is not None:
            statement = statement.where(Member.id == member_id)
        if category_id is not None:
            statement = statement.where(Member.category_id == category_id)
        return list(self.db.scalars(statement))

    def list_categories(self) -> list[MemberCategory]:
        return list(self.db.scalars(select(MemberCategory).order_by(MemberCategory.name.asc())))

    def list_packages(self) -> list[Package]:
        return list(self.db.scalars(select(Package).order_by(Package.name.asc())))

    def list_member_packages(self) -> list[MemberPackage]:
        return list(self.db.scalars(select(MemberPackage).order_by(MemberPackage.id.asc())))

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

    def get_receipt(self, receipt_id: int) -> Receipt | None:
        return self.db.get(Receipt, receipt_id)

    def list_receipt_lines(self, receipt_id: int) -> list[ReceiptLine]:
        statement = select(ReceiptLine).where(ReceiptLine.receipt_id == receipt_id).order_by(ReceiptLine.id.asc())
        return list(self.db.scalars(statement))
