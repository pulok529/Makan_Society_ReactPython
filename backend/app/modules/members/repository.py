from sqlalchemy import Integer, case, func, or_, select
from sqlalchemy.orm import Session

from app.modules.members.models import Member, MemberNominee, MemberPackage


class MemberRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_members(self, search: str | None = None) -> list[Member]:
        numeric_member_code = func.try_cast(Member.member_code, Integer)
        statement = select(Member).order_by(
            case((numeric_member_code.is_(None), 1), else_=0).asc(),
            numeric_member_code.asc(),
            Member.member_code.asc(),
            Member.full_name.asc(),
        )
        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    Member.full_name.ilike(pattern),
                    Member.member_code.ilike(pattern),
                    Member.cell_no.ilike(pattern),
                    Member.plot_no.ilike(pattern),
                )
            )
        return list(self.db.scalars(statement))

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
