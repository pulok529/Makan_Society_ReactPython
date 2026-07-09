from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.categories.repository import CategoryRepository
from app.modules.members.repository import MemberRepository
from app.modules.members.schemas import (
    MemberCreate,
    MemberDetailRead,
    MemberListPage,
    MemberListItem,
    MemberPackageAssignmentCreate,
    MemberPackageAssignmentRead,
    MemberSearchItem,
    MemberUpdate,
)
from app.modules.members.service import MemberService

router = APIRouter(prefix="/members", tags=["members"])


def _serialize_member_detail(member_id: int, db: Session) -> MemberDetailRead:
    service = MemberService(db)
    repository = MemberRepository(db)
    categories = {category.id: category for category in CategoryRepository(db).list_categories()}

    member = service.get_member(member_id)
    nominee = repository.get_nominee(member_id)
    assignments = repository.list_member_packages(member_id)

    return MemberDetailRead(
        id=member.id,
        member_code=member.member_code,
        member_id_text=member.member_id_text,
        plot_no=member.plot_no,
        plot_count=member.plot_count,
        full_name=member.full_name,
        father_name=member.father_name,
        mother_name=member.mother_name,
        present_address=member.present_address,
        permanent_address=member.permanent_address,
        cell_no=member.cell_no,
        email=member.email,
        reference=member.reference,
        national_id=member.national_id,
        category_id=member.category_id,
        category_name=categories[member.category_id].name if member.category_id in categories else None,
        member_class=member.member_class,
        joined_on=member.joined_on,
        is_active=member.is_active,
        created_at=member.created_at,
        entry_at=member.entry_at,
        nominee_name=nominee.nominee_name if nominee is not None else None,
        nominee_cell=nominee.nominee_cell if nominee is not None else None,
        packages=[
            MemberPackageAssignmentRead(
                id=assignment.id,
                package_id=assignment.package_id,
                package_name="Legacy Package",
                assigned_on=assignment.assigned_on,
                ended_on=assignment.ended_on,
                is_active=assignment.is_active,
            )
            for assignment in assignments
        ],
    )


def _serialize_member_list_item(member, categories: dict[int, object]) -> MemberListItem:
    return MemberListItem(
        id=member.id,
        member_code=member.member_code,
        full_name=member.full_name,
        plot_no=member.plot_no,
        plot_count=member.plot_count,
        cell_no=member.cell_no,
        category_id=member.category_id,
        category_name=categories[member.category_id].name if member.category_id in categories else None,
        joined_on=member.joined_on,
        is_active=member.is_active,
    )


@router.get("", response_model=list[MemberListItem])
def list_members(
    search: str | None = Query(default=None),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MemberListItem]:
    service = MemberService(db)
    categories = {category.id: category for category in CategoryRepository(db).list_categories()}
    return [_serialize_member_list_item(member, categories) for member in service.list_members(search)]


@router.get("/paged", response_model=MemberListPage)
def list_members_paged(
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    category_id: int | None = Query(default=None),
    has_phone: bool | None = Query(default=None),
    due_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MemberListPage:
    service = MemberService(db)
    categories = {category.id: category for category in CategoryRepository(db).list_categories()}
    total, items = service.paged_members(
        search=search,
        is_active=is_active,
        category_id=category_id,
        has_phone=has_phone,
        due_only=due_only,
        limit=limit,
        offset=offset,
    )
    return MemberListPage(
        items=[_serialize_member_list_item(member, categories) for member in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/search", response_model=list[MemberSearchItem])
def search_members(
    q: str = Query(min_length=2),
    limit: int = Query(default=20, ge=1, le=50),
    is_active: bool | None = Query(default=True),
    has_phone: bool | None = Query(default=None),
    due_only: bool = Query(default=False),
    category_id: int | None = Query(default=None),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MemberSearchItem]:
    service = MemberService(db)
    categories = {category.id: category for category in CategoryRepository(db).list_categories()}
    return [
        MemberSearchItem(
            id=member.id,
            member_code=member.member_code,
            full_name=member.full_name,
            plot_no=member.plot_no,
            plot_count=member.plot_count,
            cell_no=member.cell_no,
            category_name=categories[member.category_id].name if member.category_id in categories else None,
            is_active=member.is_active,
        )
        for member in service.search_members(
            query=q,
            limit=limit,
            is_active=is_active,
            has_phone=has_phone,
            due_only=due_only,
            category_id=category_id,
        )
    ]


@router.get("/{member_id}", response_model=MemberDetailRead)
def get_member(
    member_id: int,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MemberDetailRead:
    return _serialize_member_detail(member_id, db)


@router.post(
    "",
    response_model=MemberDetailRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("members:manage"))],
)
def create_member(
    payload: MemberCreate,
    db: Session = Depends(get_db),
) -> MemberDetailRead:
    service = MemberService(db)
    member = service.create_member(payload)
    return _serialize_member_detail(member.id, db)


@router.put(
    "/{member_id}",
    response_model=MemberDetailRead,
    dependencies=[Depends(require_permission("members:manage"))],
)
def update_member(
    member_id: int,
    payload: MemberUpdate,
    db: Session = Depends(get_db),
) -> MemberDetailRead:
    service = MemberService(db)
    member = service.update_member(member_id, payload)
    return _serialize_member_detail(member.id, db)


@router.post(
    "/{member_id}/packages",
    response_model=MemberDetailRead,
    dependencies=[Depends(require_permission("members:manage"))],
)
def assign_member_package(
    member_id: int,
    payload: MemberPackageAssignmentCreate,
    db: Session = Depends(get_db),
) -> MemberDetailRead:
    service = MemberService(db)
    service.assign_package(member_id, payload)
    db.commit()
    return _serialize_member_detail(member_id, db)
