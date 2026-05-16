from collections import defaultdict
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.billing.models import (
    BillingHead,
    BillingHeadCoaMapping,
    BillingInvoice,
    BillingInvoiceDetail,
    BillingPeriod,
    Charge,
    ChargeItem,
    Receipt,
    ReceiptLine,
)
from app.modules.billing.repository import BillingRepository
from app.modules.billing.schemas import (
    BillingDashboardRead,
    BillingGenerationRequest,
    BillingDueLineRead,
    BillingHeadCreate,
    BillingHeadMappingCreate,
    BillingHeadMappingRead,
    BillingHeadRead,
    BillingInvoiceCancel,
    BillingInvoiceCreate,
    BillingInvoiceDetailRead,
    BillingInvoiceRead,
    BillingReportRead,
    BillingMemberSummary,
    BillingPeriodCreate,
    ChargeRead,
    ChargeItemRead,
    ReceiptCreate,
    ReceiptLineRead,
    ReceiptRead,
)
from app.modules.members.repository import MemberRepository
from app.modules.packages.repository import PackageRepository
from app.modules.accounting.service import AccountingService


class BillingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = BillingRepository(db)
        self.member_repository = MemberRepository(db)
        self.package_repository = PackageRepository(db)

    def list_billing_heads(self) -> list[BillingHeadRead]:
        self._ensure_default_billing_setup()
        return [self._serialize_head(head) for head in self.repository.list_billing_heads()]

    def create_billing_head(self, payload: BillingHeadCreate, user: User) -> BillingHeadRead:
        billing_mode = "Mandatory" if payload.head_type == "Period" else payload.billing_mode
        if payload.head_type == "Period" and not payload.effective_from_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Period heads require effective date")
        if payload.head_type == "OneTime" and (payload.effective_from_month or payload.effective_from_year):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OneTime heads do not use period input")
        if billing_mode == "Mandatory" and payload.fee_amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mandatory heads require a fee amount")
        head = BillingHead(
            head_name=payload.head_name.strip(),
            head_type=payload.head_type,
            billing_mode=billing_mode,
            fee_amount=payload.fee_amount,
            effective_from_month=payload.effective_from_month,
            effective_from_year=payload.effective_from_year,
            effective_from_date=payload.effective_from_date,
            is_active=payload.is_active,
            created_by=user.id,
        )
        self.repository.add_billing_head(head)
        self.db.commit()
        return self._serialize_head(head)

    def update_billing_head(self, head_id: int, payload: BillingHeadCreate, user: User) -> BillingHeadRead:
        old_head = self.repository.get_billing_head(head_id)
        if old_head is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing head not found")
        billing_mode = "Mandatory" if payload.head_type == "Period" else payload.billing_mode
        if payload.head_type == "Period" and not payload.effective_from_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Period heads require effective date")
        if payload.head_type == "OneTime" and (payload.effective_from_month or payload.effective_from_year):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OneTime heads do not use period input")
        if billing_mode == "Mandatory" and payload.fee_amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mandatory heads require a fee amount")

        old_mapping = self.repository.get_active_head_mapping(old_head.id)
        old_head.is_active = False
        old_head.head_name = f"{old_head.head_name} (inactive {old_head.id})"[:150]
        if old_mapping is not None:
            old_mapping.is_active = False

        new_head = BillingHead(
            head_name=payload.head_name.strip(),
            head_type=payload.head_type,
            billing_mode=billing_mode,
            fee_amount=payload.fee_amount,
            effective_from_month=payload.effective_from_month,
            effective_from_year=payload.effective_from_year,
            effective_from_date=payload.effective_from_date,
            is_active=True,
            created_by=user.id,
        )
        self.repository.add_billing_head(new_head)
        if old_mapping is not None:
            self.repository.add_head_mapping(
                BillingHeadCoaMapping(
                    billing_head_id=new_head.id,
                    coa_id=old_mapping.coa_id,
                    is_active=True,
                    created_by=user.id,
                )
            )
        self.db.commit()
        return self._serialize_head(new_head)

    def list_head_mappings(self) -> list[BillingHeadMappingRead]:
        self._ensure_default_billing_setup()
        heads = {head.id: head for head in self.repository.list_billing_heads()}
        accounts = {account.id: account for account in self.repository.list_accounts()}
        return [
            BillingHeadMappingRead(
                id=mapping.id,
                billing_head_id=mapping.billing_head_id,
                billing_head_name=heads[mapping.billing_head_id].head_name if mapping.billing_head_id in heads else "Unknown",
                coa_id=mapping.coa_id,
                coa_name=accounts[mapping.coa_id].name if mapping.coa_id in accounts else "Unknown",
                is_active=mapping.is_active,
                created_at=mapping.created_at,
                created_by=mapping.created_by,
            )
            for mapping in self.repository.list_head_mappings()
        ]

    def create_head_mapping(self, payload: BillingHeadMappingCreate, user: User) -> BillingHeadMappingRead:
        head = self.repository.get_billing_head(payload.billing_head_id)
        account = next((item for item in self.repository.list_accounts() if item.id == payload.coa_id), None)
        if head is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing head not found")
        if account is None or account.account_type not in {"income", "both"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mapping requires an income COA")
        existing = self.repository.get_active_head_mapping(payload.billing_head_id)
        if payload.is_active and existing is not None:
            existing.is_active = False
        mapping = BillingHeadCoaMapping(
            billing_head_id=payload.billing_head_id,
            coa_id=payload.coa_id,
            is_active=payload.is_active,
            created_by=user.id,
        )
        self.repository.add_head_mapping(mapping)
        self.db.commit()
        return self.list_head_mappings()[0]

    def preview_member_dues(self, member_id: int) -> list[BillingDueLineRead]:
        self._ensure_default_billing_setup()
        member = self.member_repository.get_by_id(member_id)
        if member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        return self._build_member_due_lines(member)

    def create_invoice(self, payload: BillingInvoiceCreate, user: User) -> BillingInvoiceRead:
        self._ensure_default_billing_setup()
        member = self.member_repository.get_by_id(payload.member_id)
        if member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        billable_lines = [line for line in payload.lines if line.receive_amount > 0]
        if not billable_lines:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice requires at least one row with receive amount")

        heads = {head.id: head for head in self.repository.list_billing_heads(active_only=True)}
        subtotal = sum(line.receive_amount for line in billable_lines)
        if payload.discount_amount > subtotal:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Discount cannot exceed subtotal")
        total_line_receive = sum(line.receive_amount for line in billable_lines)
        total_line_discount = sum(line.discount_amount for line in billable_lines)
        if total_line_discount > sum(line.fee_amount for line in billable_lines):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Discount cannot exceed subtotal")
        total_due = sum(max(line.fee_amount - line.receive_amount - line.discount_amount, 0) for line in billable_lines)

        invoice = BillingInvoice(
            invoice_no=f"INV-{date.today():%Y%m%d}-{self.repository.count_invoices() + 1:05d}",
            member_id=payload.member_id,
            invoice_date=payload.invoice_date,
            subtotal_amount=subtotal,
            discount_amount=payload.discount_amount,
            net_amount=subtotal - payload.discount_amount - total_line_discount,
            total_receive_amount=total_line_receive,
            total_due_amount=total_due,
            is_cancelled=False,
            cancel_reason=None,
            created_by=user.id,
        )
        self.repository.add_invoice(invoice)

        for line in billable_lines:
            head = heads.get(line.billing_head_id)
            if head is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing head not found")
            if head.head_type == "Period" and line.period_date is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Period head requires period date")
            if head.head_type == "OneTime" and line.period_date is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OneTime head cannot use period date")
            if head.billing_mode == "Mandatory" and line.fee_amount <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mandatory head requires fee amount")
            if head.billing_mode == "Optional" and head.head_type == "OneTime" and line.fee_amount <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Optional one-time head requires amount when billing")
            if line.receive_amount + line.discount_amount > line.fee_amount:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Receive amount plus discount cannot exceed fee")
            if line.period_date is not None:
                paid, due = self.repository.get_period_payment_totals(payload.member_id, head.id, line.period_date)
                if due <= 0 < paid and line.receive_amount + line.discount_amount >= line.fee_amount:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This member/head/period is already fully paid")
            elif head.billing_mode == "Mandatory":
                paid, due = self.repository.get_one_time_payment_totals(payload.member_id, head.id)
                if due <= 0 < paid and line.receive_amount + line.discount_amount >= line.fee_amount:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This mandatory one-time head is already fully paid")

            mapping = self.repository.get_active_head_mapping(head.id)
            due_amount = max(line.fee_amount - line.receive_amount - line.discount_amount, 0)
            self.repository.add_invoice_detail(
                BillingInvoiceDetail(
                    invoice_id=invoice.id,
                    member_id=payload.member_id,
                    billing_head_id=head.id,
                    head_name_snapshot=head.head_name,
                    head_type=head.head_type,
                    period_date=line.period_date,
                    period_display=self._period_display(line.period_date) if line.period_date else None,
                    fee_amount=line.fee_amount,
                    receive_amount=line.receive_amount,
                    due_amount=due_amount,
                    discount_amount=line.discount_amount,
                    coa_id_snapshot=mapping.coa_id if mapping else None,
                    is_income_transferred=False,
                    created_by=user.id,
                )
            )
        self.db.commit()
        return self.serialize_invoice(invoice.id)

    def list_invoices(self, member_id: int | None = None) -> list[BillingInvoiceRead]:
        return [self.serialize_invoice(invoice.id) for invoice in self.repository.list_invoices(member_id=member_id)]

    def serialize_invoice(self, invoice_id: int) -> BillingInvoiceRead:
        invoice = self.repository.get_invoice(invoice_id)
        if invoice is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        member = self.member_repository.get_by_id(invoice.member_id)
        details = self.repository.list_invoice_details(invoice.id)
        return BillingInvoiceRead(
            id=invoice.id,
            invoice_no=invoice.invoice_no,
            member_id=invoice.member_id,
            member_name=member.full_name if member is not None else "Unknown",
            invoice_date=invoice.invoice_date,
            subtotal_amount=float(invoice.subtotal_amount),
            discount_amount=float(invoice.discount_amount),
            net_amount=float(invoice.net_amount),
            total_receive_amount=float(invoice.total_receive_amount),
            total_due_amount=float(invoice.total_due_amount),
            is_cancelled=invoice.is_cancelled,
            cancel_reason=invoice.cancel_reason,
            created_at=invoice.created_at,
            created_by=invoice.created_by,
            details=[self._serialize_invoice_detail(detail) for detail in details],
        )

    def cancel_invoice(self, invoice_id: int, payload: BillingInvoiceCancel) -> BillingInvoiceRead:
        invoice = self.repository.get_invoice(invoice_id)
        if invoice is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        invoice.is_cancelled = True
        invoice.cancel_reason = payload.cancel_reason
        self.db.commit()
        return self.serialize_invoice(invoice_id)

    def billing_report(self, report_type: str, member_id: int | None = None, from_date: date | None = None, to_date: date | None = None) -> BillingReportRead:
        rows: list[dict[str, str | int | float | None]] = []
        invoices = self.repository.list_invoices(member_id=member_id)
        for invoice in invoices:
            if from_date and invoice.invoice_date < from_date:
                continue
            if to_date and invoice.invoice_date > to_date:
                continue
            serialized = self.serialize_invoice(invoice.id)
            for detail in serialized.details:
                rows.append(
                    {
                        "invoice_no": serialized.invoice_no,
                        "member": serialized.member_name,
                        "invoice_date": str(serialized.invoice_date),
                        "head": detail.head_name_snapshot,
                        "period": detail.period_display,
                        "fee": detail.fee_amount,
                        "received": detail.receive_amount,
                        "due": detail.due_amount,
                        "coa_id": detail.coa_id_snapshot,
                        "transferred": int(detail.is_income_transferred),
                    }
                )
        if report_type == "customer-wise-due":
            rows = [row for row in rows if float(row["due"] or 0) > 0]
        if report_type == "head-wise-collection":
            grouped: dict[str, float] = defaultdict(float)
            for row in rows:
                grouped[str(row["head"])] += float(row["received"] or 0)
            rows = [{"head": key, "received": value} for key, value in grouped.items()]
        if report_type == "income-transfer-pending":
            rows = [row for row in rows if float(row["received"] or 0) > 0 and not row["transferred"]]
        return BillingReportRead(report_type=report_type, row_count=len(rows), rows=rows)

    def list_periods(self) -> list[BillingPeriod]:
        return self.repository.list_periods()

    def create_period(self, payload: BillingPeriodCreate) -> BillingPeriod:
        if payload.starts_on > payload.ends_on:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period range")
        if self.repository.get_period_by_year_month(payload.year, payload.month) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Billing period already exists")

        period = BillingPeriod(
            year=payload.year,
            month=payload.month,
            period_name=f"{payload.year}-{payload.month:02d}",
            starts_on=payload.starts_on,
            ends_on=payload.ends_on,
            is_closed=False,
        )
        self.repository.add_period(period)
        self.db.commit()
        return period

    def generate_period_charges(self, payload: BillingGenerationRequest) -> list[Charge]:
        period = self.repository.get_period(payload.billing_period_id)
        if period is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing period not found")
        if period.is_closed:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Billing period is closed")

        assignments = self.repository.list_active_member_packages_for_period(period.starts_on, period.ends_on)
        packages = {package.id: package for package in self.package_repository.list_packages()}
        grouped_assignments: dict[int, list] = defaultdict(list)
        for assignment in assignments:
            grouped_assignments[assignment.member_id].append(assignment)

        generated: list[Charge] = []
        for member_id, member_assignments in grouped_assignments.items():
            existing = self.repository.get_existing_member_charge(
                member_id=member_id,
                billing_period_id=period.id,
                charge_type=payload.charge_type,
            )
            if existing is not None:
                continue

            total_amount = 0.0
            item_rows: list[tuple[int | None, str, float]] = []
            for assignment in member_assignments:
                package = packages.get(assignment.package_id)
                if package is None or not package.is_active:
                    continue
                price = float(package.default_price)
                total_amount += price
                item_rows.append((package.id, package.name, price))

            if not item_rows:
                continue

            charge = Charge(
                member_id=member_id,
                billing_period_id=period.id,
                charge_type=payload.charge_type,
                status="open",
                total_amount=total_amount,
                discount_amount=0,
                net_amount=total_amount,
                due_amount=total_amount,
            )
            self.repository.add_charge(charge)
            for package_id, package_name, price in item_rows:
                self.repository.add_charge_item(
                    ChargeItem(
                        charge_id=charge.id,
                        package_id=package_id,
                        item_type="package",
                        description=f"{package_name} charge for {period.period_name}",
                        quantity=1,
                        unit_amount=price,
                        line_amount=price,
                    )
                )
            generated.append(charge)

        self.db.commit()
        return generated

    def list_charges(self, billing_period_id: int | None = None, member_id: int | None = None) -> list[ChargeRead]:
        members = {member.id: member for member in self.member_repository.list_members()}
        periods = {period.id: period for period in self.repository.list_periods()}
        packages = {package.id: package for package in self.package_repository.list_packages()}
        serialized: list[ChargeRead] = []

        for charge in self.repository.list_charges(billing_period_id=billing_period_id, member_id=member_id):
            member = members.get(charge.member_id)
            period = periods.get(charge.billing_period_id) if charge.billing_period_id is not None else None
            items = self.repository.list_charge_items(charge.id)
            serialized.append(
                ChargeRead(
                    id=charge.id,
                    member_id=charge.member_id,
                    member_name=member.full_name if member is not None else "Unknown",
                    member_code=member.member_code if member is not None else "Unknown",
                    billing_period_id=charge.billing_period_id,
                    billing_period_name=period.period_name if period is not None else None,
                    charge_type=charge.charge_type,
                    status=charge.status,
                    total_amount=float(charge.total_amount),
                    discount_amount=float(charge.discount_amount),
                    net_amount=float(charge.net_amount),
                    due_amount=float(charge.due_amount),
                    created_at=charge.created_at,
                    items=[
                        ChargeItemRead(
                            id=item.id,
                            package_id=item.package_id,
                            package_name=packages[item.package_id].name
                            if item.package_id is not None and item.package_id in packages
                            else None,
                            item_type=item.item_type,
                            description=item.description,
                            quantity=item.quantity,
                            unit_amount=float(item.unit_amount),
                            line_amount=float(item.line_amount),
                        )
                        for item in items
                    ],
                )
            )

        return serialized

    def create_receipt(self, payload: ReceiptCreate, collected_by: User) -> ReceiptRead:
        member = self.member_repository.get_by_id(payload.member_id)
        if member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        if not payload.lines:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Receipt needs at least one line")

        subtotal = 0.0
        charges: list[Charge] = []
        for line in payload.lines:
            charge = self.repository.get_charge(line.charge_id)
            if charge is None or charge.member_id != payload.member_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge not found for member")
            if float(charge.due_amount) <= 0:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Charge already settled")
            if line.amount > float(charge.due_amount):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment exceeds charge due")
            charges.append(charge)
            subtotal += line.amount

        total_amount = subtotal - payload.discount_amount
        if total_amount < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Discount exceeds subtotal")

        receipt_no = f"RCV-{date.today():%Y%m%d}-{self.repository.count_receipts() + 1:04d}"
        receipt = Receipt(
            receipt_no=receipt_no,
            member_id=payload.member_id,
            collected_by_user_id=collected_by.id,
            receipt_type="collection",
            payment_date=payload.payment_date,
            subtotal_amount=subtotal,
            discount_amount=payload.discount_amount,
            total_amount=total_amount,
            notes=payload.notes,
        )
        self.repository.add_receipt(receipt)

        for charge, line in zip(charges, payload.lines, strict=True):
            charge.due_amount = float(charge.due_amount) - line.amount
            if charge.due_amount <= 0:
                charge.due_amount = 0
                charge.status = "paid"
            elif charge.due_amount < float(charge.net_amount):
                charge.status = "partial"

            self.repository.add_receipt_line(
                ReceiptLine(
                    receipt_id=receipt.id,
                    charge_id=charge.id,
                    charge_item_id=None,
                    line_type="charge_payment",
                    amount=line.amount,
                )
            )

        # Phase 7 integration: auto-post billing collection into accounting income.
        AccountingService(self.db).post_billing_collection(total_amount, receipt_no)
        self.db.commit()
        return self.serialize_receipt(receipt.id)

    def list_receipts(self, member_id: int | None = None) -> list[ReceiptRead]:
        return [self.serialize_receipt(receipt.id) for receipt in self.repository.list_receipts(member_id=member_id)]

    def serialize_receipt(self, receipt_id: int) -> ReceiptRead:
        receipt = next((item for item in self.repository.list_receipts() if item.id == receipt_id), None)
        if receipt is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")

        member = self.member_repository.get_by_id(receipt.member_id) if receipt.member_id is not None else None
        lines = self.repository.list_receipt_lines(receipt.id)
        return ReceiptRead(
            id=receipt.id,
            receipt_no=receipt.receipt_no,
            member_id=receipt.member_id,
            member_name=member.full_name if member is not None else None,
            collected_by_user_id=receipt.collected_by_user_id,
            receipt_type=receipt.receipt_type,
            payment_date=receipt.payment_date,
            subtotal_amount=float(receipt.subtotal_amount),
            discount_amount=float(receipt.discount_amount),
            total_amount=float(receipt.total_amount),
            notes=receipt.notes,
            created_at=receipt.created_at,
            lines=[
                ReceiptLineRead(
                    id=line.id,
                    charge_id=line.charge_id,
                    charge_item_id=line.charge_item_id,
                    line_type=line.line_type,
                    amount=float(line.amount),
                )
                for line in lines
            ],
        )

    def dashboard(self) -> BillingDashboardRead:
        open_charges, total_due = self.repository.summarize_open_charges()
        return BillingDashboardRead(
            total_members_with_due=self.repository.summarize_members_with_due(),
            total_due_amount=total_due,
            total_open_charges=open_charges,
            total_receipts=self.repository.count_receipts(),
        )

    def member_due_summaries(self) -> list[BillingMemberSummary]:
        return [
            BillingMemberSummary(
                member_id=member_id,
                member_code=member_code,
                member_name=member_name,
                total_charged=float(total_charged),
                total_due=float(total_due),
                open_charge_count=int(open_charge_count),
            )
            for member_id, member_code, member_name, total_charged, total_due, open_charge_count in self.repository.list_member_due_summaries()
        ]

    def _ensure_default_billing_setup(self) -> None:
        heads = self.repository.list_billing_heads()
        if not heads:
            head = BillingHead(
                head_name="Monthly Subscription",
                head_type="Period",
                billing_mode="Mandatory",
                fee_amount=500,
                effective_from_month=1,
                effective_from_year=2018,
                effective_from_date=date(2018, 1, 1),
                is_active=True,
                created_by=None,
            )
            self.repository.add_billing_head(head)
            account = next((item for item in self.repository.list_accounts() if item.code == "MONTHLY-FEE"), None)
            if account is None:
                from app.modules.accounting.models import Account

                account = Account(code="MONTHLY-FEE", name="Monthly Fee Income", account_type="income", is_active=True)
                self.db.add(account)
                self.db.flush()
                self.db.refresh(account)
            self.repository.add_head_mapping(BillingHeadCoaMapping(billing_head_id=head.id, coa_id=account.id, is_active=True, created_by=None))
            self.db.commit()

    @staticmethod
    def _serialize_head(head: BillingHead) -> BillingHeadRead:
        return BillingHeadRead(
            id=head.id,
            head_name=head.head_name,
            head_type=head.head_type,
            billing_mode=head.billing_mode,
            fee_amount=float(head.fee_amount),
            effective_from_month=head.effective_from_month,
            effective_from_year=head.effective_from_year,
            effective_from_date=head.effective_from_date,
            is_active=head.is_active,
            created_at=head.created_at,
            created_by=head.created_by,
        )

    @staticmethod
    def _serialize_invoice_detail(detail: BillingInvoiceDetail) -> BillingInvoiceDetailRead:
        return BillingInvoiceDetailRead(
            id=detail.id,
            invoice_id=detail.invoice_id,
            member_id=detail.member_id,
            billing_head_id=detail.billing_head_id,
            head_name_snapshot=detail.head_name_snapshot,
            head_type=detail.head_type,
            period_date=detail.period_date,
            period_display=detail.period_display,
            fee_amount=float(detail.fee_amount),
            receive_amount=float(detail.receive_amount),
            due_amount=float(detail.due_amount),
            discount_amount=float(detail.discount_amount),
            coa_id_snapshot=detail.coa_id_snapshot,
            income_voucher_id=detail.income_voucher_id,
            is_income_transferred=detail.is_income_transferred,
            created_at=detail.created_at,
            created_by=detail.created_by,
        )

    def _build_member_due_lines(self, member) -> list[BillingDueLineRead]:
        today = date.today()
        rows: list[BillingDueLineRead] = []
        for head in self.repository.list_billing_heads(active_only=True):
            mapping = self.repository.get_active_head_mapping(head.id)
            if head.head_type == "Period":
                start = self._month_start(member.joined_on or date(2018, 1, 1))
                start = max(start, date(2018, 1, 1))
                if head.effective_from_date:
                    start = max(start, self._month_start(head.effective_from_date))
                current = start
                end = self._month_start(today)
                while current <= end:
                    fee = self._period_fee(current, float(head.fee_amount))
                    paid, due = self.repository.get_period_payment_totals(member.id, head.id, current)
                    remaining = fee - paid
                    if due > 0:
                        remaining = due
                    if remaining > 0:
                        rows.append(
                            BillingDueLineRead(
                                member_id=member.id,
                                billing_head_id=head.id,
                                head_name=head.head_name,
                                head_type=head.head_type,
                                billing_mode=head.billing_mode,
                                period_date=current,
                                period_display=self._period_display(current),
                                fee_amount=fee,
                                paid_amount=paid,
                                due_amount=remaining,
                                coa_id_snapshot=mapping.coa_id if mapping else None,
                            )
                        )
                    current = self._next_month(current)
                continue

            if head.billing_mode != "Mandatory":
                continue

            fee = float(head.fee_amount)
            paid, due = self.repository.get_one_time_payment_totals(member.id, head.id)
            remaining = due if due > 0 else max(fee - paid, 0)
            if remaining > 0:
                rows.append(
                    BillingDueLineRead(
                        member_id=member.id,
                        billing_head_id=head.id,
                        head_name=head.head_name,
                        head_type=head.head_type,
                        billing_mode=head.billing_mode,
                        period_date=None,
                        period_display=None,
                        fee_amount=fee,
                        paid_amount=paid,
                        due_amount=remaining,
                        coa_id_snapshot=mapping.coa_id if mapping else None,
                    )
                )
        return rows

    @staticmethod
    def _period_fee(period_date: date, default_fee: float) -> float:
        if date(2018, 1, 1) <= period_date <= date(2022, 12, 1):
            return 300.0
        if period_date >= date(2023, 1, 1):
            return 500.0
        return default_fee

    @staticmethod
    def _month_start(value: date) -> date:
        return date(value.year, value.month, 1)

    @staticmethod
    def _next_month(value: date) -> date:
        return date(value.year + 1, 1, 1) if value.month == 12 else date(value.year, value.month + 1, 1)

    @staticmethod
    def _period_display(value: date) -> str:
        return f"{value.month:02d}-{value.year}"
