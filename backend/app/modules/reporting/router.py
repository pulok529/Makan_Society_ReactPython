from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.accounting.service import AccountingService
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.reporting.schemas import ReceiptDetailReport, ReportEnvelope, ReportFilter, SingleMemberStatementReport
from app.modules.reporting.service import ReportingService

router = APIRouter(prefix="/reports", tags=["reports"])


def _filters(
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    category_id: int | None = None,
    billing_period_id: int | None = None,
    plot_no: str | None = None,
) -> ReportFilter:
    return ReportFilter(
        from_date=from_date,
        to_date=to_date,
        member_id=member_id,
        category_id=category_id,
        billing_period_id=billing_period_id,
        plot_no=plot_no,
    )


def _build_report(report_key: str, service: ReportingService, filters: ReportFilter) -> ReportEnvelope:
    builders = {
        "due-members": service.due_members,
        "collections": service.collections,
        "charges": service.charge_register,
        "members": service.member_register,
        "total-collection": service.total_collection,
        "total-due": service.total_due,
    }
    builder = builders.get(report_key)
    if builder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unsupported report type")
    return builder(filters)


@router.get("/due-members", response_model=ReportEnvelope, dependencies=[Depends(require_permission("reports:view"))])
def due_members_report(
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    category_id: int | None = None,
    billing_period_id: int | None = None,
    plot_no: str | None = Query(default=None),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportEnvelope:
    return ReportingService(db).due_members(_filters(from_date, to_date, member_id, category_id, billing_period_id, plot_no))


@router.get("/collections", response_model=ReportEnvelope, dependencies=[Depends(require_permission("reports:view"))])
def collections_report(
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    category_id: int | None = None,
    plot_no: str | None = Query(default=None),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportEnvelope:
    return ReportingService(db).collections(_filters(from_date, to_date, member_id, category_id, None, plot_no))


@router.get("/total-collection", response_model=ReportEnvelope, dependencies=[Depends(require_permission("reports:view"))])
def total_collection_report(
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    category_id: int | None = None,
    plot_no: str | None = Query(default=None),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportEnvelope:
    return ReportingService(db).total_collection(_filters(from_date, to_date, member_id, category_id, None, plot_no))


@router.get("/total-due", response_model=ReportEnvelope, dependencies=[Depends(require_permission("reports:view"))])
def total_due_report(
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    category_id: int | None = None,
    billing_period_id: int | None = None,
    plot_no: str | None = Query(default=None),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportEnvelope:
    return ReportingService(db).total_due(_filters(from_date, to_date, member_id, category_id, billing_period_id, plot_no))


@router.get("/charges", response_model=ReportEnvelope, dependencies=[Depends(require_permission("reports:view"))])
def charges_report(
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    category_id: int | None = None,
    billing_period_id: int | None = None,
    plot_no: str | None = Query(default=None),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportEnvelope:
    return ReportingService(db).charge_register(_filters(from_date, to_date, member_id, category_id, billing_period_id, plot_no))


@router.get("/members", response_model=ReportEnvelope, dependencies=[Depends(require_permission("reports:view"))])
def members_report(
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    category_id: int | None = None,
    billing_period_id: int | None = None,
    plot_no: str | None = Query(default=None),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportEnvelope:
    return ReportingService(db).member_register(_filters(from_date, to_date, member_id, category_id, billing_period_id, plot_no))


@router.get("/member-statement", response_model=SingleMemberStatementReport, dependencies=[Depends(require_permission("reports:view"))])
def member_statement_report(
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SingleMemberStatementReport:
    return ReportingService(db).single_member_statement(_filters(from_date, to_date, member_id))


@router.get("/receipt/{receipt_id}", response_model=ReceiptDetailReport, dependencies=[Depends(require_permission("reports:view"))])
def receipt_report(
    receipt_id: int,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReceiptDetailReport:
    return ReportingService(db).receipt_detail(receipt_id)


@router.get("/member-statement/xlsx", dependencies=[Depends(require_permission("reports:view"))])
def member_statement_xlsx(
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    service = ReportingService(db)
    report = service.single_member_statement(_filters(from_date, to_date, member_id))
    payload = service.render_member_statement_xlsx(report)
    headers = {"Content-Disposition": 'attachment; filename="member-statement-report.xlsx"'}
    return Response(
        content=payload,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/receipt/{receipt_id}/xlsx", dependencies=[Depends(require_permission("reports:view"))])
def receipt_report_xlsx(
    receipt_id: int,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    service = ReportingService(db)
    report = service.receipt_detail(receipt_id)
    payload = service.render_receipt_xlsx(report)
    headers = {"Content-Disposition": f'attachment; filename="receipt-{receipt_id}-report.xlsx"'}
    return Response(
        content=payload,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/income-expense/xlsx", dependencies=[Depends(require_permission("reports:view"))])
def income_expense_xlsx(
    from_date=None,
    to_date=None,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    reporting_service = ReportingService(db)
    report = AccountingService(db).income_expense_report(from_date=from_date, to_date=to_date)
    payload = reporting_service.render_income_expense_xlsx(report)
    headers = {"Content-Disposition": 'attachment; filename="income-expense-report.xlsx"'}
    return Response(
        content=payload,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/{report_key}/html", response_class=HTMLResponse, dependencies=[Depends(require_permission("reports:view"))])
def report_html(
    report_key: str,
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    category_id: int | None = None,
    billing_period_id: int | None = None,
    plot_no: str | None = Query(default=None),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ReportingService(db)
    report = _build_report(report_key, service, _filters(from_date, to_date, member_id, category_id, billing_period_id, plot_no))
    return HTMLResponse(service.render_html(report))


@router.get("/{report_key}/xlsx", dependencies=[Depends(require_permission("reports:view"))])
def report_xlsx(
    report_key: str,
    from_date=None,
    to_date=None,
    member_id: int | None = None,
    category_id: int | None = None,
    billing_period_id: int | None = None,
    plot_no: str | None = Query(default=None),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    service = ReportingService(db)
    report = _build_report(report_key, service, _filters(from_date, to_date, member_id, category_id, billing_period_id, plot_no))
    payload = service.render_xlsx(report)
    headers = {"Content-Disposition": f'attachment; filename="{report_key}-report.xlsx"'}
    return Response(
        content=payload,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
