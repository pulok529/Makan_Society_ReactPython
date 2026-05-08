from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.messaging.bulksmsbd import (
    BulkSmsBalanceResult,
    BulkSmsBdClient,
    BulkSmsResult,
    normalize_bd_phone,
)
from app.modules.messaging.models import SmsDeliveryAttempt, SmsMessage, SmsTemplate
from app.modules.messaging.repository import MessagingRepository
from app.modules.messaging.schemas import (
    SmsIntegrationStatusRead,
    SmsBulkSendRequest,
    SmsDeliveryAttemptRead,
    SmsMessageRead,
    SmsProviderCheckRead,
    SmsQueueRequest,
    SmsSendRequest,
    SmsTemplateCreate,
    SmsTemplateUpdate,
    SmsTemplateRead,
)


class MessagingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = MessagingRepository(db)

    def list_templates(self) -> list[SmsTemplateRead]:
        return [SmsTemplateRead.model_validate(item) for item in self.repository.list_templates()]

    def integration_status(self) -> SmsIntegrationStatusRead:
        provider_mode = settings.sms_provider_mode.strip().lower()
        provider_check = self.check_provider_response()
        return SmsIntegrationStatusRead(
            provider_mode=provider_mode,
            provider_name="BulkSMSBD" if provider_mode == "bulksmsbd" else "local-simulated-provider",
            provider_configured=self._provider_configured(),
            external_status_check_supported=True,
            provider_check_ok=provider_check.ok,
            provider_check_message=provider_check.message,
            template_count=self.repository.count_templates(),
            message_count=self.repository.count_messages(),
            sent_count=self.repository.count_sent_messages(),
            attempt_count=self.repository.count_attempts(),
        )

    def set_provider_mode(self, provider_mode: str) -> SmsIntegrationStatusRead:
        next_mode = provider_mode.strip().lower()
        if next_mode == "itsolutionbd":
            next_mode = "bulksmsbd"
        if next_mode not in {"simulated", "bulksmsbd"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid SMS provider mode")
        if next_mode == "bulksmsbd" and not self._provider_configured():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Real SMS gateway is not configured")
        settings.sms_provider_mode = next_mode
        return self.integration_status()

    def check_provider_response(self) -> SmsProviderCheckRead:
        result = self.get_balance()
        return SmsProviderCheckRead(
            provider_name="BulkSMSBD",
            provider_configured=self._provider_configured(),
            ok=result.success,
            status_code=None,
            message=result.provider_message,
            response_sample=str(result.raw_response)[:300] if result.raw_response else None,
        )

    def create_template(self, payload: SmsTemplateCreate) -> SmsTemplateRead:
        if self.repository.get_template_by_name(payload.name.strip()) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Template name already exists")

        template = SmsTemplate(
            name=payload.name.strip(),
            body=payload.body.strip(),
            template_type=payload.template_type.strip() if payload.template_type else None,
        )
        self.repository.add_template(template)
        self.db.commit()
        return SmsTemplateRead.model_validate(template)

    def update_template(self, template_id: int, payload: SmsTemplateUpdate) -> SmsTemplateRead:
        template = self.repository.get_template(template_id)
        if template is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        existing = self.repository.get_template_by_name(payload.name.strip())
        if existing is not None and existing.id != template_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Template name already exists")
        template.name = payload.name.strip()
        template.body = payload.body.strip()
        template.template_type = payload.template_type.strip() if payload.template_type else None
        self.db.commit()
        return SmsTemplateRead.model_validate(template)

    def list_messages(self) -> list[SmsMessageRead]:
        templates = {item.id: item for item in self.repository.list_templates()}
        members = {item.id: item for item in self.repository.list_members()}
        return [
            SmsMessageRead(
                id=item.id,
                member_id=item.member_id,
                member_name=members[item.member_id].full_name if item.member_id in members else None,
                template_id=item.template_id,
                template_name=templates[item.template_id].name if item.template_id in templates else None,
                recipient=item.recipient,
                message_body=item.message_body,
                status=item.status,
                created_at=item.created_at,
                sent_at=item.sent_at,
            )
            for item in self.repository.list_messages()
        ]

    def list_attempts(self, message_id: int | None = None) -> list[SmsDeliveryAttemptRead]:
        return [SmsDeliveryAttemptRead.model_validate(item) for item in self.repository.list_attempts(message_id)]

    def queue_message(self, payload: SmsQueueRequest) -> SmsMessageRead:
        member = None
        if payload.member_id is not None:
            member = self.repository.get_member(payload.member_id)
            if member is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        recipient = (payload.recipient or "").strip()
        if not recipient and member is not None:
            recipient = (member.cell_no or "").strip()
        if not recipient:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recipient is required")

        template = None
        body = (payload.message_body or "").strip()
        variables = self._build_variables(member)
        variables.update({key: str(value) for key, value in payload.variables.items()})
        if payload.template_id is not None:
            template = self.repository.get_template(payload.template_id)
            if template is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
            body = self._render_template(template.body, variables)
        elif body:
            body = self._render_template(body, variables)

        if not body:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message body is required")

        message = SmsMessage(
            member_id=member.id if member is not None else None,
            template_id=template.id if template is not None else None,
            recipient=recipient,
            message_body=body,
            status="queued",
            sent_at=None,
        )
        self.repository.add_message(message)

        if payload.send_now:
            self._send_message(message)

        self.db.commit()
        return self._serialize_message(message.id)

    def send_now(self, message_id: int) -> SmsMessageRead:
        message = self.repository.get_message(message_id)
        if message is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMS message not found")
        self._send_message(message)
        self.db.commit()
        return self._serialize_message(message.id)

    def _send_message(self, message: SmsMessage) -> None:
        if settings.sms_provider_mode.strip().lower() == "bulksmsbd":
            self._send_via_bulksmsbd(message)
            return
        self._simulate_send(message)

    def send_sms(self, payload: SmsSendRequest) -> BulkSmsResult:
        try:
            normalized = normalize_bd_phone(payload.number)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        message = SmsMessage(
            member_id=None,
            template_id=None,
            recipient=normalized,
            message_body=payload.message.strip(),
            status="queued",
            sent_at=None,
        )
        self.repository.add_message(message)
        result = self._send_with_bulksmsbd([normalized], payload.message, message)
        self.db.commit()
        return result

    def send_bulk_same_message(self, payload: SmsBulkSendRequest) -> BulkSmsResult:
        try:
            recipients = [normalize_bd_phone(number) for number in payload.numbers]
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        if len(recipients) > 100:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 100 recipients are allowed")

        messages = [
            SmsMessage(
                member_id=None,
                template_id=None,
                recipient=recipient,
                message_body=payload.message.strip(),
                status="queued",
                sent_at=None,
            )
            for recipient in recipients
        ]
        for message in messages:
            self.repository.add_message(message)
        result = self._send_with_bulksmsbd(recipients, payload.message, *messages)
        self.db.commit()
        return result

    def send_many_raw(self, messages: str) -> BulkSmsResult:
        result = self._bulksmsbd_client().send_many_raw(messages)
        self.repository.add_attempt(
            SmsDeliveryAttempt(
                sms_message_id=self._create_system_message(messages).id,
                provider_name="BulkSMSBD",
                provider_message_id=result.provider_code,
                provider_status="accepted" if result.success else "failed",
                error_detail=str(result.raw_response)[:1000] if result.raw_response else result.provider_message,
            )
        )
        self.db.commit()
        return result

    def get_balance(self) -> BulkSmsBalanceResult:
        return self._bulksmsbd_client().get_balance()

    def _simulate_send(self, message: SmsMessage) -> None:
        provider_message_id = f"SIM-{uuid4().hex[:10].upper()}"
        message.status = "simulated"
        message.sent_at = datetime.now(UTC)
        self.repository.add_attempt(
            SmsDeliveryAttempt(
                sms_message_id=message.id,
                provider_name="local-simulated-provider",
                provider_message_id=provider_message_id,
                provider_status="simulated",
                error_detail=None,
            )
        )

    def _send_via_bulksmsbd(self, message: SmsMessage) -> None:
        result = self._send_with_bulksmsbd([message.recipient], message.message_body, message)
        if not result.success:
            return

    def _send_with_bulksmsbd(self, recipients: list[str], message_body: str, *messages: SmsMessage) -> BulkSmsResult:
        try:
            result = self._bulksmsbd_client().send_bulk_same_message(recipients, message_body)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        now = datetime.now(UTC)
        for message in messages:
            message.status = "dry_run" if result.dry_run else "sent" if result.success else "failed"
            message.sent_at = now if result.success else None
            self.repository.add_attempt(
                SmsDeliveryAttempt(
                    sms_message_id=message.id,
                    provider_name="BulkSMSBD",
                    provider_message_id=result.provider_code,
                    provider_status="dry_run" if result.dry_run else "accepted" if result.success else "failed",
                    error_detail=str(result.raw_response)[:1000] if result.raw_response else result.provider_message,
                )
            )
        return result

    def _create_system_message(self, message_body: str) -> SmsMessage:
        message = SmsMessage(
            member_id=None,
            template_id=None,
            recipient="bulk-many-raw",
            message_body=message_body[:918],
            status="sent",
            sent_at=datetime.now(UTC),
        )
        return self.repository.add_message(message)

    @staticmethod
    def _bulksmsbd_client() -> BulkSmsBdClient:
        return BulkSmsBdClient(
            api_key=settings.bulksmsbd_api_key,
            sender_id=settings.bulksmsbd_sender_id,
            base_url=settings.bulksmsbd_base_url,
            timeout=settings.bulksmsbd_timeout_seconds,
            enabled=settings.bulksmsbd_enabled,
            dry_run=settings.bulksmsbd_dry_run,
        )

    def _serialize_message(self, message_id: int) -> SmsMessageRead:
        message = self.repository.get_message(message_id)
        if message is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMS message not found")
        templates = {item.id: item for item in self.repository.list_templates()}
        members = {item.id: item for item in self.repository.list_members()}
        return SmsMessageRead(
            id=message.id,
            member_id=message.member_id,
            member_name=members[message.member_id].full_name if message.member_id in members else None,
            template_id=message.template_id,
            template_name=templates[message.template_id].name if message.template_id in templates else None,
            recipient=message.recipient,
            message_body=message.message_body,
            status=message.status,
            created_at=message.created_at,
            sent_at=message.sent_at,
        )

    @staticmethod
    def _render_template(source: str, variables: dict[str, str]) -> str:
        rendered = source
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", value)
            rendered = rendered.replace(f"({key})", value)
        return rendered

    def _build_variables(self, member) -> dict[str, str]:
        if member is None:
            return {}
        due_amount = self.repository.get_member_due_amount(member.id)
        return {
            "name": member.full_name or "",
            "bill": f"{due_amount:.2f}",
            "due": f"{due_amount:.2f}",
            "member_code": member.member_code or "",
            "phone": member.cell_no or "",
        }

    @staticmethod
    def _provider_configured() -> bool:
        return bool(settings.bulksmsbd_api_key and settings.bulksmsbd_sender_id)
