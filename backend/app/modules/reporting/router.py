from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.reporting.schemas import ReceiptDetailReport, ReportEnvelope, ReportFilter
from app.modules.reporting.service import ReportingService

router = APIRouter(prefix="/reports", tags=["reports"])


def _filters(
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    category_id: int | None = None,
    billing_period_id: int | None = None,
) -> ReportFilter:
    return ReportFilter(
        from_date=from_date,
        to_date=to_date,
        member_id=member_id,
        category_id=category_id,
        billing_period_id=billing_period_id,
    )


@router.get("/due-members", response_model=ReportEnvelope, dependencies=[Depends(require_permission("reports:view"))])
def due_members_report(
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    category_id: int | None = None,
    billing_period_id: int | None = None,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportEnvelope:
    return ReportingService(db).due_members(_filters(from_date, to_date, member_id, category_id, billing_period_id))


@router.get("/collections", response_model=ReportEnvelope, dependencies=[Depends(require_permission("reports:view"))])
def collections_report(
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportEnvelope:
    return ReportingService(db).collections(_filters(from_date, to_date, member_id))


@router.get("/charges", response_model=ReportEnvelope, dependencies=[Depends(require_permission("reports:view"))])
def charges_report(
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    billing_period_id: int | None = None,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportEnvelope:
    return ReportingService(db).charge_register(_filters(from_date, to_date, member_id, None, billing_period_id))


@router.get("/members", response_model=ReportEnvelope, dependencies=[Depends(require_permission("reports:view"))])
def members_report(
    member_id: int | None = None,
    category_id: int | None = None,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportEnvelope:
    return ReportingService(db).member_register(_filters(member_id=member_id, category_id=category_id))


@router.get("/receipt/{receipt_id}", response_model=ReceiptDetailReport, dependencies=[Depends(require_permission("reports:view"))])
def receipt_report(
    receipt_id: int,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReceiptDetailReport:
    return ReportingService(db).receipt_detail(receipt_id)


@router.get("/due-members/html", response_class=HTMLResponse, dependencies=[Depends(require_permission("reports:view"))])
def due_members_html(
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    category_id: int | None = None,
    billing_period_id: int | None = None,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ReportingService(db)
    report = service.due_members(_filters(from_date, to_date, member_id, category_id, billing_period_id))
    return HTMLResponse(service.render_html(report))


@router.get("/due-members/xlsx", dependencies=[Depends(require_permission("reports:view"))])
def due_members_xlsx(
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    category_id: int | None = None,
    billing_period_id: int | None = None,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    service = ReportingService(db)
    report = service.due_members(_filters(from_date, to_date, member_id, category_id, billing_period_id))
    payload = service.render_xlsx(report)
    headers = {"Content-Disposition": 'attachment; filename="due-members-report.xlsx"'}
    return Response(
        content=payload,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
