from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BackgroundJobCreate(BaseModel):
    job_type: str = Field(min_length=2, max_length=80)
    payload_json: str | None = None


class BackgroundJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_type: str
    status: str
    created_by: int | None
    payload_json: str | None
    result_summary: str | None
    result_path: str | None
    output_filename: str | None
    output_content_type: str | None
    progress_current: int
    progress_total: int
    created_at: datetime
    updated_at: datetime


class BulkSmsJobCreateRequest(BaseModel):
    member_ids: list[int] = Field(min_length=1, max_length=5000)
    template_id: int | None = None
    message_body: str | None = None

    @model_validator(mode="after")
    def validate_body_or_template(self) -> "BulkSmsJobCreateRequest":
        if self.template_id is None and not (self.message_body or "").strip():
            raise ValueError("Message body is required when no template is selected")
        return self
