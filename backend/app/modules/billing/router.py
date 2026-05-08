from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.auth.models import User
from app.modules.billing.schemas import (
    BillingDashboardRead,
    BillingDueLineRead,
    BillingGenerationRequest,
    BillingHeadCreate,
    BillingHeadMappingCreate,
    BillingHeadMappingRead,
    BillingHeadRead,
    BillingInvoiceCancel,
    BillingInvoiceCreate,
    BillingInvoiceRead,
    BillingReportRead,
    BillingMemberSummary,
    BillingPeriodCreate,
    BillingPeriodRead,
    ChargeRead,
    ReceiptCreate,
    ReceiptRead,
)
from app.modules.billing.service import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/dashboard", response_model=BillingDashboardRead)
def get_billing_dashboard(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BillingDashboardRead:
    return BillingService(db).dashboard()


@router.get("/member-due-summary", response_model=list[BillingMemberSummary])
def list_member_due_summary(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BillingMemberSummary]:
    return BillingService(db).member_due_summaries()


@router.get("/periods", response_model=list[BillingPeriodRead])
def list_periods(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BillingPeriodRead]:
    periods = BillingService(db).list_periods()
    return [BillingPeriodRead.model_validate(period) for period in periods]


@router.post(
    "/periods",
    response_model=BillingPeriodRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("billing:manage"))],
)
def create_period(
    payload: BillingPeriodCreate,
    db: Session = Depends(get_db),
) -> BillingPeriodRead:
    period = BillingService(db).create_period(payload)
    return BillingPeriodRead.model_validate(period)


@router.post(
    "/generate",
    response_model=list[ChargeRead],
    dependencies=[Depends(require_permission("billing:manage"))],
)
def generate_period_charges(
    payload: BillingGenerationRequest,
    db: Session = Depends(get_db),
) -> list[ChargeRead]:
    service = BillingService(db)
    generated = service.generate_period_charges(payload)
    generated_ids = {charge.id for charge in generated}
    return [charge for charge in service.list_charges(billing_period_id=payload.billing_period_id) if charge.id in generated_ids]


@router.get("/charges", response_model=list[ChargeRead])
def list_charges(
    billing_period_id: int | None = Query(default=None),
    member_id: int | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChargeRead]:
    return BillingService(db).list_charges(billing_period_id=billing_period_id, member_id=member_id)


@router.get("/receipts", response_model=list[ReceiptRead])
def list_receipts(
    member_id: int | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ReceiptRead]:
    return BillingService(db).list_receipts(member_id=member_id)


@router.post(
    "/receipts",
    response_model=ReceiptRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("billing:manage"))],
)
def create_receipt(
    payload: ReceiptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReceiptRead:
    return BillingService(db).create_receipt(payload, current_user)


@router.get("/heads", response_model=list[BillingHeadRead])
def list_billing_heads(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BillingHeadRead]:
    return BillingService(db).list_billing_heads()


@router.post(
    "/heads",
    response_model=BillingHeadRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("billing:manage"))],
)
def create_billing_head(
    payload: BillingHeadCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BillingHeadRead:
    return BillingService(db).create_billing_head(payload, current_user)


@router.put(
    "/heads/{head_id}",
    response_model=BillingHeadRead,
    dependencies=[Depends(require_permission("billing:manage"))],
)
def update_billing_head(
    head_id: int,
    payload: BillingHeadCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BillingHeadRead:
    return BillingService(db).update_billing_head(head_id, payload, current_user)


@router.get("/head-mappings", response_model=list[BillingHeadMappingRead])
def list_billing_head_mappings(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BillingHeadMappingRead]:
    return BillingService(db).list_head_mappings()


@router.post(
    "/head-mappings",
    response_model=BillingHeadMappingRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("billing:manage"))],
)
def create_billing_head_mapping(
    payload: BillingHeadMappingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BillingHeadMappingRead:
    return BillingService(db).create_head_mapping(payload, current_user)


@router.get("/members/{member_id}/dues", response_model=list[BillingDueLineRead])
def preview_member_dues(
    member_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BillingDueLineRead]:
    return BillingService(db).preview_member_dues(member_id)


@router.get("/invoices", response_model=list[BillingInvoiceRead])
def list_invoices(
    member_id: int | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BillingInvoiceRead]:
    return BillingService(db).list_invoices(member_id=member_id)


@router.post(
    "/invoices",
    response_model=BillingInvoiceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("billing:manage"))],
)
def create_invoice(
    payload: BillingInvoiceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BillingInvoiceRead:
    return BillingService(db).create_invoice(payload, current_user)


@router.get("/invoices/{invoice_id}", response_model=BillingInvoiceRead)
def get_invoice(
    invoice_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BillingInvoiceRead:
    return BillingService(db).serialize_invoice(invoice_id)


@router.post(
    "/invoices/{invoice_id}/cancel",
    response_model=BillingInvoiceRead,
    dependencies=[Depends(require_permission("billing:manage"))],
)
def cancel_invoice(
    invoice_id: int,
    payload: BillingInvoiceCancel,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BillingInvoiceRead:
    return BillingService(db).cancel_invoice(invoice_id, payload)


@router.get("/reports/{report_type}", response_model=BillingReportRead)
def billing_report(
    report_type: str,
    member_id: int | None = Query(default=None),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BillingReportRead:
    from datetime import date

    parsed_from = date.fromisoformat(from_date) if from_date else None
    parsed_to = date.fromisoformat(to_date) if to_date else None
    return BillingService(db).billing_report(report_type, member_id=member_id, from_date=parsed_from, to_date=parsed_to)
