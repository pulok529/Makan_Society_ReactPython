from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Member(Base):
    __tablename__ = "members"
    __table_args__ = {"schema": "society"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    member_id_text: Mapped[str | None] = mapped_column(String(100))
    full_name: Mapped[str] = mapped_column(String(200), index=True)
    father_name: Mapped[str | None] = mapped_column(String(200))
    mother_name: Mapped[str | None] = mapped_column(String(200))
    present_address: Mapped[str | None] = mapped_column(String(500))
    permanent_address: Mapped[str | None] = mapped_column(String(500))
    cell_no: Mapped[str | None] = mapped_column(String(30), index=True)
    email: Mapped[str | None] = mapped_column(String(255))
    reference: Mapped[str | None] = mapped_column(String(255))
    national_id: Mapped[str | None] = mapped_column(String(100))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("society.member_categories.id"))
    member_class: Mapped[str | None] = mapped_column(String(100))
    joined_on: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MemberNominee(Base):
    __tablename__ = "member_nominees"
    __table_args__ = {"schema": "society"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("society.members.id", ondelete="CASCADE"))
    nominee_name: Mapped[str | None] = mapped_column(String(200))
    nominee_cell: Mapped[str | None] = mapped_column(String(30))


class MemberStatusHistory(Base):
    __tablename__ = "member_status_history"
    __table_args__ = {"schema": "society"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("society.members.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(50))
    reason: Mapped[str | None] = mapped_column(String(255))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MemberPackage(Base):
    __tablename__ = "member_packages"
    __table_args__ = {"schema": "society"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("society.members.id", ondelete="CASCADE"))
    package_id: Mapped[int] = mapped_column(ForeignKey("society.packages.id"))
    assigned_on: Mapped[date] = mapped_column(Date)
    ended_on: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
