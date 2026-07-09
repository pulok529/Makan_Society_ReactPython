from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BackgroundJob(Base):
    __tablename__ = "background_jobs"
    __table_args__ = {"schema": "system"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_type: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("auth.users.id"))
    payload_json: Mapped[str | None] = mapped_column(Text)
    result_summary: Mapped[str | None] = mapped_column(Text)
    result_path: Mapped[str | None] = mapped_column(String(500))
    output_filename: Mapped[str | None] = mapped_column(String(255))
    output_content_type: Mapped[str | None] = mapped_column(String(120))
    progress_current: Mapped[int] = mapped_column(Integer, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
