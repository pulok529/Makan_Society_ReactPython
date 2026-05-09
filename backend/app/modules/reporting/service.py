from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO

from fastapi import HTTPException, status
from jinja2 import Environment, FileSystemLoader, select_autoescape
from openpyxl import Workbook

from app.modules.accounting.schemas import IncomeExpenseComparisonReport
from app.modules.reporting.repository import ReportingRepository
from app.modules.reporting.schemas import (
    ChargeRegisterRow,
    CollectionRow,
    DueMemberRow,
    MemberRegisterRow,
    ReceiptDetailLine,
    ReceiptDetailReport,
    ReportEnvelope,
    ReportFilter,
    SingleMemberBillingHistoryRow,
    SingleMemberPaymentHistoryRow,
    SingleMemberStatementReport,
    TotalCollectionRow,
    TotalDueRow,
)


class ReportingService:
    def __init__(self, db) -> None:
        self.db = db
        self.repository = ReportingRepository(db)
        self.template_env = Environment(
            loader=FileSystemLoader("app/modules/reporting/templates"),
            autoescape=select_autoescape(["html"]),
        )

    def _applied_filters(self, filters: ReportFilter) -> dict[str, str]:
        applied: dict[str, str] = {}

        if filters.from_date and filters.to_date:
            applied["date_range"] = f"{filters.from_date.isoformat()} to {filters.to_date.isoformat()}"
        elif filters.from_date:
            applied["from_date"] = filters.from_date.isoformat()
        elif filters.to_date:
            applied["to_date"] = filters.to_date.isoformat()

        if filters.member_id is not None:
            member = next(iter(self.repository.list_members(member_id=filters.member_id)), None)
            applied["member"] = f"{member.member_code} - {member.full_name}" if member else str(filters.member_id)

        if filters.category_id is not None:
            category = next((item for item in self.repository.list_categories() if item.id == filters.category_id), None)
            applied["category"] = category.name if category else str(filters.category_id)

        if filters.billing_period_id is not None:
            period = next((item for item in self.repository.list_periods() if item.id == filters.billing_period_id), None)
            applied["billing_period"] = period.period_name if period else str(filters.billing_period_id)

        if filters.plot_no and filters.plot_no.strip():
            applied["plot_no"] = filters.plot_no.strip()

        return applied

    def due_members(self, filters: ReportFilter) -> ReportEnvelope:
        categories = {item.id: item for item in self.repository.list_categories()}
        charges = self.repository.list_charges(
            member_id=filters.member_id,
            billing_period_id=filters.billing_period_id,
        )
        members = {
            member.id: member
            for member in self.repository.list_members(
                member_id=filters.member_id,
                category_id=filters.category_id,
                plot_no=filters.plot_no,
            )
        }

        grouped: dict[int, DueMemberRow] = {}
        for charge in charges:
            if charge.member_id not in members or float(charge.due_amount) <= 0:
                continue
            member = members[charge.member_id]
            existing = grouped.get(member.id)
            if existing is None:
                grouped[member.id] = DueMemberRow(
                    member_id=member.id,
                    member_code=member.member_code,
                    member_name=member.full_name,
                    category_name=categories[member.category_id].name if member.category_id in categories else None,
                    cell_no=member.cell_no,
                    total_charged=float(charge.net_amount),
                    total_due=float(charge.due_amount),
                    open_charge_count=1,
                )
            else:
                existing.total_charged += float(charge.net_amount)
                existing.total_due += float(charge.due_amount)
                existing.open_charge_count += 1

        rows = sorted(grouped.values(), key=lambda item: (item.member_code, item.member_name))
        return ReportEnvelope(
            report_type="due_members",
            title="Due Members Report",
            generated_at=datetime.now(UTC),
            row_count=len(rows),
            totals={
                "total_due_amount": round(sum(item.total_due for item in rows), 2),
                "member_count": len(rows),
            },
            applied_filters=self._applied_filters(filters),
            rows=[row.model_dump() for row in rows],
        )

    def collections(self, filters: ReportFilter) -> ReportEnvelope:
        members = {member.id: member for member in self.repository.list_members()}
        receipts = self.repository.list_receipts(
            member_id=filters.member_id,
            from_date=filters.from_date,
            to_date=filters.to_date,
        )
        rows = [
            CollectionRow(
                member_id=receipt.member_id,
                member_code=members[receipt.member_id].member_code if receipt.member_id in members else None,
                member_name=members[receipt.member_id].full_name if receipt.member_id in members else None,
                receipt_no=receipt.receipt_no,
                payment_date=receipt.payment_date,
                total_amount=float(receipt.total_amount),
                discount_amount=float(receipt.discount_amount),
            )
            for receipt in receipts
        ]
        rows.sort(key=lambda item: (item.member_code or "", item.payment_date, item.receipt_no))
        return ReportEnvelope(
            report_type="collections",
            title="Collection Report",
            generated_at=datetime.now(UTC),
            row_count=len(rows),
            totals={
                "total_collected": round(sum(item.total_amount for item in rows), 2),
                "discount_amount": round(sum(item.discount_amount for item in rows), 2),
            },
            applied_filters=self._applied_filters(filters),
            rows=[row.model_dump() for row in rows],
        )

    def total_collection(self, filters: ReportFilter) -> ReportEnvelope:
        members = {
            member.id: member
            for member in self.repository.list_members(
                member_id=filters.member_id,
                category_id=filters.category_id,
                plot_no=filters.plot_no,
            )
        }
        grouped: dict[int, TotalCollectionRow] = {}
        for receipt in self.repository.list_receipts(
            member_id=filters.member_id,
            from_date=filters.from_date,
            to_date=filters.to_date,
        ):
            if receipt.member_id is None or receipt.member_id not in members:
                continue
            member = members[receipt.member_id]
            row = grouped.get(member.id)
            if row is None:
                grouped[member.id] = TotalCollectionRow(
                    member_id=member.id,
                    member_code=member.member_code,
                    member_name=member.full_name,
                    plot_no=member.member_id_text,
                    total_collection_amount=float(receipt.total_amount),
                )
            else:
                row.total_collection_amount += float(receipt.total_amount)
        rows = sorted(grouped.values(), key=lambda item: (item.member_code, item.member_name))
        return ReportEnvelope(
            report_type="total_collection",
            title="Total Collection Report",
            generated_at=datetime.now(UTC),
            row_count=len(rows),
            totals={
                "total_collection_amount": round(sum(item.total_collection_amount for item in rows), 2),
                "member_count": len(rows),
            },
            applied_filters=self._applied_filters(filters),
            rows=[row.model_dump() for row in rows],
        )

    def total_due(self, filters: ReportFilter) -> ReportEnvelope:
        members = {
            member.id: member
            for member in self.repository.list_members(
                member_id=filters.member_id,
                category_id=filters.category_id,
                plot_no=filters.plot_no,
            )
        }
        grouped: dict[int, TotalDueRow] = {}
        for charge in self.repository.list_charges(
            member_id=filters.member_id,
            billing_period_id=filters.billing_period_id,
            from_date=filters.from_date,
            to_date=filters.to_date,
        ):
            if charge.member_id not in members or float(charge.due_amount) <= 0:
                continue
            member = members[charge.member_id]
            row = grouped.get(member.id)
            if row is None:
                grouped[member.id] = TotalDueRow(
                    member_id=member.id,
                    member_code=member.member_code,
                    member_name=member.full_name,
                    plot_no=member.member_id_text,
                    total_due_amount=float(charge.due_amount),
                )
            else:
                row.total_due_amount += float(charge.due_amount)
        rows = sorted(grouped.values(), key=lambda item: (item.member_code, item.member_name))
        return ReportEnvelope(
            report_type="total_due",
            title="Total Due Report",
            generated_at=datetime.now(UTC),
            row_count=len(rows),
            totals={
                "total_due_amount": round(sum(item.total_due_amount for item in rows), 2),
                "member_count": len(rows),
            },
            applied_filters=self._applied_filters(filters),
            rows=[row.model_dump() for row in rows],
        )

    def single_member_statement(self, filters: ReportFilter) -> SingleMemberStatementReport:
        if filters.member_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Member is required for this report")
        members = {member.id: member for member in self.repository.list_members(member_id=filters.member_id)}
        member = members.get(filters.member_id)
        if member is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        invoices = self.repository.list_invoices(
            member_id=filters.member_id,
            from_date=filters.from_date,
            to_date=filters.to_date,
        )
        receipts = self.repository.list_receipts(
            member_id=filters.member_id,
            from_date=filters.from_date,
            to_date=filters.to_date,
        )

        billing_history = [
            SingleMemberBillingHistoryRow(
                invoice_no=invoice.invoice_no,
                invoice_date=invoice.invoice_date,
                total_bill=float(invoice.net_amount),
                paid_amount=float(invoice.total_receive_amount),
                due_amount=float(invoice.total_due_amount),
                status="Cancelled" if invoice.is_cancelled else ("Paid" if float(invoice.total_due_amount) <= 0 else "Due"),
            )
            for invoice in invoices
        ]
        payment_history = [
            SingleMemberPaymentHistoryRow(
                receipt_no=receipt.receipt_no,
                payment_date=receipt.payment_date,
                amount=float(receipt.total_amount),
                discount_amount=float(receipt.discount_amount),
            )
            for receipt in receipts
        ]
        return SingleMemberStatementReport(
            member_id=member.id,
            member_code=member.member_code,
            member_name=member.full_name,
            plot_no=member.member_id_text,
            total_bill=round(sum(item.total_bill for item in billing_history), 2),
            paid_amount=round(sum(item.paid_amount for item in billing_history), 2),
            due_amount=round(sum(item.due_amount for item in billing_history), 2),
            billing_history=billing_history,
            payment_history=payment_history,
        )

    def charge_register(self, filters: ReportFilter) -> ReportEnvelope:
        members = {member.id: member for member in self.repository.list_members()}
        periods = {period.id: period for period in self.repository.list_periods()}
        charges = self.repository.list_charges(
            member_id=filters.member_id,
            billing_period_id=filters.billing_period_id,
            from_date=filters.from_date,
            to_date=filters.to_date,
        )
        rows = [
            ChargeRegisterRow(
                charge_id=charge.id,
                created_at=charge.created_at,
                member_id=charge.member_id,
                member_code=members[charge.member_id].member_code if charge.member_id in members else "Unknown",
                member_name=members[charge.member_id].full_name if charge.member_id in members else "Unknown",
                billing_period_name=periods[charge.billing_period_id].period_name
                if charge.billing_period_id in periods
                else None,
                charge_type=charge.charge_type,
                status=charge.status,
                net_amount=float(charge.net_amount),
                due_amount=float(charge.due_amount),
            )
            for charge in charges
        ]
        rows.sort(key=lambda item: (item.member_code, item.created_at, item.charge_id))
        return ReportEnvelope(
            report_type="charge_register",
            title="Charge Register",
            generated_at=datetime.now(UTC),
            row_count=len(rows),
            totals={
                "net_amount": round(sum(item.net_amount for item in rows), 2),
                "due_amount": round(sum(item.due_amount for item in rows), 2),
            },
            applied_filters=self._applied_filters(filters),
            rows=[row.model_dump(mode="json") for row in rows],
        )

    def member_register(self, filters: ReportFilter) -> ReportEnvelope:
        categories = {item.id: item for item in self.repository.list_categories()}
        packages = {item.id: item for item in self.repository.list_packages()}
        member_packages = self.repository.list_member_packages()
        latest_active_package: dict[int, str | None] = {}
        for assignment in member_packages:
            if assignment.is_active and assignment.package_id in packages:
                latest_active_package[assignment.member_id] = packages[assignment.package_id].name

        members = self.repository.list_members(member_id=filters.member_id, category_id=filters.category_id)
        rows = [
            MemberRegisterRow(
                member_id=member.id,
                member_code=member.member_code,
                full_name=member.full_name,
                category_name=categories[member.category_id].name if member.category_id in categories else None,
                cell_no=member.cell_no,
                email=member.email,
                joined_on=member.joined_on,
                is_active=member.is_active,
                active_package_name=latest_active_package.get(member.id),
            )
            for member in members
        ]
        return ReportEnvelope(
            report_type="member_register",
            title="Member Register",
            generated_at=datetime.now(UTC),
            row_count=len(rows),
            totals={"member_count": len(rows), "active_members": sum(1 for row in rows if row.is_active)},
            applied_filters=self._applied_filters(filters),
            rows=[row.model_dump(mode="json") for row in rows],
        )

    def receipt_detail(self, receipt_id: int) -> ReceiptDetailReport:
        members = {member.id: member for member in self.repository.list_members()}
        receipt = self.repository.get_receipt(receipt_id)
        if receipt is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")
        member = members.get(receipt.member_id) if receipt.member_id is not None else None
        lines = self.repository.list_receipt_lines(receipt_id)
        return ReceiptDetailReport(
            receipt_id=receipt.id,
            receipt_no=receipt.receipt_no,
            payment_date=receipt.payment_date,
            member_name=member.full_name if member is not None else None,
            member_code=member.member_code if member is not None else None,
            subtotal_amount=float(receipt.subtotal_amount),
            discount_amount=float(receipt.discount_amount),
            total_amount=float(receipt.total_amount),
            lines=[
                ReceiptDetailLine(line_type=line.line_type, amount=float(line.amount), charge_id=line.charge_id)
                for line in lines
            ],
        )

    def render_html(self, report: ReportEnvelope) -> str:
        template = self.template_env.get_template("table_report.html")
        return template.render(report=report)

    def render_xlsx(self, report: ReportEnvelope) -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = report.title[:31]
        sheet.append([report.title])
        sheet.append([f"Generated at: {report.generated_at.isoformat()}"])
        for key, value in report.applied_filters.items():
            sheet.append([key, value])
        sheet.append([])
        if report.rows:
            headers = list(report.rows[0].keys())
            sheet.append(headers)
            for row in report.rows:
                sheet.append([row.get(header) for header in headers])
        sheet.append([])
        sheet.append(["Totals"])
        for key, value in report.totals.items():
            sheet.append([key, value])

        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def render_receipt_xlsx(self, report: ReceiptDetailReport) -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Receipt Detail"
        sheet.append(["Receipt Detail Report"])
        sheet.append(["Receipt No", report.receipt_no])
        sheet.append(["Payment Date", report.payment_date.isoformat()])
        sheet.append(["Member Name", report.member_name or ""])
        sheet.append(["Member Code", report.member_code or ""])
        sheet.append(["Subtotal", report.subtotal_amount])
        sheet.append(["Discount", report.discount_amount])
        sheet.append(["Collected", report.total_amount])
        sheet.append([])
        sheet.append(["Line Type", "Charge ID", "Amount"])
        for line in report.lines:
            sheet.append([line.line_type, line.charge_id, line.amount])

        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def render_member_statement_xlsx(self, report: SingleMemberStatementReport) -> bytes:
        workbook = Workbook()
        summary_sheet = workbook.active
        summary_sheet.title = "Member Statement"
        summary_sheet.append(["Single Member Due And Paid Statement"])
        summary_sheet.append(["Member Code", report.member_code])
        summary_sheet.append(["Member Name", report.member_name])
        summary_sheet.append(["Plot No", report.plot_no or ""])
        summary_sheet.append(["Total Bill", report.total_bill])
        summary_sheet.append(["Paid Amount", report.paid_amount])
        summary_sheet.append(["Due Amount", report.due_amount])

        billing_sheet = workbook.create_sheet("Billing History")
        billing_sheet.append(["Invoice No", "Invoice Date", "Total Bill", "Paid Amount", "Due Amount", "Status"])
        for row in report.billing_history:
            billing_sheet.append(
                [row.invoice_no, row.invoice_date.isoformat(), row.total_bill, row.paid_amount, row.due_amount, row.status]
            )

        payment_sheet = workbook.create_sheet("Payment History")
        payment_sheet.append(["Receipt No", "Payment Date", "Paid Amount", "Discount Amount"])
        for row in report.payment_history:
            payment_sheet.append([row.receipt_no, row.payment_date.isoformat(), row.amount, row.discount_amount])

        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def render_income_expense_xlsx(self, report: IncomeExpenseComparisonReport) -> bytes:
        workbook = Workbook()
        summary_sheet = workbook.active
        summary_sheet.title = "Summary"
        summary_sheet.append(["Income vs Expense Report"])
        summary_sheet.append(["From Date", report.from_date.isoformat() if report.from_date else ""])
        summary_sheet.append(["To Date", report.to_date.isoformat() if report.to_date else ""])
        summary_sheet.append(["Income Subtotal", report.income.subtotal])
        summary_sheet.append(["Expense Subtotal", report.expense.subtotal])
        summary_sheet.append(["Net Amount", report.net_amount])

        income_sheet = workbook.create_sheet("Income")
        income_rows = report.income.rows
        income_headers = list(income_rows[0].keys()) if income_rows else ["coa_name", "amount"]
        income_sheet.append(income_headers)
        for row in income_rows:
            income_sheet.append([row.get(header) for header in income_headers])
        income_sheet.append([])
        income_sheet.append(["Subtotal", report.income.subtotal])

        expense_sheet = workbook.create_sheet("Expense")
        expense_rows = report.expense.rows
        expense_headers = list(expense_rows[0].keys()) if expense_rows else ["coa_name", "amount"]
        expense_sheet.append(expense_headers)
        for row in expense_rows:
            expense_sheet.append([row.get(header) for header in expense_headers])
        expense_sheet.append([])
        expense_sheet.append(["Subtotal", report.expense.subtotal])

        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()
