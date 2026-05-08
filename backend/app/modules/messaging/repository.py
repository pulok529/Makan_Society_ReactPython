from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.billing.models import Charge
from app.modules.members.models import Member
from app.modules.messaging.models import SmsDeliveryAttempt, SmsMessage, SmsTemplate


class MessagingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_templates(self) -> list[SmsTemplate]:
        return list(self.db.scalars(select(SmsTemplate).order_by(SmsTemplate.name.asc())))

    def get_template(self, template_id: int) -> SmsTemplate | None:
        return self.db.get(SmsTemplate, template_id)

    def get_template_by_name(self, name: str) -> SmsTemplate | None:
        return self.db.scalar(select(SmsTemplate).where(SmsTemplate.name == name))

    def add_template(self, template: SmsTemplate) -> SmsTemplate:
        self.db.add(template)
        self.db.flush()
        self.db.refresh(template)
        return template

    def list_messages(self) -> list[SmsMessage]:
        statement = select(SmsMessage).order_by(SmsMessage.created_at.desc(), SmsMessage.id.desc())
        return list(self.db.scalars(statement))

    def get_message(self, message_id: int) -> SmsMessage | None:
        return self.db.get(SmsMessage, message_id)

    def add_message(self, message: SmsMessage) -> SmsMessage:
        self.db.add(message)
        self.db.flush()
        self.db.refresh(message)
        return message

    def list_attempts(self, message_id: int | None = None) -> list[SmsDeliveryAttempt]:
        statement = select(SmsDeliveryAttempt).order_by(
            SmsDeliveryAttempt.attempted_at.desc(),
            SmsDeliveryAttempt.id.desc(),
        )
        if message_id is not None:
            statement = statement.where(SmsDeliveryAttempt.sms_message_id == message_id)
        return list(self.db.scalars(statement))

    def add_attempt(self, attempt: SmsDeliveryAttempt) -> SmsDeliveryAttempt:
        self.db.add(attempt)
        self.db.flush()
        self.db.refresh(attempt)
        return attempt

    def get_member(self, member_id: int) -> Member | None:
        return self.db.get(Member, member_id)

    def list_members(self) -> list[Member]:
        return list(self.db.scalars(select(Member).order_by(Member.full_name.asc())))

    def count_templates(self) -> int:
        return int(self.db.scalar(select(func.count()).select_from(SmsTemplate)) or 0)

    def count_messages(self) -> int:
        return int(self.db.scalar(select(func.count()).select_from(SmsMessage)) or 0)

    def count_attempts(self) -> int:
        return int(self.db.scalar(select(func.count()).select_from(SmsDeliveryAttempt)) or 0)

    def count_sent_messages(self) -> int:
        statement = select(func.count()).select_from(SmsMessage).where(SmsMessage.status == "sent")
        return int(self.db.scalar(statement) or 0)

    def get_member_due_amount(self, member_id: int) -> float:
        statement = select(func.coalesce(func.sum(Charge.due_amount), 0)).where(Charge.member_id == member_id)
        return float(self.db.scalar(statement) or 0)
