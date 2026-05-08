from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SmsTemplate(Base):
    __tablename__ = "sms_templates"
    __table_args__ = {"schema": "messaging"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    body: Mapped[str] = mapped_column(Text)
    template_type: Mapped[str | None] = mapped_column(String(50))


class SmsMessage(Base):
    __tablename__ = "sms_messages"
    __table_args__ = {"schema": "messaging"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_id: Mapped[int | None] = mapped_column(ForeignKey("society.members.id"))
    template_id: Mapped[int | None] = mapped_column(ForeignKey("messaging.sms_templates.id"))
    recipient: Mapped[str] = mapped_column(String(30))
    message_body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="queued")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SmsDeliveryAttempt(Base):
    __tablename__ = "sms_delivery_attempts"
    __table_args__ = {"schema": "messaging"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sms_message_id: Mapped[int] = mapped_column(
        ForeignKey("messaging.sms_messages.id", ondelete="CASCADE")
    )
    provider_name: Mapped[str | None] = mapped_column(String(100))
    provider_message_id: Mapped[str | None] = mapped_column(String(255))
    provider_status: Mapped[str | None] = mapped_column(String(100))
    error_detail: Mapped[str | None] = mapped_column(Text)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
