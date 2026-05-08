from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReportProfile(Base):
    __tablename__ = "report_profiles"
    __table_args__ = {"schema": "reporting"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    header_text: Mapped[str | None] = mapped_column(String(255))
    address_text: Mapped[str | None] = mapped_column(String(255))
    phone_text: Mapped[str | None] = mapped_column(String(100))
    email_text: Mapped[str | None] = mapped_column(String(255))
    logo_file_id: Mapped[int | None] = mapped_column(ForeignKey("files.file_objects.id"))


class GeneratedReport(Base):
    __tablename__ = "generated_reports"
    __table_args__ = {"schema": "reporting"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    report_type: Mapped[str] = mapped_column(String(100))
    requested_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("auth.users.id"))
    file_object_id: Mapped[int | None] = mapped_column(ForeignKey("files.file_objects.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
