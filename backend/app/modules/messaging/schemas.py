from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SmsTemplateCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    body: str = Field(min_length=1)
    template_type: str | None = Field(default=None, max_length=50)


class SmsTemplateUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    body: str = Field(min_length=1)
    template_type: str | None = Field(default=None, max_length=50)


class SmsTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    body: str
    template_type: str | None


class SmsIntegrationStatusRead(BaseModel):
    provider_mode: str
    provider_name: str
    provider_configured: bool
    external_status_check_supported: bool
    provider_check_ok: bool | None = None
    provider_check_message: str | None = None
    template_count: int
    message_count: int
    sent_count: int
    attempt_count: int


class SmsProviderModeUpdate(BaseModel):
    provider_mode: str = Field(pattern="^(simulated|bulksmsbd|itsolutionbd)$")


class SmsProviderCheckRead(BaseModel):
    provider_name: str
    provider_configured: bool
    ok: bool
    status_code: int | None = None
    message: str
    response_sample: str | None = None


class SmsQueueRequest(BaseModel):
    member_id: int | None = None
    template_id: int | None = None
    recipient: str | None = None
    message_body: str | None = None
    variables: dict[str, str] = Field(default_factory=dict)
    send_now: bool = True


class SmsSendRequest(BaseModel):
    number: str = Field(min_length=10, max_length=30)
    message: str = Field(min_length=1, max_length=918)


class SmsBulkSendRequest(BaseModel):
    numbers: list[str] = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=918)


class SmsManyRawRequest(BaseModel):
    messages: str = Field(min_length=1, max_length=10000)


class BulkSmsResultRead(BaseModel):
    success: bool
    provider_code: str | None
    provider_message: str
    raw_response: str | dict
    recipients: list[str]
    dry_run: bool


class BulkSmsBalanceRead(BaseModel):
    success: bool
    provider_code: str | None
    provider_message: str
    raw_response: str | dict
    balance: str | None
    dry_run: bool


class SmsMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int | None
    member_name: str | None
    template_id: int | None
    template_name: str | None
    recipient: str
    message_body: str
    status: str
    created_at: datetime
    sent_at: datetime | None


class SmsDeliveryAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sms_message_id: int
    provider_name: str | None
    provider_message_id: str | None
    provider_status: str | None
    error_detail: str | None
    attempted_at: datetime
