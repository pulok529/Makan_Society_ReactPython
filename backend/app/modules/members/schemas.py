from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MemberPackageAssignmentCreate(BaseModel):
    package_id: int
    assigned_on: date
    ended_on: date | None = None
    is_active: bool = True


class MemberNomineePayload(BaseModel):
    nominee_name: str | None = None
    nominee_cell: str | None = None


class MemberCreate(BaseModel):
    member_code: str
    member_id_text: str | None = None
    full_name: str
    father_name: str | None = None
    mother_name: str | None = None
    present_address: str | None = None
    permanent_address: str | None = None
    cell_no: str | None = None
    email: str | None = None
    reference: str | None = None
    national_id: str | None = None
    category_id: int | None = None
    member_class: str | None = None
    joined_on: date | None = None
    is_active: bool = True
    nominee: MemberNomineePayload | None = None
    initial_package: MemberPackageAssignmentCreate | None = None


class MemberUpdate(BaseModel):
    member_code: str
    member_id_text: str | None = None
    full_name: str
    father_name: str | None = None
    mother_name: str | None = None
    present_address: str | None = None
    permanent_address: str | None = None
    cell_no: str | None = None
    email: str | None = None
    reference: str | None = None
    national_id: str | None = None
    category_id: int | None = None
    member_class: str | None = None
    joined_on: date | None = None
    is_active: bool = True
    nominee: MemberNomineePayload | None = None


class MemberPackageAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    package_id: int
    package_name: str
    assigned_on: date
    ended_on: date | None
    is_active: bool


class MemberDetailRead(BaseModel):
    id: int
    member_code: str
    member_id_text: str | None
    full_name: str
    father_name: str | None
    mother_name: str | None
    present_address: str | None
    permanent_address: str | None
    cell_no: str | None
    email: str | None
    reference: str | None
    national_id: str | None
    category_id: int | None
    category_name: str | None
    member_class: str | None
    joined_on: date | None
    is_active: bool
    created_at: datetime
    nominee_name: str | None
    nominee_cell: str | None
    packages: list[MemberPackageAssignmentRead]


class MemberListItem(BaseModel):
    id: int
    member_code: str
    full_name: str
    cell_no: str | None
    category_id: int | None
    category_name: str | None
    joined_on: date | None
    is_active: bool
    active_package_name: str | None
