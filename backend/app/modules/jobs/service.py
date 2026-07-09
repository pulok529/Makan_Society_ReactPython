from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.modules.accounting.service import AccountingService
from app.modules.jobs.models import BackgroundJob
from app.modules.jobs.repository import JobRepository
from app.modules.jobs.schemas import BackgroundJobCreate
from app.modules.jobs.types import BulkSmsJobPayload, ReportExportJobPayload
from app.modules.messaging.schemas import SmsQueueRequest
from app.modules.messaging.service import MessagingService
from app.modules.reporting.schemas import ReportFilter
from app.modules.reporting.service import ReportingService


EXPORT_DIR = Path("app/storage/exports")


class JobService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = JobRepository(db)

    def create_job(self, payload: BackgroundJobCreate, created_by: int | None = None) -> BackgroundJob:
        job = BackgroundJob(
            job_type=payload.job_type.strip(),
            status="pending",
            created_by=created_by,
            payload_json=payload.payload_json,
            result_summary="Queued for worker processing.",
            progress_current=0,
            progress_total=0,
        )
        self.repository.add_job(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def create_report_export_job(
        self,
        *,
        report_type: str,
        kind: str,
        filters: ReportFilter,
        receipt_id: int | None = None,
        created_by: int | None = None,
    ) -> BackgroundJob:
        payload = ReportExportJobPayload(kind=kind, report_type=report_type, filters=filters, receipt_id=receipt_id)
        return self.create_job(
            BackgroundJobCreate(job_type="report_export", payload_json=payload.model_dump_json()),
            created_by=created_by,
        )

    def create_bulk_sms_job(
        self,
        *,
        member_ids: list[int],
        template_id: int | None,
        message_body: str | None,
        created_by: int | None = None,
    ) -> BackgroundJob:
        payload = BulkSmsJobPayload(member_ids=member_ids, template_id=template_id, message_body=message_body)
        return self.create_job(
            BackgroundJobCreate(job_type="bulk_sms", payload_json=payload.model_dump_json()),
            created_by=created_by,
        )

    def get_job(self, job_id: int) -> BackgroundJob:
        job = self.repository.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background job not found")
        return job

    def download_job_output(self, job_id: int) -> FileResponse:
        job = self.get_job(job_id)
        if job.status != "completed" or not job.result_path:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job output is not ready")
        path = Path(job.result_path)
        if not path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job output file not found")
        return FileResponse(path, media_type=job.output_content_type or "application/octet-stream", filename=job.output_filename or path.name)

    def process_next_pending_job(self) -> bool:
        job = self.repository.get_next_pending_job()
        if job is None:
            return False
        job.status = "running"
        job.result_summary = "Worker picked up the job."
        self.db.commit()
        self.db.refresh(job)
        try:
            if job.job_type == "report_export":
                self._process_report_export(job)
            elif job.job_type == "bulk_sms":
                self._process_bulk_sms(job)
            else:
                raise ValueError(f"Unsupported job type: {job.job_type}")
            job.status = "completed"
            if not job.result_summary:
                job.result_summary = "Job completed successfully."
        except Exception as exc:  # noqa: BLE001
            job.status = "failed"
            job.result_summary = str(exc)
        self.db.commit()
        return True

    def _process_report_export(self, job: BackgroundJob) -> None:
        if not job.payload_json:
            raise ValueError("Missing report export payload")
        payload = ReportExportJobPayload.model_validate_json(job.payload_json)
        reporting = ReportingService(self.db)
        accounting = AccountingService(self.db)

        report_filename = f"{payload.report_type}-{uuid4().hex[:10]}"
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)

        if payload.report_type == "income-expense":
            report = accounting.income_expense_report(from_date=payload.filters.from_date, to_date=payload.filters.to_date)
            if payload.kind == "xlsx":
                content = reporting.render_income_expense_xlsx(report)
                suffix = ".xlsx"
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif payload.kind == "html":
                content = reporting.render_json_html("Income Expense Report", report.model_dump(mode="json")).encode("utf-8")
                suffix = ".html"
                content_type = "text/html; charset=utf-8"
            else:
                content = json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2).encode("utf-8")
                suffix = ".json"
                content_type = "application/json"
        elif payload.report_type == "receipt-detail":
            if payload.receipt_id is None:
                raise ValueError("Receipt report requires a receipt id")
            report = reporting.receipt_detail(payload.receipt_id)
            if payload.kind == "xlsx":
                content = reporting.render_receipt_xlsx(report)
                suffix = ".xlsx"
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif payload.kind == "html":
                content = reporting.render_json_html(f"Receipt {report.receipt_no}", report.model_dump(mode="json")).encode("utf-8")
                suffix = ".html"
                content_type = "text/html; charset=utf-8"
            else:
                content = json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2).encode("utf-8")
                suffix = ".json"
                content_type = "application/json"
        elif payload.report_type == "member-statement":
            if payload.filters.member_id is None:
                raise ValueError("Member statement requires a member id")
            report = reporting.single_member_statement(payload.filters)
            if payload.kind == "xlsx":
                content = reporting.render_member_statement_xlsx(report)
                suffix = ".xlsx"
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif payload.kind == "html":
                content = reporting.render_json_html(f"Member Statement {report.member_code}", report.model_dump(mode="json")).encode("utf-8")
                suffix = ".html"
                content_type = "text/html; charset=utf-8"
            else:
                content = json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2).encode("utf-8")
                suffix = ".json"
                content_type = "application/json"
        elif payload.report_type == "member-information-detail":
            if payload.filters.member_id is None:
                raise ValueError("Member information detail requires a member id")
            report = reporting.member_information_detail(payload.filters)
            if payload.kind == "xlsx":
                content = reporting.render_member_information_detail_xlsx(report)
                suffix = ".xlsx"
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif payload.kind == "html":
                content = reporting.render_json_html(f"Member Detail {report.member_info.member_code}", report.model_dump(mode="json")).encode("utf-8")
                suffix = ".html"
                content_type = "text/html; charset=utf-8"
            else:
                content = json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2).encode("utf-8")
                suffix = ".json"
                content_type = "application/json"
        else:
            path_map = {
                "due-members": reporting.due_members,
                "collections": reporting.collections,
                "income-detail": reporting.income_detail,
                "expense-detail": reporting.expense_detail,
                "total-collection": reporting.total_collection,
                "total-due": reporting.total_due,
                "charges": reporting.charge_register,
                "members": reporting.member_register,
            }
            builder = path_map.get(payload.report_type)
            if builder is None:
                raise ValueError("Unsupported report type")
            report = builder(payload.filters)
            if payload.kind == "html":
                content = reporting.render_html(report).encode("utf-8")
                suffix = ".html"
                content_type = "text/html; charset=utf-8"
            elif payload.kind == "xlsx":
                content = reporting.render_xlsx(report)
                suffix = ".xlsx"
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                content = json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2).encode("utf-8")
                suffix = ".json"
                content_type = "application/json"

        output_path = EXPORT_DIR / f"{report_filename}{suffix}"
        output_path.write_bytes(content)
        job.result_path = str(output_path)
        job.output_filename = output_path.name
        job.output_content_type = content_type
        job.progress_current = 1
        job.progress_total = 1
        job.result_summary = f"Export ready: {output_path.name}"

    def _process_bulk_sms(self, job: BackgroundJob) -> None:
        if not job.payload_json:
            raise ValueError("Missing bulk SMS payload")
        payload = BulkSmsJobPayload.model_validate_json(job.payload_json)
        messaging = MessagingService(self.db)
        job.progress_total = len(payload.member_ids)
        job.progress_current = 0
        self.db.commit()

        success = 0
        failed = 0
        results: list[dict[str, object]] = []
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        for index, member_id in enumerate(payload.member_ids, start=1):
            member = messaging.repository.get_member(member_id)
            if member is None:
                failed += 1
                results.append({
                    "member_id": member_id,
                    "status": "failed",
                    "reason": "Member not found",
                })
                job.progress_current = index
                self.db.commit()
                continue
            try:
                messaging.queue_message(
                    SmsQueueRequest(
                        member_id=member_id,
                        template_id=payload.template_id,
                        recipient=member.cell_no,
                        message_body=payload.message_body,
                        variables={},
                        send_now=True,
                    )
                )
                success += 1
                results.append({
                    "member_id": member_id,
                    "member_code": member.member_code,
                    "member_name": member.full_name,
                    "recipient": member.cell_no,
                    "status": "sent",
                })
            except Exception as exc:  # noqa: BLE001
                failed += 1
                results.append({
                    "member_id": member_id,
                    "member_code": member.member_code,
                    "member_name": member.full_name,
                    "recipient": member.cell_no,
                    "status": "failed",
                    "reason": str(exc),
                })
            job.progress_current = index
            job.result_summary = f"Processed {index}/{len(payload.member_ids)} recipients. Success={success}, Failed={failed}"
            self.db.commit()
        output_path = EXPORT_DIR / f"bulk-sms-{uuid4().hex[:10]}.json"
        output_path.write_text(
            json.dumps(
                {
                    "job_id": job.id,
                    "success_count": success,
                    "failed_count": failed,
                    "results": results,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        job.result_path = str(output_path)
        job.output_filename = output_path.name
        job.output_content_type = "application/json"
        job.result_summary = f"Bulk SMS completed. Success={success}, Failed={failed}"
