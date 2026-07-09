from datetime import date

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.auth.models import User
from app.modules.jobs.schemas import BackgroundJobRead, BulkSmsJobCreateRequest
from app.modules.jobs.service import JobService
from app.modules.reporting.schemas import ReportFilter

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/report-export", response_model=BackgroundJobRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("reports:view"))])
def create_report_export_job(
    report_type: str = Query(),
    kind: str = Query(pattern="^(html|xlsx|json)$"),
    receipt_id: int | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    member_id: int | None = Query(default=None),
    category_id: int | None = Query(default=None),
    billing_period_id: int | None = Query(default=None),
    plot_no: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BackgroundJobRead:
    filters = ReportFilter(
        from_date=from_date,
        to_date=to_date,
        member_id=member_id,
        category_id=category_id,
        billing_period_id=billing_period_id,
        plot_no=plot_no,
    )
    job = JobService(db).create_report_export_job(
        report_type=report_type,
        kind=kind,
        filters=filters,
        receipt_id=receipt_id,
        created_by=current_user.id,
    )
    return BackgroundJobRead.model_validate(job)


@router.post("/bulk-sms", response_model=BackgroundJobRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("admin:manage"))])
def create_bulk_sms_job(
    payload: BulkSmsJobCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BackgroundJobRead:
    job = JobService(db).create_bulk_sms_job(
        member_ids=payload.member_ids,
        template_id=payload.template_id,
        message_body=payload.message_body,
        created_by=current_user.id,
    )
    return BackgroundJobRead.model_validate(job)


@router.get("/{job_id}", response_model=BackgroundJobRead, dependencies=[Depends(require_permission("reports:view"))])
def get_job(
    job_id: int,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BackgroundJobRead:
    return BackgroundJobRead.model_validate(JobService(db).get_job(job_id))


@router.get("/{job_id}/download", dependencies=[Depends(require_permission("reports:view"))])
def download_job_output(
    job_id: int,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    return JobService(db).download_job_output(job_id)
