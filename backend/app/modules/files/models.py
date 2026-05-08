from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FileObject(Base):
    __tablename__ = "file_objects"
    __table_args__ = {"schema": "files"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    storage_key: Mapped[str] = mapped_column(String(255), unique=True)
    original_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(100))
    file_size: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FileLink(Base):
    __tablename__ = "file_links"
    __table_args__ = {"schema": "files"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_object_id: Mapped[int] = mapped_column(ForeignKey("files.file_objects.id", ondelete="CASCADE"))
    linked_entity: Mapped[str] = mapped_column(String(100))
    linked_entity_id: Mapped[int]
    purpose: Mapped[str | None] = mapped_column(String(100))
