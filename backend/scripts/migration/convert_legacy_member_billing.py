from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import text

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal
from app.modules.accounting.models import Account  # noqa: F401
from app.modules.auth.models import User  # noqa: F401
from app.modules.billing.models import BillingInvoice, BillingInvoiceDetail
from app.modules.members.models import Member

LEGACY_DB_NAME = "LegacySocietyDB_20260502_Latest"


def _period_fee(period_date: date) -> float:
    if date(2018, 1, 1) <= period_date <= date(2022, 12, 1):
        return 300.0
    if period_date >= date(2023, 1, 1):
        return 500.0
    return 300.0


def _period_display(period_date: date) -> str:
    return f"{period_date:%m-%Y}"


def _legacy_monthly_rows(db, member_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
                r.id AS receipt_id,
                r.receipt_no,
                r.payment_date,
                c.id AS charge_id,
                ci.id AS charge_item_id,
                bp.starts_on AS period_date,
                bp.period_name,
                ci.line_amount,
                c.charge_type
            FROM billing.charges c
            JOIN billing.charge_items ci ON ci.charge_id = c.id
            JOIN billing.receipt_lines rl ON rl.charge_item_id = ci.id
            JOIN billing.receipts r ON r.id = rl.receipt_id
            JOIN billing.billing_periods bp ON bp.id = c.billing_period_id
            WHERE c.member_id = :member_id
              AND bp.starts_on >= '2018-01-01'
              AND LOWER(c.charge_type) LIKE '%monthly%'
            ORDER BY r.payment_date, r.id, bp.starts_on, ci.id
            """
        ),
        {"member_id": member_id},
    ).mappings()
    return [dict(row) for row in rows]


def _legacy_generated_monthly_rows(db, member_code: str) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            f"""
            WITH MonthMap AS (
                SELECT 'January' AS MonthName, 1 AS MonthNo UNION ALL
                SELECT 'February', 2 UNION ALL
                SELECT 'March', 3 UNION ALL
                SELECT 'April', 4 UNION ALL
                SELECT 'May', 5 UNION ALL
                SELECT 'June', 6 UNION ALL
                SELECT 'July', 7 UNION ALL
                SELECT 'August', 8 UNION ALL
                SELECT 'September', 9 UNION ALL
                SELECT 'October', 10 UNION ALL
                SELECT 'November', 11 UNION ALL
                SELECT 'December', 12
            )
            SELECT
                CAST(cb.[Year] AS int) AS bill_year,
                mm.MonthNo AS bill_month,
                DATEFROMPARTS(CAST(cb.[Year] AS int), mm.MonthNo, 1) AS period_date,
                SUM(CAST(ISNULL(cb.RecevableAmount, 0) AS decimal(18, 2))) AS receivable_amount
            FROM [{LEGACY_DB_NAME}].dbo.CustomerBillInfoMaster cb
            JOIN [{LEGACY_DB_NAME}].dbo.tblCustomer c ON c.CustomerId = cb.CustomerId
            JOIN MonthMap mm ON mm.MonthName = cb.MonthName
            WHERE c.CustomerCode = :member_code
              AND cb.AmountType LIKE '%Monthly%'
              AND DATEFROMPARTS(CAST(cb.[Year] AS int), mm.MonthNo, 1) >= '2018-01-01'
            GROUP BY CAST(cb.[Year] AS int), mm.MonthNo
            ORDER BY CAST(cb.[Year] AS int), mm.MonthNo
            """
        ),
        {"member_code": member_code},
    ).mappings()
    return [dict(row) for row in rows]


def _existing_period_due(db, member_id: int, head_id: int, period_date: date) -> float:
    value = db.execute(
        text(
            """
            SELECT COALESCE(SUM(d.DueAmount), 0)
            FROM billing.billing_invoice_details d
            JOIN billing.billing_invoices i ON i.InvoiceID = d.InvoiceID
            WHERE i.IsCancelled = 0
              AND d.MemberID = :member_id
              AND d.BillingHeadID = :head_id
              AND d.PeriodDate = :period_date
            """
        ),
        {"member_id": member_id, "head_id": head_id, "period_date": period_date},
    ).scalar()
    return float(value or 0)


def _legacy_paid_by_period(rows: list[dict[str, Any]]) -> dict[date, float]:
    paid: dict[date, float] = defaultdict(float)
    for row in rows:
        period_date = row["period_date"]
        if hasattr(period_date, "date"):
            period_date = period_date.date()
        paid[period_date] += float(row["line_amount"] or 0)
    return paid


def _delete_generated_legacy_invoices(db, member_id: int, member_code: str) -> int:
    invoice_ids = [
        int(row[0])
        for row in db.execute(
            text(
                """
                SELECT InvoiceID
                FROM billing.billing_invoices
                WHERE MemberID = :member_id
                  AND (InvoiceNo LIKE :receipt_prefix OR InvoiceNo = :due_invoice OR InvoiceNo = :oldest_invoice)
                """
            ),
            {
                "member_id": member_id,
                "receipt_prefix": f"{member_code}-%",
                "due_invoice": f"DUE-{member_code}"[:50],
                "oldest_invoice": f"OLDEST-{member_code}"[:50],
            },
        ).all()
    ]
    if not invoice_ids:
        return 0
    for invoice_id in invoice_ids:
        db.execute(text("DELETE FROM billing.billing_invoices WHERE InvoiceID = :invoice_id"), {"invoice_id": invoice_id})
    return len(invoice_ids)


def _convert_oldest_first(db, member: Member, member_code: str, head_row: dict[str, Any], rows: list[dict[str, Any]]) -> tuple[int, int]:
    generated_rows = _legacy_generated_monthly_rows(db, member_code)
    total_paid = sum(float(row["line_amount"] or 0) for row in rows)
    if not generated_rows:
        return 0, 0

    invoice_no = f"OLDEST-{member_code}"[:50]
    existing_invoice = db.query(BillingInvoice).filter(BillingInvoice.invoice_no == invoice_no).one_or_none()
    if existing_invoice is not None:
        return 0, 0

    detail_payloads = []
    remaining_paid = total_paid
    for row in generated_rows:
        period_date = row["period_date"]
        if hasattr(period_date, "date"):
            period_date = period_date.date()
        fee = float(row["receivable_amount"] or 0)
        received = min(fee, remaining_paid)
        remaining_paid -= received
        due = max(fee - received, 0)
        detail_payloads.append((period_date, fee, received, due))

    invoice = BillingInvoice(
        invoice_no=invoice_no,
        member_id=member.id,
        invoice_date=date.today(),
        subtotal_amount=sum(item[1] for item in detail_payloads),
        discount_amount=0,
        net_amount=sum(item[1] for item in detail_payloads),
        total_receive_amount=sum(item[2] for item in detail_payloads),
        total_due_amount=sum(item[3] for item in detail_payloads),
        is_cancelled=False,
        cancel_reason=None,
        created_by=None,
    )
    db.add(invoice)
    db.flush()

    created_details = 0
    for period_date, fee, received, due in detail_payloads:
        db.add(
            BillingInvoiceDetail(
                invoice_id=invoice.id,
                member_id=member.id,
                billing_head_id=int(head_row["BillingHeadID"]),
                head_name_snapshot=str(head_row["HeadName"]),
                head_type="Period",
                period_date=period_date,
                period_display=_period_display(period_date),
                fee_amount=fee,
                receive_amount=received,
                due_amount=due,
                discount_amount=0,
                coa_id_snapshot=head_row["COAID"],
                is_income_transferred=received > 0,
                created_by=None,
            )
        )
        created_details += 1
    return 1, created_details


def convert_member(member_code: str, execute: bool, allocation_mode: str = "legacy-periods", replace: bool = False) -> dict[str, int]:
    with SessionLocal() as db:
        member = db.query(Member).filter(Member.member_code == member_code).one_or_none()
        if member is None:
            raise SystemExit(f"Member code not found: {member_code}")

        head_row = db.execute(
            text(
                """
                SELECT TOP 1 h.BillingHeadID, h.HeadName, m.COAID
                FROM billing.billing_heads h
                LEFT JOIN billing.billing_head_coa_mappings m
                    ON m.BillingHeadID = h.BillingHeadID AND m.IsActive = 1
                WHERE h.IsActive = 1
                  AND h.HeadType = 'Period'
                  AND h.HeadName = 'Monthly CHADA'
                ORDER BY h.BillingHeadID DESC
                """
            )
        ).mappings().one_or_none()
        if head_row is None:
            raise SystemExit("Active Monthly CHADA billing head was not found.")

        rows = _legacy_monthly_rows(db, member.id)
        grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[int(row["receipt_id"])].append(row)

        existing = int(
            db.execute(
                text("SELECT COUNT(*) FROM billing.billing_invoices WHERE InvoiceNo LIKE :prefix"),
                {"prefix": f"{member_code}-%"},
            ).scalar()
            or 0
        )
        if not execute:
            generated_rows = _legacy_generated_monthly_rows(db, member_code)
            paid_by_period = _legacy_paid_by_period(rows)
            open_due_rows = 0
            open_due_total = 0.0
            oldest_first_due_rows = 0
            oldest_first_due_total = 0.0
            remaining_paid = sum(float(row["line_amount"] or 0) for row in rows)
            for row in generated_rows:
                period_date = row["period_date"]
                if hasattr(period_date, "date"):
                    period_date = period_date.date()
                remaining = max(float(row["receivable_amount"] or 0) - paid_by_period.get(period_date, 0.0), 0)
                if remaining > 0:
                    open_due_rows += 1
                    open_due_total += remaining
                fee = float(row["receivable_amount"] or 0)
                paid_here = min(fee, remaining_paid)
                remaining_paid -= paid_here
                oldest_due = max(fee - paid_here, 0)
                if oldest_due > 0:
                    oldest_first_due_rows += 1
                    oldest_first_due_total += oldest_due
            return {
                "member_id": member.id,
                "legacy_monthly_rows": len(rows),
                "legacy_receipts": len(grouped),
                "legacy_generated_rows": len(generated_rows),
                "legacy_open_due_rows": open_due_rows,
                "legacy_open_due_total": int(open_due_total) if open_due_total.is_integer() else open_due_total,
                "oldest_first_due_rows": oldest_first_due_rows,
                "oldest_first_due_total": int(oldest_first_due_total) if oldest_first_due_total.is_integer() else oldest_first_due_total,
                "existing_legacy_invoices": existing,
                "created_invoices": 0,
                "created_details": 0,
            }

        deleted_invoices = 0
        if replace:
            deleted_invoices = _delete_generated_legacy_invoices(db, member.id, member_code)

        if allocation_mode == "oldest-first":
            created_invoices, created_details = _convert_oldest_first(db, member, member_code, head_row, rows)
            db.commit()
            return {
                "member_id": member.id,
                "legacy_monthly_rows": len(rows),
                "legacy_receipts": len(grouped),
                "existing_legacy_invoices": existing,
                "deleted_legacy_invoices": deleted_invoices,
                "created_invoices": created_invoices,
                "created_details": created_details,
            }

        created_invoices = 0
        created_details = 0
        for receipt_id, receipt_rows in grouped.items():
            receipt_no = str(receipt_rows[0]["receipt_no"]).strip()
            invoice_no = f"{member_code}-{receipt_no}"[:50]
            existing_invoice = db.query(BillingInvoice).filter(BillingInvoice.invoice_no == invoice_no).one_or_none()
            if existing_invoice is not None:
                continue

            detail_payloads = []
            for row in receipt_rows:
                period_date = row["period_date"]
                if hasattr(period_date, "date"):
                    period_date = period_date.date()
                fee = _period_fee(period_date)
                received = float(row["line_amount"] or 0)
                due = max(fee - received, 0)
                detail_payloads.append((row, period_date, fee, received, due))

            subtotal = sum(item[2] for item in detail_payloads)
            received_total = sum(item[3] for item in detail_payloads)
            due_total = sum(item[4] for item in detail_payloads)

            invoice = BillingInvoice(
                invoice_no=invoice_no,
                member_id=member.id,
                invoice_date=receipt_rows[0]["payment_date"],
                subtotal_amount=subtotal,
                discount_amount=0,
                net_amount=subtotal,
                total_receive_amount=received_total,
                total_due_amount=due_total,
                is_cancelled=False,
                cancel_reason=None,
                created_by=None,
            )
            db.add(invoice)
            db.flush()
            created_invoices += 1

            for row, period_date, fee, received, due in detail_payloads:
                db.add(
                    BillingInvoiceDetail(
                        invoice_id=invoice.id,
                        member_id=member.id,
                        billing_head_id=int(head_row["BillingHeadID"]),
                        head_name_snapshot=str(head_row["HeadName"]),
                        head_type="Period",
                        period_date=period_date,
                        period_display=_period_display(period_date),
                        fee_amount=fee,
                        receive_amount=received,
                        due_amount=due,
                        discount_amount=0,
                        coa_id_snapshot=head_row["COAID"],
                        is_income_transferred=True,
                        created_by=None,
                    )
                )
                created_details += 1

        due_invoice_no = f"DUE-{member_code}"[:50]
        existing_due_invoice = db.query(BillingInvoice).filter(BillingInvoice.invoice_no == due_invoice_no).one_or_none()
        if existing_due_invoice is None:
            paid_by_period = _legacy_paid_by_period(rows)
            due_payloads = []
            for row in _legacy_generated_monthly_rows(db, member_code):
                period_date = row["period_date"]
                if hasattr(period_date, "date"):
                    period_date = period_date.date()
                legacy_remaining = max(float(row["receivable_amount"] or 0) - paid_by_period.get(period_date, 0.0), 0)
                existing_due = _existing_period_due(db, member.id, int(head_row["BillingHeadID"]), period_date)
                adjustment_due = max(legacy_remaining - existing_due, 0)
                if adjustment_due > 0:
                    due_payloads.append((period_date, adjustment_due))

            if due_payloads:
                invoice = BillingInvoice(
                    invoice_no=due_invoice_no,
                    member_id=member.id,
                    invoice_date=date.today(),
                    subtotal_amount=sum(item[1] for item in due_payloads),
                    discount_amount=0,
                    net_amount=sum(item[1] for item in due_payloads),
                    total_receive_amount=0,
                    total_due_amount=sum(item[1] for item in due_payloads),
                    is_cancelled=False,
                    cancel_reason=None,
                    created_by=None,
                )
                db.add(invoice)
                db.flush()
                created_invoices += 1

                for period_date, adjustment_due in due_payloads:
                    db.add(
                        BillingInvoiceDetail(
                            invoice_id=invoice.id,
                            member_id=member.id,
                            billing_head_id=int(head_row["BillingHeadID"]),
                            head_name_snapshot=str(head_row["HeadName"]),
                            head_type="Period",
                            period_date=period_date,
                            period_display=_period_display(period_date),
                            fee_amount=adjustment_due,
                            receive_amount=0,
                            due_amount=adjustment_due,
                            discount_amount=0,
                            coa_id_snapshot=head_row["COAID"],
                            is_income_transferred=False,
                            created_by=None,
                        )
                    )
                    created_details += 1

        db.commit()
        return {
            "member_id": member.id,
            "legacy_monthly_rows": len(rows),
            "legacy_receipts": len(grouped),
            "existing_legacy_invoices": existing,
            "deleted_legacy_invoices": deleted_invoices,
            "created_invoices": created_invoices,
            "created_details": created_details,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert legacy paid monthly billing rows into new invoice details for one member.")
    parser.add_argument("--member-code", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allocation-mode", choices=["legacy-periods", "oldest-first"], default="legacy-periods")
    parser.add_argument("--replace", action="store_true", help="Delete previously generated LEGACY invoices for this member before converting.")
    args = parser.parse_args()

    stats = convert_member(args.member_code, args.execute, allocation_mode=args.allocation_mode, replace=args.replace)
    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print(f"mode={mode} " + " ".join(f"{key}={value}" for key, value in stats.items()))


if __name__ == "__main__":
    main()
