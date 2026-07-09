from sqlalchemy import Integer, and_, case, cast, exists, func, or_, select
from sqlalchemy.orm import Session

from app.modules.billing.models import BillingDueTracker
from app.modules.members.models import Member, MemberNominee, MemberPackage


class MemberRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_members(self, search: str | None = None) -> list[Member]:
        statement = self._member_ordered_statement()
        if search:
            statement = statement.where(self._search_expression(search))
        return list(self.db.scalars(statement))

    def paged_members(
        self,
        *,
        search: str | None = None,
        is_active: bool | None = None,
        category_id: int | None = None,
        has_phone: bool | None = None,
        due_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[Member]]:
        statement = self._member_ordered_statement()
        count_statement = select(func.count()).select_from(Member)
        conditions = []
        if search:
            conditions.append(self._search_expression(search))
        if is_active is not None:
            conditions.append(Member.is_active == is_active)
        if category_id is not None:
            conditions.append(Member.category_id == category_id)
        if has_phone is True:
            conditions.append(Member.cell_no.is_not(None))
            conditions.append(Member.cell_no != "")
        elif has_phone is False:
            conditions.append(or_(Member.cell_no.is_(None), Member.cell_no == ""))
        if due_only:
            due_exists = exists(
                select(BillingDueTracker.id).where(
                    BillingDueTracker.member_id == Member.id,
                    BillingDueTracker.is_settled == False,  # noqa: E712
                    BillingDueTracker.due_amount > 0,
                )
            )
            conditions.append(due_exists)
        for condition in conditions:
            statement = statement.where(condition)
            count_statement = count_statement.where(condition)
        total = int(self.db.scalar(count_statement) or 0)
        items = list(self.db.scalars(statement.offset(offset).limit(limit)))
        return total, items

    def search_members(
        self,
        *,
        query: str,
        limit: int = 20,
        is_active: bool | None = True,
        has_phone: bool | None = None,
        due_only: bool = False,
        category_id: int | None = None,
    ) -> list[Member]:
        _total, items = self.paged_members(
            search=query,
            is_active=is_active,
            category_id=category_id,
            has_phone=has_phone,
            due_only=due_only,
            limit=limit,
            offset=0,
        )
        return items

    def _member_ordered_statement(self):
        numeric_member_code = case(
            (
                and_(
                    Member.member_code.is_not(None),
                    Member.member_code != "",
                    Member.member_code.op("NOT LIKE")("%[^0-9]%"),
                ),
                cast(Member.member_code, Integer),
            ),
            else_=None,
        )
        return select(Member).order_by(
            case((numeric_member_code.is_(None), 1), else_=0).asc(),
            numeric_member_code.asc(),
            Member.member_code.asc(),
            Member.full_name.asc(),
        )

    @staticmethod
    def _search_expression(search: str):
        pattern = f"%{search.strip()}%"
        return or_(
            Member.full_name.ilike(pattern),
            Member.member_code.ilike(pattern),
            Member.cell_no.ilike(pattern),
            Member.plot_no.ilike(pattern),
            Member.member_id_text.ilike(pattern),
        )

    def get_by_id(self, member_id: int) -> Member | None:
        return self.db.get(Member, member_id)

    def get_by_code(self, member_code: str) -> Member | None:
        statement = select(Member).where(Member.member_code == member_code)
        return self.db.scalar(statement)

    def get_nominee(self, member_id: int) -> MemberNominee | None:
        statement = select(MemberNominee).where(MemberNominee.member_id == member_id)
        return self.db.scalar(statement)

    def list_member_packages(self, member_id: int) -> list[MemberPackage]:
        statement = (
            select(MemberPackage)
            .where(MemberPackage.member_id == member_id)
            .order_by(MemberPackage.assigned_on.desc(), MemberPackage.id.desc())
        )
        return list(self.db.scalars(statement))

    def add_member(self, member: Member) -> Member:
        self.db.add(member)
        self.db.flush()
        self.db.refresh(member)
        return member

    def add_nominee(self, nominee: MemberNominee) -> MemberNominee:
        self.db.add(nominee)
        self.db.flush()
        self.db.refresh(nominee)
        return nominee

    def add_member_package(self, member_package: MemberPackage) -> MemberPackage:
        self.db.add(member_package)
        self.db.flush()
        self.db.refresh(member_package)
        return member_package
