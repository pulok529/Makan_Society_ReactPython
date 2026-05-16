from datetime import UTC, date, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.categories.repository import CategoryRepository
from app.modules.members.models import Member, MemberNominee, MemberPackage
from app.modules.members.repository import MemberRepository
from app.modules.members.schemas import MemberCreate, MemberPackageAssignmentCreate, MemberUpdate
from app.modules.packages.repository import PackageRepository


class MemberService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = MemberRepository(db)
        self.category_repository = CategoryRepository(db)
        self.package_repository = PackageRepository(db)

    def list_members(self, search: str | None = None) -> list[Member]:
        return self.repository.list_members(search)

    def get_member(self, member_id: int) -> Member:
        member = self.repository.get_by_id(member_id)
        if member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        return member

    def create_member(self, payload: MemberCreate) -> Member:
        if self.repository.get_by_code(payload.member_code.strip()) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Member code already exists",
            )

        if payload.category_id is not None and self.category_repository.get_by_id(payload.category_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        member = Member(
            member_code=payload.member_code.strip(),
            member_id_text=payload.member_id_text.strip() if payload.member_id_text else None,
            plot_no=payload.plot_no.strip() if payload.plot_no else None,
            full_name=payload.full_name.strip(),
            father_name=payload.father_name.strip() if payload.father_name else None,
            mother_name=payload.mother_name.strip() if payload.mother_name else None,
            present_address=payload.present_address.strip() if payload.present_address else None,
            permanent_address=payload.permanent_address.strip() if payload.permanent_address else None,
            cell_no=payload.cell_no.strip() if payload.cell_no else None,
            email=payload.email.strip() if payload.email else None,
            reference=payload.reference.strip() if payload.reference else None,
            national_id=payload.national_id.strip() if payload.national_id else None,
            category_id=payload.category_id,
            member_class=payload.member_class.strip() if payload.member_class else None,
            joined_on=payload.joined_on or date.today(),
            is_active=payload.is_active,
            entry_at=datetime.now(UTC),
        )
        self.repository.add_member(member)

        if payload.nominee and (payload.nominee.nominee_name or payload.nominee.nominee_cell):
            self.repository.add_nominee(
                MemberNominee(
                    member_id=member.id,
                    nominee_name=payload.nominee.nominee_name.strip()
                    if payload.nominee.nominee_name
                    else None,
                    nominee_cell=payload.nominee.nominee_cell.strip()
                    if payload.nominee.nominee_cell
                    else None,
                )
            )

        if payload.initial_package is not None:
            self.assign_package(member.id, payload.initial_package)

        self.db.commit()
        self.db.refresh(member)
        return member

    def assign_package(self, member_id: int, payload: MemberPackageAssignmentCreate) -> MemberPackage:
        member = self.repository.get_by_id(member_id)
        if member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        package = self.package_repository.get_by_id(payload.package_id)
        if package is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")

        assignment = MemberPackage(
            member_id=member_id,
            package_id=payload.package_id,
            assigned_on=payload.assigned_on,
            ended_on=payload.ended_on,
            is_active=payload.is_active,
        )
        self.repository.add_member_package(assignment)
        self.db.flush()
        return assignment

    def update_member(self, member_id: int, payload: MemberUpdate) -> Member:
        member = self.get_member(member_id)
        existing = self.repository.get_by_code(payload.member_code.strip())
        if existing is not None and existing.id != member_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Member code already exists")
        if payload.category_id is not None and self.category_repository.get_by_id(payload.category_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        member.member_code = payload.member_code.strip()
        member.member_id_text = payload.member_id_text.strip() if payload.member_id_text else None
        member.plot_no = payload.plot_no.strip() if payload.plot_no else None
        member.full_name = payload.full_name.strip()
        member.father_name = payload.father_name.strip() if payload.father_name else None
        member.mother_name = payload.mother_name.strip() if payload.mother_name else None
        member.present_address = payload.present_address.strip() if payload.present_address else None
        member.permanent_address = payload.permanent_address.strip() if payload.permanent_address else None
        member.cell_no = payload.cell_no.strip() if payload.cell_no else None
        member.email = payload.email.strip() if payload.email else None
        member.reference = payload.reference.strip() if payload.reference else None
        member.national_id = payload.national_id.strip() if payload.national_id else None
        member.category_id = payload.category_id
        member.member_class = payload.member_class.strip() if payload.member_class else None
        if payload.joined_on is not None:
            member.joined_on = payload.joined_on
        member.is_active = payload.is_active
        member.entry_at = datetime.now(UTC)

        if payload.nominee is not None:
            nominee = self.repository.get_nominee(member_id)
            if nominee is None:
                nominee = MemberNominee(member_id=member_id)
                self.repository.add_nominee(nominee)
            nominee.nominee_name = payload.nominee.nominee_name.strip() if payload.nominee.nominee_name else None
            nominee.nominee_cell = payload.nominee.nominee_cell.strip() if payload.nominee.nominee_cell else None

        if payload.package_id is not None:
            package = self.package_repository.get_by_id(payload.package_id)
            if package is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
            assignments = self.repository.list_member_packages(member_id)
            active_assignments = [assignment for assignment in assignments if assignment.is_active]
            current_active = next((assignment for assignment in active_assignments if assignment.package_id == payload.package_id), None)
            if current_active is None:
                assigned_on = payload.joined_on or member.joined_on or date.today()
                for assignment in active_assignments:
                    assignment.is_active = False
                    assignment.ended_on = assigned_on
                self.repository.add_member_package(
                    MemberPackage(
                        member_id=member_id,
                        package_id=payload.package_id,
                        assigned_on=assigned_on,
                        ended_on=None,
                        is_active=True,
                    )
                )

        self.db.commit()
        self.db.refresh(member)
        return member
