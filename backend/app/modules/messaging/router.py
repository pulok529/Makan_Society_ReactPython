from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.messaging.schemas import (
    BulkSmsBalanceRead,
    BulkSmsResultRead,
    SmsIntegrationStatusRead,
    SmsDeliveryAttemptPage,
    SmsBulkSendRequest,
    SmsDeliveryAttemptRead,
    SmsMessagePage,
    SmsManyRawRequest,
    SmsMessageRead,
    SmsProviderCheckRead,
    SmsProviderModeUpdate,
    SmsQueueRequest,
    SmsSendRequest,
    SmsTemplateCreate,
    SmsTemplateUpdate,
    SmsTemplateRead,
)
from app.modules.messaging.service import MessagingService

router = APIRouter(prefix="/messaging", tags=["messaging"])
sms_router = APIRouter(prefix="/sms", tags=["sms"])


@router.get("/status", response_model=SmsIntegrationStatusRead, dependencies=[Depends(require_permission("reports:view"))])
def integration_status(
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SmsIntegrationStatusRead:
    return MessagingService(db).integration_status()


@router.post("/provider-mode", response_model=SmsIntegrationStatusRead, dependencies=[Depends(require_permission("admin:manage"))])
def update_provider_mode(
    payload: SmsProviderModeUpdate,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SmsIntegrationStatusRead:
    return MessagingService(db).set_provider_mode(payload.provider_mode)


@router.get("/provider-check", response_model=SmsProviderCheckRead, dependencies=[Depends(require_permission("reports:view"))])
def check_provider_response(
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SmsProviderCheckRead:
    return MessagingService(db).check_provider_response()


@router.get("/templates", response_model=list[SmsTemplateRead], dependencies=[Depends(require_permission("reports:view"))])
def list_templates(
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SmsTemplateRead]:
    return MessagingService(db).list_templates()


@router.post(
    "/templates",
    response_model=SmsTemplateRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("admin:manage"))],
)
def create_template(
    payload: SmsTemplateCreate,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SmsTemplateRead:
    return MessagingService(db).create_template(payload)


@router.put(
    "/templates/{template_id}",
    response_model=SmsTemplateRead,
    dependencies=[Depends(require_permission("admin:manage"))],
)
def update_template(
    template_id: int,
    payload: SmsTemplateUpdate,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SmsTemplateRead:
    return MessagingService(db).update_template(template_id, payload)


@router.get("/messages", response_model=list[SmsMessageRead], dependencies=[Depends(require_permission("reports:view"))])
def list_messages(
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SmsMessageRead]:
    return MessagingService(db).list_messages()


@router.get("/messages/paged", response_model=SmsMessagePage, dependencies=[Depends(require_permission("reports:view"))])
def list_messages_paged(
    search: str | None = Query(default=None),
    member_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SmsMessagePage:
    return MessagingService(db).paged_messages(
        search=search,
        member_id=member_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/queue",
    response_model=SmsMessageRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("admin:manage"))],
)
def queue_message(
    payload: SmsQueueRequest,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SmsMessageRead:
    return MessagingService(db).queue_message(payload)


@router.post(
    "/messages/{message_id}/send",
    response_model=SmsMessageRead,
    dependencies=[Depends(require_permission("admin:manage"))],
)
def send_message_now(
    message_id: int,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SmsMessageRead:
    return MessagingService(db).send_now(message_id)


@router.get("/attempts", response_model=list[SmsDeliveryAttemptRead], dependencies=[Depends(require_permission("reports:view"))])
def list_attempts(
    message_id: int | None = None,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SmsDeliveryAttemptRead]:
    return MessagingService(db).list_attempts(message_id)


@router.get("/attempts/paged", response_model=SmsDeliveryAttemptPage, dependencies=[Depends(require_permission("reports:view"))])
def list_attempts_paged(
    message_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    provider_status: str | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SmsDeliveryAttemptPage:
    return MessagingService(db).paged_attempts(
        message_id=message_id,
        search=search,
        provider_status=provider_status,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )


@sms_router.post("/send", response_model=BulkSmsResultRead, dependencies=[Depends(require_permission("admin:manage"))])
def send_sms(
    payload: SmsSendRequest,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BulkSmsResultRead:
    return BulkSmsResultRead.model_validate(MessagingService(db).send_sms(payload).as_dict())


@sms_router.post("/send-bulk", response_model=BulkSmsResultRead, dependencies=[Depends(require_permission("admin:manage"))])
def send_bulk_sms(
    payload: SmsBulkSendRequest,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BulkSmsResultRead:
    return BulkSmsResultRead.model_validate(MessagingService(db).send_bulk_same_message(payload).as_dict())


@sms_router.post("/send-many-raw", response_model=BulkSmsResultRead, dependencies=[Depends(require_permission("admin:manage"))])
def send_many_raw_sms(
    payload: SmsManyRawRequest,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BulkSmsResultRead:
    return BulkSmsResultRead.model_validate(MessagingService(db).send_many_raw(payload.messages).as_dict())


@sms_router.get("/balance", response_model=BulkSmsBalanceRead, dependencies=[Depends(require_permission("reports:view"))])
def get_sms_balance(
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BulkSmsBalanceRead:
    return BulkSmsBalanceRead.model_validate(MessagingService(db).get_balance().as_dict())
