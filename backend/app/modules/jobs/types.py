from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.modules.reporting.schemas import ReportFilter


class ReportExportJobPayload(BaseModel):
    kind: Literal["html", "xlsx", "json", "pdf"]
    report_type: str
    filters: ReportFilter = Field(default_factory=ReportFilter)
    receipt_id: int | None = None


class BulkSmsJobPayload(BaseModel):
    member_ids: list[int] = Field(min_length=1)
    template_id: int | None = None
    message_body: str | None = None
